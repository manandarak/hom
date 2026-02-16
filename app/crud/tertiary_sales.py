from sqlalchemy.orm import Session
from src.app.models.sales_tertiary import TertiaryOrder
from src.app.schemas.orders import TertiaryOrderCreate
from datetime import date
from src.app.models.user import User
from src.app.models.sales_tertiary import EndConsumer
from src.app.schemas.partner import EndConsumerCreate, EndConsumerUpdate


def create_tertiary_sale(db: Session, sale_in: TertiaryOrderCreate):
    """Creates a new tertiary sale record (Pending status by default)"""
    db_order = TertiaryOrder(
        end_consumer_id=sale_in.end_consumer_id,
        fulfilled_by_retailer_id=sale_in.fulfilled_by_retailer_id,
        product_id=sale_in.product_id,
        quantity=sale_in.quantity,
        assigned_so_id=sale_in.assigned_so_id,
        request_date=date.today(),
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


def get_scoped_pending_orders(db: Session, scope_filter: dict):
    query = db.query(TertiaryOrder).filter(TertiaryOrder.status == "Pending")

    if not scope_filter:
        return query.all()

    return query.join(
        User, TertiaryOrder.assigned_so_id == User.id
    ).filter_by(**scope_filter).all()


def create_end_consumer(db: Session, consumer_in: EndConsumerCreate):
    db_consumer = EndConsumer(**consumer_in.model_dump())
    db.add(db_consumer)
    db.commit()
    db.refresh(db_consumer)
    return db_consumer

def get_end_consumers(db: Session):
    return db.query(EndConsumer).all()

def update_end_consumer(db: Session, consumer_id: int, consumer_in: EndConsumerUpdate):
    db_consumer = db.query(EndConsumer).filter(EndConsumer.id == consumer_id).first()
    if db_consumer:
        update_data = consumer_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_consumer, key, value)
        db.commit()
        db.refresh(db_consumer)
    return db_consumer

def delete_end_consumer(db: Session, consumer_id: int):
    db_consumer = db.query(EndConsumer).filter(EndConsumer.id == consumer_id).first()
    if db_consumer:
        db.delete(db_consumer)
        db.commit()
        return True
    return False