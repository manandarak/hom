from sqlalchemy.orm import Session
from src.app.models.sales_secondary import SecondaryOrder, SecondaryOrderItems

def create_secondary_order(db: Session, retailer_id: int, distributor_id: int, items_in: list):
    db_order = SecondaryOrder(
        retailer_id=retailer_id,
        distributor_id=distributor_id,
        status="Pending"
    )
    db.add(db_order)
    db.flush()

    for item in items_in:
        db_item = SecondaryOrderItems(
            secondary_order_id=db_order.id,
            product_id=item['product_id'],
            quantity_units=item['quantity']
        )
        db.add(db_item)
    return db_order