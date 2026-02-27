from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.core.security import get_current_user
from src.app.models.user import User
from src.app.models.partner import SuperStockist, Distributor
from src.app.models.sales_primary import PrimaryOrder, PrimaryOrderItems
from src.app.schemas.orders import PrimaryOrderCreate, PrimaryOrderRead, DispatchPayload
from src.app.crud.primary_sales import create_primary_order
from src.app.services.order_service import OrderService
from src.app.services.permission_service import PermissionService

router = APIRouter()

@router.get("/", response_model=list[PrimaryOrderRead])
def get_all_primary_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch primary orders filtered dynamically based on user role and hierarchy."""
    query = db.query(PrimaryOrder)

    if not current_user.role:
        return []

    role_name = current_user.role.name
    scope = PermissionService.get_geo_scope(current_user)

    # 1. Admin gets everything
    if role_name == "Admin":
        return query.order_by(PrimaryOrder.id.desc()).all()

    # 2. Partners strictly see their own entity's orders
    if role_name == "SuperStockist":
        ss = db.query(SuperStockist).filter(SuperStockist.user_id == current_user.id).first()
        if ss:
            query = query.filter((PrimaryOrder.to_entity_id == ss.id) | (PrimaryOrder.from_entity_id == ss.id))
        return query.order_by(PrimaryOrder.id.desc()).all()

    elif role_name == "Distributor":
        distributor = db.query(Distributor).filter(Distributor.user_id == current_user.id).first()
        if distributor:
            query = query.filter(PrimaryOrder.to_entity_id == distributor.id)
        return query.order_by(PrimaryOrder.id.desc()).all()

    elif role_name == "Retailer":
        return [] # Retailers don't deal with primary sales

    # 3. Internal Teams (ZSM, RSM, ASM, SO) scoped by Geography
    if scope and "id" not in scope:
        # Primary Orders go to SuperStockists, so we filter based on the SS geography
        query = query.join(SuperStockist, PrimaryOrder.to_entity_id == SuperStockist.id)
        for key, value in scope.items():
            if hasattr(SuperStockist, key) and value is not None:
                query = query.filter(getattr(SuperStockist, key) == value)

    return query.order_by(PrimaryOrder.id.desc()).all()


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
def dispatch_order(order_id: int, dispatch_data: DispatchPayload, db: Session = Depends(get_db)):
    """Dispatches a primary order with partial fulfillment and logistics tracking."""
    try:
        result = OrderService.dispatch_primary_order(db, order_id, dispatch_data)
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/receive")
def receive_order(order_id: int, db: Session = Depends(get_db)):
    """
    Moves stock from In-Transit Inventory to the Super Stockist.
    Updates status to 'Received'.
    """
    return OrderService.receive_primary_order(db, order_id)


@router.put("/{order_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_primary_order(order_id: int, db: Session = Depends(get_db)):
    """Cancels a primary order if it has not been dispatched yet."""
    order = db.query(PrimaryOrder).filter(PrimaryOrder.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order. Current status is '{order.status}'. Only 'Pending' orders can be cancelled."
        )

    order.status = "Cancelled"
    db.commit()
    return {"message": f"Order {order.order_number} has been cancelled successfully."}


@router.put("/{order_id}", status_code=status.HTTP_200_OK)
def update_primary_order(order_id: int, update_in: PrimaryOrderCreate, db: Session = Depends(get_db)):
    """Updates the items in a primary order before it is dispatched."""
    order = db.query(PrimaryOrder).filter(PrimaryOrder.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update order in '{order.status}' status. Create a new order instead."
        )

    # 1. Delete the old items completely
    db.query(PrimaryOrderItems).filter(PrimaryOrderItems.primary_order_id == order_id).delete()
    db.flush()

    # 2. Insert the fresh, corrected items
    for item in update_in.items:
        new_item = PrimaryOrderItems(
            primary_order_id=order.id,
            product_id=item.product_id,
            batch_number=item.batch_number,
            quantity_cases=item.quantity,
            dispatched_cases=0,
            backordered_cases=0,
            free_cases=0
        )
        db.add(new_item)

    db.commit()
    return {"message": f"Order {order.order_number} updated successfully."}