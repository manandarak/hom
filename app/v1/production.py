from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.models.production import DailyProductionLog

router = APIRouter()

@router.post("/log-production")
def log_daily_production(factory_id: int, product_id: int, qty: int, batch: str, db: Session = Depends(get_db)):
    new_log = DailyProductionLog(
        factory_id=factory_id,
        product_id=product_id,
        quantity_produced=qty,
        batch_number=batch,
        qc_status="Passed"
    )
    db.add(new_log)
    # Note: In a real service, this would also call StockService to increase Factory stock
    db.commit()
    return {"message": "Production logged successfully"}