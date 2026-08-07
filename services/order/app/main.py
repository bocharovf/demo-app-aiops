import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.events import get_redis
from app.logging_config import configure_logging
from app.routers import orders

configure_logging(settings.log_level)
logger = logging.getLogger("order.main")

app = FastAPI(title="order-service")
app.include_router(orders.router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    await get_redis().ping()
    return {"status": "ready"}


@app.on_event("startup")
async def on_startup():
    logger.info("order service starting up")
