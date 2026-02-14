from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.inventory import ProductionLogCreate
from src.app.models.inventory import DailyProductionLog, FactoryInventory, StockLedger

router = APIRouter()

@router.post("/log", status_code=201)
def create_production_log(log_in: ProductionLogCreate, db: Session = Depends(get_db)):
    try:
        # 1. Log the production event
        new_log = DailyProductionLog(
            product_id=log_in.product_id,
            factory_id=log_in.factory_id,
            quantity_produced=log_in.quantity_produced,
            batch_number=log_in.batch_number,
            production_date=log_in.production_date
        )
        db.add(new_log)

        # 2. Update the Factory Inventory (Upsert logic)
        factory_stock = db.query(FactoryInventory).filter(
            FactoryInventory.product_id == log_in.product_id,
            FactoryInventory.factory_id == log_in.factory_id
        ).first()

        if factory_stock:
            factory_stock.current_stock_qty += log_in.quantity_produced
        else:
            factory_stock = FactoryInventory(
                product_id=log_in.product_id,
                factory_id=log_in.factory_id,
                current_stock_qty=log_in.quantity_produced
            )
            db.add(factory_stock)

        db.flush() # Force ID creation and math before ledger

        # 3. Write to the immutable Stock Ledger
        ledger_entry = StockLedger(
            product_id=log_in.product_id,
            entity_type="FACTORY",
            entity_id=log_in.factory_id,
            transaction_type="PRODUCTION",
            reference_document=f"BATCH-{log_in.batch_number}",
            quantity_change=log_in.quantity_produced,
            closing_balance=factory_stock.current_stock_qty
        )
        db.add(ledger_entry)

        # 4. Atomic Commit!
        db.commit()
        db.refresh(new_log)

        return {
            "message": f"Successfully produced {log_in.quantity_produced} units.",
            "log_id": new_log.id,
            "new_factory_stock_balance": factory_stock.current_stock_qty
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")