from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    batch_number: str


class PrimaryOrderCreate(BaseModel):
    order_number: str
    type: str
    from_entity_id: int
    to_entity_id: int
    items: List[OrderItemBase]

class PrimaryOrderRead(BaseModel):
    id: int
    order_number: str
    status: str
    model_config = ConfigDict(from_attributes=True)

class SecondaryOrderCreate(BaseModel):
    retailer_id: int
    distributor_id: int
    items: List[OrderItemBase]

class TertiaryOrderCreate(BaseModel):
    end_consumer_id: int
    fulfilled_by_retailer_id: int
    product_id: int
    quantity: int
    assigned_so_id: int

class DispatchPayload(BaseModel):
    transporter_name: str
    vehicle_number: str
    lr_number: str
    driver_phone: Optional[str] = None
    estimated_arrival_date: date

class OrderItemRead(BaseModel):
    product_id: int
    quantity_cases: int  # or quantity, whatever your model uses
    batch_number: Optional[str] = None

    class Config:
        from_attributes = True # This tells Pydantic to read from SQLAlchemy

# 2. Update the main Order Read schema to include the missing data!
class PrimaryOrderRead(BaseModel):
    id: int
    order_number: str
    status: str
    ss_id: Optional[int] = None           # <--- ADD THIS
    to_entity_id: Optional[int] = None    # <--- OR THIS (depending on your model)
    items: List[OrderItemRead] = []       # <--- ADD THIS (This is the most important part)

    class Config:
        from_attributes = True