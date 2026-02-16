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
from src.app.core.security import get_current_user
from src.app.services.permission_service import PermissionService
from src.app.crud.tertiary_sales import get_scoped_pending_orders
from src.app.models.user import User

router = APIRouter()


@router.get("/")
def get_all_tertiary_orders(db: Session = Depends(get_db)):
    from src.app.models.sales_tertiary import TertiaryOrder
    return db.query(TertiaryOrder).order_by(TertiaryOrder.id.desc()).all()


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
            entity_type="Retailer",
            # Use the correct Retailer ID field from your TertiaryOrder model
            entity_id=order.fulfilled_by_retailer_id,  # Or order.retailer_id if that is what your DB uses
            product_id=order.product_id,
            qty_change=-order.quantity,  # Negative to remove from shop
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


@router.get("/pending")
def get_my_pending_requests(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)  # Extracts the user from the JWT Token!
):
    scope_filter = PermissionService.get_user_data_scope(current_user)

    # 2. Pass the filter to the database query
    return get_scoped_pending_orders(db, scope_filter)