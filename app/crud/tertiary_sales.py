from sqlalchemy.orm import Session
from src.app.models.sales_tertiary import TertiaryOrder
from src.app.schemas.orders import TertiaryOrderCreate

def create_tertiary_sale(db: Session, sale_in: TertiaryOrderCreate):
    """Creates a new tertiary sale record (Pending status by default)"""
    db_order = TertiaryOrder(
        distributor_id=sale_in.distributor_id,
        retailer_id=sale_in.retailer_id,
        product_id=sale_in.product_id,
        quantity=sale_in.quantity,
        assigned_so_id=sale_in.so_id,
        consumer_name=sale_in.consumer_name,
        status="Pending"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_tertiary_order_by_id(db: Session, order_id: int):
    """Fetches a single order - Required for the Approval logic to work"""
    return db.query(TertiaryOrder).filter(TertiaryOrder.id == order_id).first()

def get_tertiary_orders_by_so(db: Session, so_id: int):
    """Fetches all sales assigned to a specific Sales Officer for review"""
    return db.query(TertiaryOrder).filter(TertiaryOrder.assigned_so_id == so_id).all()

def update_tertiary_status(db: Session, order_id: int, status: str):
    """Updates the status (e.g., to 'Approved_by_SO')"""
    db_order = db.query(TertiaryOrder).filter(TertiaryOrder.id == order_id).first()
    if db_order:
        db_order.status = status
        db.commit()
        db.refresh(db_order)
    return db_order