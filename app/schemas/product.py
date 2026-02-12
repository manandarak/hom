import decimal
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import Optional


class ProductBase(BaseModel):
    sku_code: str
    name: str
    base_price: Decimal
    # 1. Make MRP optional or give it a default so validation passes
    mrp: Optional[Decimal] = None
    description: Optional[str] = None


class ProductCreate(ProductBase):
    # 2. Add stock_quantity here so the API accepts it
    stock_quantity: int = 0


class ProductRead(ProductBase):
    id: int
    # 3. Add this so the frontend can read the stock back
    stock_quantity: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)