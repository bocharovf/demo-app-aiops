import asyncio
import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.config import settings
from app.consumer import run_consumer_loop
from app.database import engine, init_models
from app.logging_config import configure_logging

configure_logging(settings.log_level)
logger = logging.getLogger("notification.main")

app = FastAPI(title="notification-service")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

_stop_event = asyncio.Event()
_consumer_task: asyncio.Task | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.on_event("startup")
async def on_startup():
    global _consumer_task
    logger.info("notification service starting up")
    await init_models()
    _consumer_task = asyncio.create_task(run_consumer_loop(_stop_event))


@app.on_event("shutdown")
async def on_shutdown():
    _stop_event.set()
    if _consumer_task:
        await _consumer_task
