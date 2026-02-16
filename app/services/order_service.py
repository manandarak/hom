from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import date
from src.app.models.sales_primary import PrimaryOrder, PrimaryInvoice
from src.app.models.product import ProductMaster
from src.app.services.stock_service import StockService


class OrderService:
    @staticmethod
    def dispatch_primary_order(db: Session, order_id: int):
        # 1. Fetch the order
        order = db.query(PrimaryOrder).filter(PrimaryOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != "Pending":
            raise HTTPException(status_code=400, detail=f"Cannot dispatch order in {order.status} status")

        total_invoice_amount = 0

        # 2. Process Items: Deduct from Factory, Add to In-Transit, Calculate Totals
        for item in order.items:
            # Fetch Product to calculate invoice
            product = db.query(ProductMaster).filter(ProductMaster.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")

            # Invoice Math: quantity_cases * units_per_case * base_price * (1 + gst_percent/100)
            amount = (item.quantity_cases * product.units_per_case) * float(product.base_price) * (
                        1 + (product.gst_percent / 100))
            total_invoice_amount += amount

            # Deduct from Factory
            StockService.update_stock(
                db=db,
                entity_type="Factory",
                entity_id=order.from_entity_id,
                product_id=item.product_id,
                qty_change=-item.quantity_cases,
                ref_doc=order.order_number,
                trans_type="PRIMARY_DISPATCH_OUT"
            )

            # Add to In-Transit
            StockService.update_stock(
                db=db,
                entity_type="InTransit",
                entity_id=order.id,  # Entity ID is the Order ID here
                product_id=item.product_id,
                qty_change=item.quantity_cases,
                ref_doc=order.order_number,
                trans_type="PRIMARY_DISPATCH_IN"
            )

        # 3. Generate the Orphaned Invoice!
        invoice = PrimaryInvoice(
            primary_order_id=order.id,
            invoice_number=f"INV-{order.order_number}",
            final_amount=total_invoice_amount,
            invoice_date=date.today()
        )
        db.add(invoice)

        # 4. Update status to 'Dispatched'
        order.status = "Dispatched"
        db.commit()

        return {
            "message": "Order dispatched successfully",
            "invoice_number": invoice.invoice_number,
            "invoice_amount": total_invoice_amount
        }

    @staticmethod
    def receive_primary_order(db: Session, order_id: int):
        # 1. Fetch the order
        order = db.query(PrimaryOrder).filter(PrimaryOrder.id == order_id).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status == "Received":
            return {"message": "Order already processed"}

        if order.status != "Dispatched":
            raise HTTPException(status_code=400,
                                detail=f"Cannot receive order. Current status is {order.status}. Must be Dispatched.")

        # 2. Move stock from 'InTransit' to 'SuperStockist'
        for item in order.items:
            # Deduct from In-Transit
            StockService.update_stock(
                db=db,
                entity_type="InTransit",
                entity_id=order.id,
                product_id=item.product_id,
                qty_change=-item.quantity_cases,
                ref_doc=order.order_number,
                trans_type="PRIMARY_RECEIPT_OUT"
            )

            # Add to Super Stockist
            StockService.update_stock(
                db=db,
                entity_type="SuperStockist",
                entity_id=order.to_entity_id,
                product_id=item.product_id,
                qty_change=item.quantity_cases,
                ref_doc=order.order_number,
                trans_type="PRIMARY_RECEIPT_IN"
            )

        # 3. Update status to 'Received'
        order.status = "Received"
        db.commit()
        return {"message": "Order received successfully and stock delivered to Super Stockist."}