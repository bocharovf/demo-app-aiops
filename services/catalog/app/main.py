import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.logging_config import configure_logging
from app.middleware import upstream_throttle_middleware
from app.routers import categories, products, stock

configure_logging(settings.log_level)
logger = logging.getLogger("catalog.main")

app = FastAPI(title="catalog-service")
app.middleware("http")(upstream_throttle_middleware)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(stock.router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


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
    logger.info("catalog service starting up")
