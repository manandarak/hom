from sqlalchemy.orm import Session
from src.app.models import geography as models

def get_zones(db: Session):
    return db.query(models.Zone).all()

def get_territories_by_area(db: Session, area_id: int):
    return db.query(models.Territory).filter(models.Territory.area_id == area_id).all()