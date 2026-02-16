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
from src.app.schemas.geography import (
    StateCreate, StateRead, RegionCreate, RegionRead, AreaCreate, AreaRead
)
from src.app.crud.geography import (
    create_state, get_states_by_zone,
    create_region, get_regions_by_state,
    create_area, get_areas_by_region,
    get_territories_by_area
)

from src.app.core.security import get_current_user
from src.app.schemas.geography import TerritoryRead
from sqlalchemy.exc import IntegrityError
from src.app.schemas.geography import ZoneUpdate
from src.app.models.geography import Zone

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

@router.post("/states", response_model=StateRead, status_code=status.HTTP_201_CREATED)
def create_new_state(state: StateCreate, db: Session = Depends(get_db)):
    return create_state(db=db, state=state)

@router.get("/zones/{zone_id}/states", response_model=list[StateRead])
def list_states_in_zone(zone_id: int, db: Session = Depends(get_db)):
    return get_states_by_zone(db, zone_id)

# --- REGION ROUTES ---
@router.post("/regions", response_model=RegionRead, status_code=status.HTTP_201_CREATED)
def create_new_region(region: RegionCreate, db: Session = Depends(get_db)):
    return create_region(db=db, region=region)

@router.get("/states/{state_id}/regions", response_model=list[RegionRead])
def list_regions_in_state(state_id: int, db: Session = Depends(get_db)):
    return get_regions_by_state(db, state_id)

# --- AREA ROUTES ---
@router.post("/areas", response_model=AreaRead, status_code=status.HTTP_201_CREATED)
def create_new_area(area: AreaCreate, db: Session = Depends(get_db)):
    return create_area(db=db, area=area)

@router.get("/regions/{region_id}/areas", response_model=list[AreaRead])
def list_areas_in_region(region_id: int, db: Session = Depends(get_db)):
    return get_areas_by_region(db, region_id)


@router.get("/areas/{area_id}/territories", response_model=list[TerritoryRead])
def list_territories_in_area(area_id: int, db: Session = Depends(get_db)):
    return get_territories_by_area(db, area_id)


@router.patch("/zones/{zone_id}", response_model=ZoneRead)
def update_zone(
        zone_id: int,
        zone_in: ZoneUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    update_data = zone_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_zone, key, value)

    db.commit()
    db.refresh(db_zone)
    return db_zone


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
        zone_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    db_zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    try:
        db.delete(db_zone)
        db.commit()
    except IntegrityError:
        db.rollback()
        # This catches the error if States or ZSMs are still linked to this Zone!
        raise HTTPException(
            status_code=400,
            detail="Cannot delete Zone. It is currently assigned to active States, Super Stockists, or Users."
        )
    return None