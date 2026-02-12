from sqlalchemy.orm import Session
from src.app.crud.inventory import get_distributor_stock, create_ledger_entry


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