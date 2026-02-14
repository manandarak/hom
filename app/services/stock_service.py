from sqlalchemy.orm import Session
from src.app.crud.inventory import get_distributor_stock, create_ledger_entry
from src.app.models.inventory import DistributorInventory, FactoryInventory, SSInventory


class StockService:
    @staticmethod
    def update_stock(db: Session, entity_type: str, entity_id: int, product_id: int, qty_change: int, ref_doc: str,
                     trans_type: str):
        # 1. Update Snapshot Logic (Dynamic based on entity_type)
        # In a real app, you'd switch between FactoryInventory/SSInventory/DistributorInventory
        # Let's assume a helper to get the correct stock record
        stock_record = StockService._get_stock_record(db, entity_type, entity_id, product_id)

        # 2. Update the balance
        stock_record.current_stock_qty += qty_change

        # 3. Create the 'History of Truth' Entry
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

        if entity_type == "Distributor":
            model = DistributorInventory
            record = db.query(model).filter_by(distributor_id=entity_id, product_id=product_id).first()
        elif entity_type == "Factory":
            model = FactoryInventory
            record = db.query(model).filter_by(factory_id=entity_id, product_id=product_id).first()
        elif entity_type == "SuperStockist":
            model = SSInventory
            record = db.query(model).filter_by(ss_id=entity_id, product_id=product_id).first()
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")


        if not record:
            if entity_type == "Distributor":
                record = DistributorInventory(distributor_id=entity_id, product_id=product_id, current_stock_qty=0)
            elif entity_type == "Factory":
                record = FactoryInventory(factory_id=entity_id, product_id=product_id, current_stock_qty=0)
            elif entity_type == "SuperStockist":
                record = SSInventory(ss_id=entity_id, product_id=product_id, current_stock_qty=0)

            db.add(record)
            db.flush()

        return record