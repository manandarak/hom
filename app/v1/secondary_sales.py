from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.orders import SecondaryOrderCreate
from src.app.services.stock_service import StockService
from src.app.crud.secondary_sales import create_secondary_order

router = APIRouter()


# Create a quick schema in schemas/orders.py if you want response_model validation,
# otherwise, this simple query works for now!
@router.get("/")
def get_all_secondary_orders(db: Session = Depends(get_db)):
    from src.app.models.sales_secondary import SecondaryOrder
    return db.query(SecondaryOrder).order_by(SecondaryOrder.id.desc()).all()

@router.post("/", status_code=201)
def record_secondary_sale(sale_in: SecondaryOrderCreate, db: Session = Depends(get_db)):
    try:
        for item in sale_in.items:
            # 1. Deduct stock from the Distributor
            StockService.update_stock(
                db=db,
                entity_type="Distributor",
                entity_id=sale_in.distributor_id,
                product_id=item.product_id,
                qty_change=-item.quantity,  # Deducting stock
                ref_doc=f"INV-SEC-{sale_in.retailer_id}",
                trans_type="SECONDARY_SALE_OUT"
            )

            # 2. Add stock to the Retailer (NEW LOGIC)
            StockService.update_stock(
                db=db,
                entity_type="Retailer",
                entity_id=sale_in.retailer_id,
                product_id=item.product_id,
                qty_change=item.quantity,  # Adding stock
                ref_doc=f"INV-SEC-{sale_in.retailer_id}",
                trans_type="SECONDARY_SALE_IN"
            )
        db.commit()
        return {"message": "Secondary sale recorded and distributor stock updated."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))