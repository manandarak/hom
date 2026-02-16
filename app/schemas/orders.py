from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date
from decimal import Decimal

# --- SHARED ITEM SCHEMAS ---
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int # cases for Primary, units for Secondary

# --- PRIMARY ORDERS (Factory/SS) ---
class PrimaryOrderCreate(BaseModel):
    order_number: str
    type: str # Factory_to_SS, SS_to_DB
    from_entity_id: int
    to_entity_id: int
    items: List[OrderItemBase]

class PrimaryOrderRead(BaseModel):
    id: int
    order_number: str
    status: str
    model_config = ConfigDict(from_attributes=True)

# --- SECONDARY ORDERS (DB to Retailer) ---
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