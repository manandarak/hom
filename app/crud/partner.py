from sqlalchemy.orm import Session
from src.app.models.partner import SuperStockist, Distributor, Retailer
from src.app.schemas.partner import SuperStockistCreate, DistributorCreate, RetailerCreate

def create_super_stockist(db: Session, ss_in: SuperStockistCreate):
    db_ss = SuperStockist(**ss_in.model_dump())
    db.add(db_ss)
    db.commit()
    db.refresh(db_ss)
    return db_ss

def create_distributor(db: Session, dist_in: DistributorCreate):
    db_dist = Distributor(**dist_in.model_dump())
    db.add(db_dist)
    db.commit()
    db.refresh(db_dist)
    return db_dist

def create_retailer(db: Session, ret_in: RetailerCreate):
    db_ret = Retailer(**ret_in.model_dump())
    db.add(db_ret)
    db.commit()
    db.refresh(db_ret)
    return db_ret