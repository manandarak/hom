from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.orders import SecondaryOrderCreate
from src.app.services.stock_service import StockService
from src.app.crud.secondary_sales import create_secondary_order

router = APIRouter()

@router.post("/", status_code=201)
def record_secondary_sale(sale_in: SecondaryOrderCreate, db: Session = Depends(get_db)):
    try:
        for item in sale_in.items:
            # Deduct stock from the Distributor
            StockService.update_stock(
                db=db,
                entity_type="Distributor",
                entity_id=sale_in.distributor_id,
                product_id=item.product_id,
                qty_change=-item.quantity, # Deducting stock
                ref_doc=f"INV-SEC-{sale_in.retailer_id}",
                trans_type="SECONDARY_SALE"
            )
        db.commit()
        return {"message": "Secondary sale recorded and distributor stock updated."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))