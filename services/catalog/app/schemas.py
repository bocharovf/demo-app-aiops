from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CategoryCreate(BaseModel):
    name: str


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    description: str
    price: float


class ProductCreate(BaseModel):
    category_id: int
    name: str
    description: str = ""
    price: float
    initial_quantity: int = 0


class StockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    reserved_quantity: int

    @property
    def available(self) -> int:
        return self.quantity - self.reserved_quantity


class ReserveRequest(BaseModel):
    product_id: int
    quantity: int
    order_id: int


class ReserveResponse(BaseModel):
    ok: bool
    available: int
