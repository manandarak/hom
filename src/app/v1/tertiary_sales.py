from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.orders import TertiaryOrderCreate
from src.app.crud.tertiary_sales import (
    get_tertiary_orders_by_so,
    update_tertiary_status,
    get_tertiary_order_by_id
)
from src.app.services.stock_service import StockService
from src.app.core.security import get_current_user
from src.app.services.permission_service import PermissionService
from src.app.crud.tertiary_sales import get_scoped_pending_orders
from src.app.models.user import User
from src.app.schemas.partner import EndConsumerCreate, EndConsumerRead, EndConsumerUpdate
from src.app.crud.tertiary_sales import (
    create_end_consumer, get_end_consumers, update_end_consumer, delete_end_consumer
)
from fastapi import APIRouter, Depends, HTTPException, status
from src.app.models.sales_tertiary import TertiaryOrder, TertiaryOrder
from src.app.schemas.orders import TertiaryOrderCreate

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
    order = get_tertiary_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Tertiary Order not found")

    if order.status == "Approved_by_SO":
        return {"message": "Order already approved"}

    try:
        StockService.update_stock(
            db=db,
            entity_type="Retailer",
            entity_id=order.fulfilled_by_retailer_id,
            product_id=order.product_id,
            qty_change=-order.quantity,
            ref_doc=f"TERT-{order.id}",
            batch_number=order.batch_number,
            trans_type="RETAIL_SALE"
        )

        updated_order = update_tertiary_status(db, order_id, "Approved_by_SO")
        db.commit()

        return updated_order
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pending")
def get_my_pending_requests(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    scope_filter = PermissionService.get_user_data_scope(current_user)

    # 2. Pass the filter to the database query
    return get_scoped_pending_orders(db, scope_filter)


@router.post("/consumers", response_model=EndConsumerRead, status_code=201)
def register_end_consumer(consumer_in: EndConsumerCreate, db: Session = Depends(get_db)):
    return create_end_consumer(db, consumer_in)

@router.get("/consumers", response_model=list[EndConsumerRead])
def list_end_consumers(db: Session = Depends(get_db)):
    return get_end_consumers(db)

@router.patch("/consumers/{consumer_id}", response_model=EndConsumerRead)
def modify_end_consumer(consumer_id: int, consumer_in: EndConsumerUpdate, db: Session = Depends(get_db)):
    updated = update_end_consumer(db, consumer_id, consumer_in)
    if not updated:
        raise HTTPException(status_code=404, detail="End Consumer not found")
    return updated

@router.delete("/consumers/{consumer_id}", status_code=204)
def remove_end_consumer(consumer_id: int, db: Session = Depends(get_db)):
    success = delete_end_consumer(db, consumer_id)
    if not success:
        raise HTTPException(status_code=404, detail="End Consumer not found")
    return None


@router.put("/{order_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_tertiary_order(order_id: int, db: Session = Depends(get_db)):
    """Cancels a tertiary order if it is still pending."""
    order = db.query(TertiaryOrder).filter(TertiaryOrder.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Tertiary Order not found")

    if order.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order. Current status is '{order.status}'."
        )

    order.status = "Cancelled"
    db.commit()
    return {"message": f"Tertiary Order {order.id} has been cancelled successfully."}


@router.put("/{order_id}", status_code=status.HTTP_200_OK)
def update_tertiary_order(order_id: int, update_in: TertiaryOrderCreate, db: Session = Depends(get_db)):
    """Updates the tertiary order before fulfillment."""
    order = db.query(TertiaryOrder).filter(TertiaryOrder.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Tertiary Order not found")

    if order.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update order in '{order.status}' status."
        )


    order.end_consumer_id = update_in.end_consumer_id
    order.fulfilled_by_retailer_id = update_in.fulfilled_by_retailer_id
    order.assigned_so_id = update_in.assigned_so_id
    order.product_id = update_in.product_id
    order.quantity = update_in.quantity
    order.batch_number = update_in.batch_number

    db.commit()
    return {"message": f"Tertiary Order {order.id} updated successfully."}