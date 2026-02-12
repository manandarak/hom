from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.crud.tertiary_sales import get_tertiary_orders_by_so, update_tertiary_status

router = APIRouter()

@router.get("/so/{so_id}/pending")
def get_pending_requests(so_id: int, db: Session = Depends(get_db)):
    return get_tertiary_orders_by_so(db, so_id)

@router.patch("/{order_id}/approve")
def approve_tertiary_order(order_id: int, db: Session = Depends(get_db)):
    # Changes status to "Approved_by_SO"
    return update_tertiary_status(db, order_id, "Approved_by_SO")