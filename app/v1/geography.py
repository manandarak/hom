from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db

# 1. IMPORT THE SCHEMAS (So Python knows what TerritoryCreate/Read are)
from src.app.schemas.geography import TerritoryCreate, TerritoryRead

# 2. IMPORT THE CRUD FUNCTIONS
from src.app.crud.geography import get_zones, create_territory_in_db

# 3. IMPORT SECURITY (Optional but recommended for creating data)
from src.app.core.security import get_current_user

router = APIRouter()

@router.get("/zones")
def list_zones(db: Session = Depends(get_db)):
    return get_zones(db)

@router.post("/territories", response_model=TerritoryRead)
def create_territory(
    territory_input: TerritoryCreate,
    db: Session = Depends(get_db),
    # Recommended: Lock this down so only admins can create
    current_user = Depends(get_current_user)
):
    return create_territory_in_db(db, territory_input)