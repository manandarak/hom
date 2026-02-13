from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal

class SuperStockistBase(BaseModel):
    zone_id: int
    firm_name: str
    credit_limit: Optional[Decimal] = None
    contact_number: Optional[str] = None
    gstin: Optional[str] = None
    user_id: Optional[int] = None

class SuperStockistCreate(SuperStockistBase):
    pass

class SuperStockistRead(SuperStockistBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- DISTRIBUTOR ---
class DistributorBase(BaseModel):
    state_id: int
    parent_ss_id: Optional[int] = None
    is_direct_party: Optional[bool] = False
    firm_name: Optional[str] = None
    contact_number: Optional[str] = None
    gstin: Optional[str] = None
    user_id: Optional[int] = None

class DistributorCreate(DistributorBase):
    pass

class DistributorRead(DistributorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class RetailerBase(BaseModel):
    territory_id: int
    linked_distributor_id: Optional[int] = None
    shop_name: Optional[str] = None
    shop_type: Optional[str] = None
    contact_number: Optional[str] = None
    gstin: Optional[str] = None
    user_id: Optional[int] = None

class RetailerCreate(RetailerBase):
    pass

class RetailerRead(RetailerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)