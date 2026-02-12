from src.app.crud.primary_sales import update_order_status
from sqlalchemy.orm import Session


class OrderService:
    @staticmethod
    def receive_primary_order(db: Session, order_id: int):
        # 1. Logic to verify order exists
        # 2. Logic to move stock from 'From_Entity' to 'To_Entity'
        # 3. Update status to 'Received'
        return update_order_status(db, order_id, "Received")