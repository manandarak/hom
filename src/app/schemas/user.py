from pydantic import BaseModel, ConfigDict
from typing import Optional, List

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
    role_id: int
    assigned_zone_id: Optional[int] = None
    assigned_region_id: Optional[int] = None
    assigned_area_id: Optional[int] = None
    assigned_territory_id: Optional[int] = None

class UserRead(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
    role_id: int
    assigned_territory_id: Optional[int]

class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
    assigned_zone_id: Optional[int] = None
    assigned_region_id: Optional[int] = None
    assigned_area_id: Optional[int] = None
    assigned_territory_id: Optional[int] = None


class PermissionRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleRead(RoleBase):
    id: int
    permissions: List[PermissionRead] = []
    model_config = ConfigDict(from_attributes=True)

class RolePermissionUpdate(BaseModel):
    permission_ids: List[int]