import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Stock
from app.schemas import ReserveRequest, ReserveResponse, StockOut

logger = logging.getLogger("catalog.stock")
router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/{product_id}", response_model=StockOut)
async def get_stock(product_id: int, session: AsyncSession = Depends(get_session)):
    stock = await session.get(Stock, product_id)
    if stock is None:
        raise HTTPException(status_code=404, detail="stock not found")
    return stock


@router.post("/reserve", response_model=ReserveResponse)
async def reserve_stock(payload: ReserveRequest, session: AsyncSession = Depends(get_session)):
    # Atomic conditional update avoids overselling under concurrent orders:
    # the WHERE clause re-checks availability at UPDATE time, not at SELECT time.
    result = await session.execute(
        update(Stock)
        .where(
            Stock.product_id == payload.product_id,
            Stock.quantity - Stock.reserved_quantity >= payload.quantity,
        )
        .values(reserved_quantity=Stock.reserved_quantity + payload.quantity)
        .returning(Stock.quantity, Stock.reserved_quantity)
    )
    row = result.first()
    await session.commit()

    if row is None:
        stock = await session.get(Stock, payload.product_id)
        available = (stock.quantity - stock.reserved_quantity) if stock else 0
        logger.warning(
            "reservation rejected: insufficient stock",
            extra={"product_id": payload.product_id, "order_id": payload.order_id, "available": available},
        )
        return ReserveResponse(ok=False, available=available)

    quantity, reserved_quantity = row
    logger.info(
        "stock reserved",
        extra={"product_id": payload.product_id, "order_id": payload.order_id, "quantity": payload.quantity},
    )
    return ReserveResponse(ok=True, available=quantity - reserved_quantity)


@router.post("/release", response_model=ReserveResponse)
async def release_stock(payload: ReserveRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        update(Stock)
        .where(Stock.product_id == payload.product_id)
        .values(reserved_quantity=Stock.reserved_quantity - payload.quantity)
        .returning(Stock.quantity, Stock.reserved_quantity)
    )
    row = result.first()
    await session.commit()
    if row is None:
        raise HTTPException(status_code=404, detail="stock not found")

    quantity, reserved_quantity = row
    logger.info(
        "stock released",
        extra={"product_id": payload.product_id, "order_id": payload.order_id, "quantity": payload.quantity},
    )
    return ReserveResponse(ok=True, available=quantity - reserved_quantity)
