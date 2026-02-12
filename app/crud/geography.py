from sqlalchemy.orm import Session
# Import the specific models you use
from src.app.models.geography import Zone, Territory
# Import the schemas you need
from src.app.schemas.geography import TerritoryCreate, ZoneCreate

# --- READ FUNCTIONS ---
def get_zones(db: Session):
    return db.query(Zone).all()

def get_territories_by_area(db: Session, area_id: int):
    return db.query(Territory).filter(Territory.area_id == area_id).all()

# --- CREATE FUNCTIONS ---
def create_zone(db: Session, zone: ZoneCreate):
    db_zone = Zone(name=zone.name)
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

def create_territory_in_db(db: Session, territory: TerritoryCreate):
    db_territory = Territory(
        name=territory.name,
        area_id=territory.area_id
    )
    db.add(db_territory)
    db.commit()
    db.refresh(db_territory)
    return db_territory