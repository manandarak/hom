from sqlalchemy.orm import Session
from fastapi import HTTPException, status  # <-- NEW IMPORT
from src.app.crud.inventory import get_distributor_stock, create_ledger_entry
from src.app.models.inventory import DistributorInventory, FactoryInventory, SSInventory, RetailerInventory
from src.app.models.inventory import DistributorInventory, FactoryInventory, SSInventory, RetailerInventory, InTransitInventory


class StockService:
    @staticmethod
    def update_stock(db: Session, entity_type: str, entity_id: int, product_id: int, qty_change: int, ref_doc: str, trans_type: str):
        # 1. Fetch record with a pessimistic lock (via _get_stock_record)
        stock_record = StockService._get_stock_record(db, entity_type, entity_id, product_id)

        # 2. --- NEW: NEGATIVE STOCK VALIDATION ---
        if stock_record.current_stock_qty + qty_change < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {entity_type} ID {entity_id}. Available: {stock_record.current_stock_qty}, Attempted to deduct: {abs(qty_change)}"
            )

        # 3. Update the balance safely
        stock_record.current_stock_qty += qty_change

        # 4. Create the 'History of Truth' Entry
        ledger_data = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "product_id": product_id,
            "transaction_type": trans_type,
            "reference_document": ref_doc,
            "quantity_change": qty_change,
            "closing_balance": stock_record.current_stock_qty
        }
        create_ledger_entry(db, ledger_data)
        return stock_record

    @staticmethod
    def _get_stock_record(db: Session, entity_type: str, entity_id: int, product_id: int):
        """Helper to find the correct inventory record based on entity type"""
        model = None
        record = None

        # --- NEW: ADDED .with_for_update() TO ALL QUERIES TO PREVENT RACE CONDITIONS ---
        if entity_type == "Distributor":
            model = DistributorInventory
            record = db.query(model).filter_by(distributor_id=entity_id, product_id=product_id).with_for_update().first()
        elif entity_type == "Factory":
            model = FactoryInventory
            record = db.query(model).filter_by(factory_id=entity_id, product_id=product_id).with_for_update().first()
        elif entity_type == "SuperStockist":
            model = SSInventory
            record = db.query(model).filter_by(ss_id=entity_id, product_id=product_id).with_for_update().first()
        elif entity_type == "Retailer":
            model = RetailerInventory
            record = db.query(model).filter_by(retailer_id=entity_id, product_id=product_id).with_for_update().first()
        elif entity_type == "InTransit":
            model = InTransitInventory
            # For InTransit, the entity_id is actually the order_id
            record = db.query(model).filter_by(order_id=entity_id, product_id=product_id).with_for_update().first()
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # If no record exists, initialize it at 0 (Safe because transaction locks the insert)
        if not record:
            if entity_type == "Distributor":
                record = DistributorInventory(distributor_id=entity_id, product_id=product_id, current_stock_qty=0)
            elif entity_type == "Factory":
                record = FactoryInventory(factory_id=entity_id, product_id=product_id, current_stock_qty=0)
            elif entity_type == "SuperStockist":
                record = SSInventory(ss_id=entity_id, product_id=product_id, current_stock_qty=0)
            elif entity_type == "Retailer":
                record = RetailerInventory(retailer_id=entity_id, product_id=product_id, current_stock_qty=0)
            elif entity_type == "InTransit":
                record = InTransitInventory(order_id=entity_id, product_id=product_id, current_stock_qty=0)

            db.add(record)
            db.flush()

        return record