import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Category
from app.schemas import CategoryCreate, CategoryOut

logger = logging.getLogger("catalog.categories")
router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Category).order_by(Category.id))
    return result.scalars().all()


@router.post("", response_model=CategoryOut, status_code=201)
async def get_or_create_category(payload: CategoryCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Category).where(Category.name == payload.name))
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    category = Category(name=payload.name)
    session.add(category)
    await session.commit()
    logger.info("category created", extra={"category_id": category.id, "category_name": category.name})
    return category
