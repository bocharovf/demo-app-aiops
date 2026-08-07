import datetime

from sqlalchemy import ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": "catalog"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "catalog"}

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("catalog.categories.id"))
    name: Mapped[str]
    description: Mapped[str] = mapped_column(default="")
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    category: Mapped["Category"] = relationship(back_populates="products")
    stock: Mapped["Stock"] = relationship(back_populates="product", uselist=False)


class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = {"schema": "catalog"}

    product_id: Mapped[int] = mapped_column(ForeignKey("catalog.products.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(default=0)
    reserved_quantity: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    product: Mapped["Product"] = relationship(back_populates="stock")
