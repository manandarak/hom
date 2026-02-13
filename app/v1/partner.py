from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db

from src.app.schemas.partner import (
    SuperStockistCreate, SuperStockistRead,
    DistributorCreate, DistributorRead,
    RetailerCreate, RetailerRead
)
from src.app.crud.partner import (
    create_super_stockist, create_distributor, create_retailer
)

router = APIRouter()

@router.post("/super-stockists", response_model=SuperStockistRead, status_code=status.HTTP_201_CREATED)
def add_super_stockist(ss_in: SuperStockistCreate, db: Session = Depends(get_db)):
    return create_super_stockist(db, ss_in)

@router.post("/distributors", response_model=DistributorRead, status_code=status.HTTP_201_CREATED)
def add_distributor(dist_in: DistributorCreate, db: Session = Depends(get_db)):
    return create_distributor(db, dist_in)

@router.post("/retailers", response_model=RetailerRead, status_code=status.HTTP_201_CREATED)
def add_retailer(ret_in: RetailerCreate, db: Session = Depends(get_db)):
    return create_retailer(db, ret_in)