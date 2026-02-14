from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.orders import PrimaryOrderCreate, PrimaryOrderRead
from src.app.crud.primary_sales import create_primary_order
from src.app.services.order_service import OrderService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.orders import PrimaryOrderCreate, PrimaryOrderRead
from src.app.services.stock_service import StockService

router = APIRouter()

@router.post("/", response_model=PrimaryOrderRead, status_code=status.HTTP_201_CREATED)
def place_primary_order(order_in: PrimaryOrderCreate, db: Session = Depends(get_db)):
    try:
        # 1. Create the Order Record in the DB
        db_order = create_primary_order(db, order_in)

        # 2. Loop through items to decrease Factory Stock
        # This is what makes the 5005 go down!
        for item in order_in.items:
            StockService.update_stock(
                db=db,
                entity_type="Factory",
                entity_id=order_in.from_entity_id,
                product_id=item.product_id,
                qty_change=-item.quantity, # Negative value to deduct stock
                ref_doc=order_in.order_number,
                trans_type="PRIMARY_SALE_OUT"
            )

        db.commit() # Save both order and stock change together
        db.refresh(db_order)
        return db_order

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{order_id}/receive")
def receive_order(order_id: int, db: Session = Depends(get_db)):
    # This triggers the complex inventory movement logic
    return OrderService.receive_primary_order(db, order_id)

@router.post("/secondary-sale", status_code=201)
def secondary_sale_dispatch(order_in: PrimaryOrderCreate, db: Session = Depends(get_db)):
    """
    Moves stock from Super Stockist (to_entity_id in Primary)
    to a Distributor.
    """
    try:
        for item in order_in.items:
            # 1. Deduct Stock from Super Stockist
            StockService.update_stock(
                db=db,
                entity_type="SuperStockist",
                entity_id=order_in.from_entity_id, # The SS sending the goods
                product_id=item.product_id,
                qty_change=-item.quantity, # Negative to deduct
                ref_doc=order_in.order_number,
                trans_type="SECONDARY_SALE_OUT"
            )

            # 2. Add Stock to Distributor
            StockService.update_stock(
                db=db,
                entity_type="Distributor",
                entity_id=order_in.to_entity_id, # The Distributor receiving
                product_id=item.product_id,
                qty_change=item.quantity, # Positive to add
                ref_doc=order_in.order_number,
                trans_type="SECONDARY_SALE_IN"
            )

        db.commit()
        return {"message": "Stock moved from Super Stockist to Distributor successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))