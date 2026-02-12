from pydantic import BaseModel, ConfigDict

# --- BASE (Shared fields) ---
class GeoBase(BaseModel):
    name: str

# --- CREATE SCHEMAS (Input - No IDs) ---
# Use these in your POST requests
class ZoneCreate(GeoBase):
    pass  # Just needs 'name'

class RegionCreate(GeoBase):
    zone_id: int

class AreaCreate(GeoBase):
    region_id: int

class TerritoryCreate(GeoBase):
    area_id: int

# --- READ SCHEMAS (Output - Includes IDs) ---
# Use these in your response_model
class ZoneRead(GeoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RegionRead(GeoBase):
    id: int
    zone_id: int
    model_config = ConfigDict(from_attributes=True)

class AreaRead(GeoBase):
    id: int
    region_id: int
    model_config = ConfigDict(from_attributes=True)

class TerritoryRead(GeoBase):
    id: int
    area_id: int
    model_config = ConfigDict(from_attributes=True)