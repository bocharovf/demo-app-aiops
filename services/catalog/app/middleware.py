import asyncio
import random

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings

_EXEMPT_PATHS = {"/health", "/ready", "/metrics"}
_FAILURE_RATE = 0.35


async def upstream_throttle_middleware(request: Request, call_next):
    """Adds variable latency/error handling to business requests based on
    THROTTLE_MODE."""
    if settings.throttle_mode != "adaptive" or request.url.path in _EXEMPT_PATHS:
        return await call_next(request)

    if random.random() < _FAILURE_RATE:
        if random.random() < 0.5:
            await asyncio.sleep(random.uniform(3, 6))
        else:
            return JSONResponse(status_code=503, content={"detail": "upstream unavailable"})

    return await call_next(request)
