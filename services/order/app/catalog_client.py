import asyncio
import logging
import random
import time

import httpx

from app.config import settings

logger = logging.getLogger("order.catalog_client")

# The catalog service is deliberately throttled (THROTTLE_MODE=adaptive injects
# 503/slowness on ~35% of business requests to simulate a flaky upstream).
# `order` must survive that: transient failures are retried with exponential
# backoff + jitter, and a circuit breaker fails fast once catalog is clearly
# down instead of hammering it on every order.
_RETRY_STATUS_CODES = {502, 503, 504}
_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECONDS = 0.25
_MAX_BACKOFF_SECONDS = 2.0


class CatalogUnavailable(Exception):
    pass


class ProductNotFound(Exception):
    pass


class CircuitBreaker:
    """Fails fast after `failure_threshold` consecutive failures, stays open for
    `reset_timeout_seconds`, then allows one probe through (half-open)."""

    def __init__(self, failure_threshold: int = 5, reset_timeout_seconds: float = 10.0):
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout_seconds
        self._failure_count = 0
        self._opened_at = 0.0

    @property
    def is_open(self) -> bool:
        if self._failure_count >= self._failure_threshold:
            if time.monotonic() - self._opened_at >= self._reset_timeout:
                # Half-open: let a single request through to test recovery.
                self._failure_count = self._failure_threshold - 1
                return False
            return True
        return False

    def record_success(self) -> None:
        self._failure_count = 0

    def record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self._failure_threshold:
            self._opened_at = time.monotonic()


_catalog_breaker = CircuitBreaker()


def _backoff_delay(attempt: int) -> float:
    delay = min(_BASE_BACKOFF_SECONDS * (2**attempt), _MAX_BACKOFF_SECONDS)
    return delay + random.uniform(0, 0.1 * delay)


def _status_error(resp: httpx.Response) -> httpx.HTTPStatusError:
    return httpx.HTTPStatusError(
        f"upstream returned {resp.status_code}", request=resp.request, response=resp
    )


async def _backoff(action: str, attempt: int, exc: Exception, extra: dict) -> None:
    delay = _backoff_delay(attempt)
    logger.warning(
        f"catalog {action} transient failure, retrying",
        extra={**extra, "attempt": attempt + 1, "error": str(exc), "retry_in_seconds": round(delay, 3)},
    )
    await asyncio.sleep(delay)


async def _request_with_retry(
    call,
    *,
    action: str,
    extra: dict,
    allowed_statuses: frozenset = frozenset(),
) -> httpx.Response:
    """Run an httpx call with retry/backoff and a circuit breaker.

    Retries transport errors and 5xx responses. Returns the response for 2xx
    (and any explicitly `allowed_statuses`). Raises `CatalogUnavailable` when
    the breaker is open or retries are exhausted.
    """
    if _catalog_breaker.is_open:
        logger.error("catalog circuit breaker open, skipping request", extra=extra)
        raise CatalogUnavailable("catalog circuit breaker open")

    last_exc: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            resp = await call()
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt < _MAX_ATTEMPTS - 1:
                await _backoff(action, attempt, exc, extra)
                continue
            break

        if resp.status_code in _RETRY_STATUS_CODES:
            last_exc = _status_error(resp)
            if attempt < _MAX_ATTEMPTS - 1:
                await _backoff(action, attempt, last_exc, extra)
                continue
            break

        if resp.status_code in allowed_statuses or 200 <= resp.status_code < 300:
            _catalog_breaker.record_success()
            return resp

        last_exc = _status_error(resp)
        break

    _catalog_breaker.record_failure()
    logger.error(f"catalog {action} failed", extra={**extra, "error": str(last_exc)})
    raise CatalogUnavailable(str(last_exc)) from last_exc


async def get_product(client: httpx.AsyncClient, product_id: int) -> dict:
    resp = await _request_with_retry(
        lambda: client.get(f"{settings.catalog_url}/products/{product_id}", timeout=5),
        action="get_product",
        extra={"product_id": product_id},
        allowed_statuses=frozenset({404}),
    )
    if resp.status_code == 404:
        raise ProductNotFound(f"product {product_id} not found")
    return resp.json()


async def reserve_stock(client: httpx.AsyncClient, product_id: int, quantity: int, order_id: int) -> bool:
    if settings.experiment_flag == "batch_mode":
        await asyncio.sleep(8)

    # Retrying a 5xx here is safe: the throttle middleware returns 503 *before*
    # the reserve endpoint runs, so no stock was actually reserved.
    resp = await _request_with_retry(
        lambda: client.post(
            f"{settings.catalog_url}/stock/reserve",
            json={"product_id": product_id, "quantity": quantity, "order_id": order_id},
            timeout=5,
        ),
        action="reserve_stock",
        extra={"product_id": product_id, "order_id": order_id},
    )
    return resp.json()["ok"]


async def release_stock(client: httpx.AsyncClient, product_id: int, quantity: int, order_id: int) -> None:
    # Best-effort: a failed release must never mask the error that triggered it,
    # so CatalogUnavailable is swallowed here after logging.
    try:
        await _request_with_retry(
            lambda: client.post(
                f"{settings.catalog_url}/stock/release",
                json={"product_id": product_id, "quantity": quantity, "order_id": order_id},
                timeout=5,
            ),
            action="release_stock",
            extra={"product_id": product_id, "order_id": order_id},
        )
    except CatalogUnavailable as exc:
        logger.error("catalog release failed", extra={"product_id": product_id, "error": str(exc)})
