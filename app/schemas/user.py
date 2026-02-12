from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    username: str
    is_active: bool = True
    role_id: int
    assigned_zone_id: Optional[int] = None
    assigned_region_id: Optional[int] = None
    assigned_area_id: Optional[int] = None
    assigned_territory_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)