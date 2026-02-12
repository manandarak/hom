from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.inventory import StockUpdate, StockLedgerRead
from src.app.services.stock_service import StockService

router = APIRouter()

@router.post("/adjust")
def adjust_stock(data: StockUpdate, db: Session = Depends(get_db)):
    # This calls the "Brain" (Service) to update Snapshot + Ledger
    return StockService.update_stock(
        db,
        entity_type="Distributor",
        entity_id=1, # Example ID
        product_id=data.product_id,
        qty_change=data.quantity_change,
        ref_doc=data.reference_document,
        trans_type="Adjustment"
    )

