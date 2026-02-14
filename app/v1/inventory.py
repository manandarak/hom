from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.inventory import ProductionLogCreate
from src.app.models.inventory import DailyProductionLog, FactoryInventory, StockLedger, SSInventory, DistributorInventory
from src.app.services.stock_service import StockService

router = APIRouter()

@router.get("/factory/{factory_id}")
def get_factory_stock(factory_id: int, db: Session = Depends(get_db)):
    # Corrected GET API for your dashboard to see current stock levels
    from src.app.models.inventory import FactoryInventory
    stock = db.query(FactoryInventory).filter(FactoryInventory.factory_id == factory_id).all()
    return [{"product_id": s.product_id, "current_stock": s.current_stock_qty} for s in stock]

@router.post("/factory/produce", status_code=201)
def log_factory_production(log_in: ProductionLogCreate, db: Session = Depends(get_db)):
    try:
        # 1. Log the production event in the transaction log
        production_log = DailyProductionLog(
            product_id=log_in.product_id,
            factory_id=log_in.factory_id,
            quantity_produced=log_in.quantity_produced,
            batch_number=log_in.batch_number,
            production_date=log_in.production_date
        )
        db.add(production_log)

        # 2. Use StockService to handle the complex inventory update and ledger entry
        # This ensures current_stock_qty and stock_ledger stay perfectly synced
        StockService.update_stock(
            db=db,
            entity_type="Factory",
            entity_id=log_in.factory_id,
            product_id=log_in.product_id,
            qty_change=log_in.quantity_produced,
            ref_doc=f"BATCH-{log_in.batch_number}",
            trans_type="PRODUCTION"
        )

        db.commit()
        return {"message": f"Successfully produced {log_in.quantity_produced} units and updated inventory."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ss/{ss_id}")
def get_ss_stock(ss_id: int, db: Session = Depends(get_db)):
    """Fetches all stock sitting with a specific Super Stockist"""
    stock = db.query(SSInventory).filter(SSInventory.ss_id == ss_id).all()
    return [{"product_id": s.product_id, "current_stock": s.current_stock_qty} for s in stock]