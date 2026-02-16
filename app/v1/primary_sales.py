from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db

from src.app.models.sales_primary import PrimaryOrder
from src.app.schemas.orders import PrimaryOrderCreate, PrimaryOrderRead
from src.app.crud.primary_sales import create_primary_order
from src.app.services.order_service import OrderService

router = APIRouter()

@router.get("/", response_model=list[PrimaryOrderRead])
def get_all_primary_orders(db: Session = Depends(get_db)):
    """Fetch all primary orders"""
    return db.query(PrimaryOrder).order_by(PrimaryOrder.id.desc()).all()


@router.post("/", response_model=PrimaryOrderRead, status_code=status.HTTP_201_CREATED)
def place_primary_order(order_in: PrimaryOrderCreate, db: Session = Depends(get_db)):
    """
    Creates a Primary Order (Factory to Super Stockist).
    Status defaults to 'Pending'. No stock is deducted yet.
    """
    try:
        # 1. Create the Order Record in the DB
        db_order = create_primary_order(db, order_in)

        db.commit()
        db.refresh(db_order)
        return db_order

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/dispatch")
def dispatch_order(order_id: int, db: Session = Depends(get_db)):
    """
    Deducts stock from Factory, generates Primary Invoice,
    and moves stock to In-Transit Inventory.
    Updates status to 'Dispatched'.
    """
    return OrderService.dispatch_primary_order(db, order_id)


@router.post("/{order_id}/receive")
def receive_order(order_id: int, db: Session = Depends(get_db)):
    """
    Moves stock from In-Transit Inventory to the Super Stockist.
    Updates status to 'Received'.
    """
    return OrderService.receive_primary_order(db, order_id)