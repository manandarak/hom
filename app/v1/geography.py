from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.models.user import User
from src.app.schemas.geography import (
    TerritoryCreate,
    TerritoryRead,
    ZoneCreate,
    ZoneRead
)

from src.app.crud.geography import (
    get_zones,
    create_zone,
    create_territory_in_db
)


from src.app.core.security import get_current_user

router = APIRouter()


@router.get("/zones", response_model=list[ZoneRead])
def list_zones(db: Session = Depends(get_db)):
    return get_zones(db)

@router.post("/zones", response_model=ZoneRead, status_code=status.HTTP_201_CREATED)
def create_new_zone(
    zone: ZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return create_zone(db=db, zone=zone)

@router.post("/territories", response_model=TerritoryRead, status_code=status.HTTP_201_CREATED)
def create_territory(
    territory_input: TerritoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_territory_in_db(db, territory_input)