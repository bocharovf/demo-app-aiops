import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Category, Product, Stock
from app.schemas import ProductCreate, ProductOut

logger = logging.getLogger("catalog.products")
router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Product).order_by(Product.id))
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)):
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    return product


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
    )
    session.add(product)
    await session.flush()

    session.add(Stock(product_id=product.id, quantity=payload.initial_quantity, reserved_quantity=0))
    await session.commit()
    logger.info("product created", extra={"product_id": product.id})
    return product
