from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.models.inventory import DailyProductionLog
from src.app.schemas.inventory import ProductionLogCreate
from fastapi import APIRouter, Depends, HTTPException
router = APIRouter()


@router.post("/log", status_code=201)
def create_production_log(log_in: ProductionLogCreate, db: Session = Depends(get_db)):
    try:
        # Create the database record from the Pydantic schema
        new_log = DailyProductionLog(
            product_id=log_in.product_id,
            factory_id=log_in.factory_id,
            quantity_produced=log_in.quantity_produced,
            batch_number=log_in.batch_number,
            production_date=log_in.production_date
        )

        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        return {
            "message": "Production logged successfully!",
            "log_id": new_log.id,
            "quantity": new_log.quantity_produced
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")