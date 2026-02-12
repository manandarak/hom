from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db

# 1. IMPORT MODELS (Fixes 'User' not defined error)
from src.app.models.user import User

# 2. IMPORT SCHEMAS
from src.app.schemas.geography import (
    TerritoryCreate,
    TerritoryRead,
    ZoneCreate,
    ZoneRead
)

# 3. IMPORT CRUD FUNCTIONS (Fixes 'create_zone' not defined error)
from src.app.crud.geography import (
    get_zones,
    create_zone,           # <--- Added this
    create_territory_in_db
)

# 4. IMPORT SECURITY
from src.app.core.security import get_current_user

router = APIRouter()

# --- ZONES ---
@router.get("/zones", response_model=list[ZoneRead])
def list_zones(db: Session = Depends(get_db)):
    return get_zones(db)

@router.post("/zones", response_model=ZoneRead, status_code=status.HTTP_201_CREATED)
def create_new_zone(
    zone: ZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Now works because User is imported
):
    """Create a new zone (Admin only)"""
    return create_zone(db=db, zone=zone) # Now works because create_zone is imported

# --- TERRITORIES ---
@router.post("/territories", response_model=TerritoryRead, status_code=status.HTTP_201_CREATED)
def create_territory(
    territory_input: TerritoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new territory"""
    return create_territory_in_db(db, territory_input)