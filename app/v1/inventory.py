from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.schemas.inventory import ProductionLogCreate
from src.app.models.inventory import DailyProductionLog, FactoryInventory, StockLedger

router = APIRouter()


@router.post("/factory/produce", status_code=201)
def log_factory_production(log_in: ProductionLogCreate, db: Session = Depends(get_db)):
    # 1. Log the production event
    production_log = DailyProductionLog(
        product_id=log_in.product_id,
        factory_id=log_in.factory_id,
        quantity=log_in.quantity_produced,
        batch_number=log_in.batch_number,
        date=log_in.production_date
    )
    db.add(production_log)

    # 2. Update the Factory Inventory (Upsert logic)
    factory_stock = db.query(FactoryInventory).filter(
        FactoryInventory.product_id == log_in.product_id,
        FactoryInventory.factory_id == log_in.factory_id
    ).first()

    if factory_stock:
        factory_stock.quantity += log_in.quantity_produced
    else:
        factory_stock = FactoryInventory(
            product_id=log_in.product_id,
            factory_id=log_in.factory_id,
            quantity=log_in.quantity_produced
        )
        db.add(factory_stock)

    # 3. Write to the immutable Stock Ledger
    ledger_entry = StockLedger(
        product_id=log_in.product_id,
        from_entity_type="SYSTEM",  # Originated from manufacturing
        from_entity_id=0,
        to_entity_type="FACTORY",
        to_entity_id=log_in.factory_id,
        transaction_type="PRODUCTION",
        quantity=log_in.quantity_produced
    )
    db.add(ledger_entry)

    # Commit all three actions as a single atomic transaction
    db.commit()

    return {"message": f"Successfully produced {log_in.quantity_produced} units."}

