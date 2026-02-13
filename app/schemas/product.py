import decimal
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import Optional


class ProductBase(BaseModel):
    sku_code: str
    name: str
    base_price: Decimal
    mrp: Optional[Decimal] = None
    description: Optional[str] = None


class ProductCreate(ProductBase):
    stock_quantity: int = 0


class ProductRead(ProductBase):
    id: int
    stock_quantity: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)