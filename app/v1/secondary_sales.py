from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.orders import SecondaryOrderCreate
from src.app.crud.secondary_sales import create_secondary_order

router = APIRouter()

@router.post("/")
def place_secondary_order(order_in: SecondaryOrderCreate, db: Session = Depends(get_db)):
    # Converting schema list to dict list for the CRUD function
    items = [{"product_id": i.product_id, "quantity": i.quantity} for i in order_in.items]
    return create_secondary_order(
        db,
        retailer_id=order_in.retailer_id,
        distributor_id=order_in.distributor_id,
        items_in=items
    )