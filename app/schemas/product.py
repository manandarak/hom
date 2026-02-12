import decimal

from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional

class ProductBase(BaseModel):
    sku_code : str
    name : str
    mrp : Decimal
    base_price : Decimal

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True) # Allows reading from SQLAlchemy