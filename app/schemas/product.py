from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class ProductBase(BaseModel):
    sku_code: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    mrp: Decimal
    base_price: Decimal
    gst_percent: int = 18
    units_per_case: int = 1
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True  # Use orm_mode = True if using Pydantic v1