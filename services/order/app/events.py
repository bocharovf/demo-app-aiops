import json
import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger("order.events")

STREAM_NAME = "order.events"

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def publish_order_event(event_type: str, order_id: int, payload: dict) -> None:
    client = get_redis()
    body = {"type": event_type, "order_id": str(order_id), "payload": json.dumps(payload, default=str)}
    try:
        await client.xadd(STREAM_NAME, body)
        logger.info("order event published", extra={"event_type": event_type, "order_id": order_id})
    except redis.RedisError as exc:
        logger.error("failed to publish order event", extra={"order_id": order_id, "error": str(exc)})
