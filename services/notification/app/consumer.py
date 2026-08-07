import asyncio
import json
import logging

import redis.asyncio as redis

from app.config import settings
from app.database import SessionLocal
from app.models import Notification

logger = logging.getLogger("notification.consumer")

STREAM_NAME = "order.events"
GROUP_NAME = "notification-workers"
CONSUMER_NAME = "notification-1"

_event_history: list[dict] = []


async def _ensure_group(client: redis.Redis) -> None:
    try:
        await client.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def _handle_message(fields: dict) -> None:
    order_id = int(fields.get("order_id", 0))
    event_type = fields.get("type", "unknown")
    payload = json.loads(fields.get("payload", "{}"))

    async with SessionLocal() as session:
        session.add(Notification(order_id=order_id, type=event_type, status="sent", payload=payload))
        await session.commit()

    if settings.cache_mode == "extended":
        _event_history.append({"order_id": order_id, "type": event_type, "payload": payload})

    logger.info("notification sent", extra={"order_id": order_id, "event_type": event_type})


async def run_consumer_loop(stop_event: asyncio.Event) -> None:
    client = redis.from_url(settings.redis_url, decode_responses=True)
    await _ensure_group(client)
    logger.info("notification consumer started")

    while not stop_event.is_set():
        try:
            response = await client.xreadgroup(
                GROUP_NAME, CONSUMER_NAME, {STREAM_NAME: ">"}, count=10, block=5000
            )
        except redis.RedisError as exc:
            logger.error("redis read failed", extra={"error": str(exc)})
            await asyncio.sleep(2)
            continue

        if not response:
            continue

        for _, messages in response:
            for message_id, fields in messages:
                try:
                    await _handle_message(fields)
                    await client.xack(STREAM_NAME, GROUP_NAME, message_id)
                except Exception:
                    logger.exception("failed to process message", extra={"message_id": message_id})

    await client.close()
