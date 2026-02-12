from sqlalchemy.orm import Session
from src.app.models.sales_tertiary import TertiaryOrder

def get_tertiary_orders_by_so(db: Session, so_id: int):
    return db.query(TertiaryOrder).filter(TertiaryOrder.assigned_so_id == so_id).all()

def update_tertiary_status(db: Session, order_id: int, status: str):
    db_order = db.query(TertiaryOrder).filter(TertiaryOrder.id == order_id).first()
    if db_order:
        db_order.status = status
        db.commit()
    return db_order