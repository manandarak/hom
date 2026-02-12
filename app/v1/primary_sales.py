from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.orders import PrimaryOrderCreate, PrimaryOrderRead
from src.app.crud.primary_sales import create_primary_order
from src.app.services.order_service import OrderService

router = APIRouter()

@router.post("/", response_model=PrimaryOrderRead, status_code=status.HTTP_201_CREATED)
def place_primary_order(order_in: PrimaryOrderCreate, db: Session = Depends(get_db)):
    return create_primary_order(db, order_in)

@router.post("/{order_id}/receive")
def receive_order(order_id: int, db: Session = Depends(get_db)):
    # This triggers the complex inventory movement logic
    return OrderService.receive_primary_order(db, order_id)