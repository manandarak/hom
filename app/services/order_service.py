from sqlalchemy.orm import Session
from src.app.crud.primary_sales import update_order_status
from src.app.models.sales_primary import PrimaryOrder  # Import the model
from src.app.services.stock_service import StockService  # Import StockService
from fastapi import HTTPException


class OrderService:
    @staticmethod
    def receive_primary_order(db: Session, order_id: int):
        # 1. Fetch the order with its items
        order = db.query(PrimaryOrder).filter(PrimaryOrder.id == order_id).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status == "Received":
            return {"message": "Order already processed"}

        # 2. Move stock to 'To_Entity' (Super Stockist)
        # Use quantity_cases to match your model definition
        for item in order.items:
            StockService.update_stock(
                db=db,
                entity_type="SuperStockist",
                entity_id=order.to_entity_id,
                product_id=item.product_id,
                qty_change=item.quantity_cases,  # Fixed attribute name
                ref_doc=order.order_number,
                trans_type="PRIMARY_RECEIPT"
            )

        # 3. Update status to 'Received'
        return update_order_status(db, order_id, "Received")