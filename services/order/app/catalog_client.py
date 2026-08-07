import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger("order.catalog_client")


class CatalogUnavailable(Exception):
    pass


class ProductNotFound(Exception):
    pass


async def get_product(client: httpx.AsyncClient, product_id: int) -> dict:
    try:
        resp = await client.get(f"{settings.catalog_url}/products/{product_id}", timeout=5)
    except httpx.HTTPError as exc:
        logger.error("catalog request failed", extra={"product_id": product_id, "error": str(exc)})
        raise CatalogUnavailable(str(exc)) from exc

    if resp.status_code == 404:
        raise ProductNotFound(f"product {product_id} not found")
    resp.raise_for_status()
    return resp.json()


async def reserve_stock(client: httpx.AsyncClient, product_id: int, quantity: int, order_id: int) -> bool:
    if settings.experiment_flag == "batch_mode":
        await asyncio.sleep(8)

    try:
        resp = await client.post(
            f"{settings.catalog_url}/stock/reserve",
            json={"product_id": product_id, "quantity": quantity, "order_id": order_id},
            timeout=5,
        )
    except httpx.HTTPError as exc:
        logger.error("catalog reserve failed", extra={"product_id": product_id, "error": str(exc)})
        raise CatalogUnavailable(str(exc)) from exc

    resp.raise_for_status()
    return resp.json()["ok"]


async def release_stock(client: httpx.AsyncClient, product_id: int, quantity: int, order_id: int) -> None:
    try:
        resp = await client.post(
            f"{settings.catalog_url}/stock/release",
            json={"product_id": product_id, "quantity": quantity, "order_id": order_id},
            timeout=5,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("catalog release failed", extra={"product_id": product_id, "error": str(exc)})
