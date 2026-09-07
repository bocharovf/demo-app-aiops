import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import Category, Product, Stock
from app.schemas import ProductCreate, ProductOut

logger = logging.getLogger("catalog.products")
router = APIRouter(prefix="/products", tags=["products"])


def _to_product_out(product: Product) -> ProductOut:
    available = product.stock.quantity - product.stock.reserved_quantity if product.stock else 0
    return ProductOut(
        id=product.id,
        category_id=product.category_id,
        name=product.name,
        description=product.description,
        price=float(product.price),
        image_url=product.image_url,
        available=available,
    )


@router.get("", response_model=list[ProductOut])
async def list_products(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Product).options(selectinload(Product.stock)).order_by(Product.id)
    )
    return [_to_product_out(p) for p in result.scalars().all()]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Product).options(selectinload(Product.stock)).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    return _to_product_out(product)


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(payload: ProductCreate, session: AsyncSession = Depends(get_session)):
    category = await session.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(status_code=400, detail="unknown category_id")

    product = Product(
        category_id=payload.category_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        image_url=payload.image_url,
    )
    session.add(product)
    await session.flush()

    stock = Stock(product_id=product.id, quantity=payload.initial_quantity, reserved_quantity=0)
    session.add(stock)
    await session.commit()
    logger.info("product created", extra={"product_id": product.id})

    product.stock = stock
    return _to_product_out(product)
