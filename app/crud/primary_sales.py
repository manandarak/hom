from sqlalchemy.orm import Session
from src.app.models.sales_primary import PrimaryOrder, PrimaryOrderItems
from src.app.schemas.orders import PrimaryOrderCreate


def create_primary_order(db: Session, obj_in: PrimaryOrderCreate):
    # 1. Create Order Header
    db_order = PrimaryOrder(
        order_number=obj_in.order_number,
        type=obj_in.type,
        from_entity_id=obj_in.from_entity_id,
        to_entity_id=obj_in.to_entity_id,
        status="Pending"
    )
    db.add(db_order)
    db.flush()

    # 2. Create Order Items
    for item in obj_in.items:
        db_item = PrimaryOrderItems(
            primary_order_id=db_order.id,
            product_id=item.product_id,
            quantity_cases=item.quantity  # Mapping 'quantity' from schema to 'quantity_cases' in DB
        )
        db.add(db_item)

    return db_order


def update_order_status(db: Session, order_id: int, status: str):
    db_order = db.query(PrimaryOrder).filter(PrimaryOrder.id == order_id).first()
    if db_order:
        db_order.status = status
    return db_order