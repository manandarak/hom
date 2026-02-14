from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
# Ensure these imports exist in your project
from src.app.schemas.orders import TertiaryOrderCreate
from src.app.crud.tertiary_sales import (
    get_tertiary_orders_by_so,
    update_tertiary_status,
    get_tertiary_order_by_id  # You'll need this to find the distributor info
)
from src.app.services.stock_service import StockService

router = APIRouter()


@router.post("/", status_code=201)
def record_tertiary_sale(sale_in: TertiaryOrderCreate, db: Session = Depends(get_db)):
    """
    Consumer or Retailer logs a sale.
    This is just a 'request' until approved by the Sales Officer (SO).
    """
    from src.app.crud.tertiary_sales import create_tertiary_sale
    new_sale = create_tertiary_sale(db, sale_in)
    return {"message": "Tertiary sale logged successfully", "order_id": new_sale.id}


@router.get("/so/{so_id}/pending")
def get_pending_requests(so_id: int, db: Session = Depends(get_db)):
    """Fetch pending sales for a specific Sales Officer to review."""
    return get_tertiary_orders_by_so(db, so_id)


@router.patch("/{order_id}/approve")
def approve_tertiary_order(order_id: int, db: Session = Depends(get_db)):
    """
    Approves the sale and DEDUCTS stock from the Distributor.
    """
    # 1. Get the order details
    order = get_tertiary_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Tertiary Order not found")

    if order.status == "Approved_by_SO":
        return {"message": "Order already approved"}

    try:
        # 2. Deduct Stock from Distributor
        # This is the crucial link in the supply chain!
        StockService.update_stock(
            db=db,
            entity_type="Distributor",
            entity_id=order.distributor_id,
            product_id=order.product_id,
            qty_change=-order.quantity,  # Negative to remove from warehouse
            ref_doc=f"TERT-{order.id}",
            trans_type="RETAIL_SALE"
        )

        # 3. Update the status in the DB
        updated_order = update_tertiary_status(db, order_id, "Approved_by_SO")
        db.commit()

        return updated_order
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))