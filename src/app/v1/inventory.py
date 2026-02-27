from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from src.app.core.database import get_db
from src.app.core.security import get_current_user
from src.app.models.user import User
from src.app.models.partner import SuperStockist, Distributor, Retailer
from src.app.services.permission_service import PermissionService
from src.app.schemas.inventory import ProductionLogCreate, StockLedgerRead, StockUpdate
from src.app.models.inventory import DailyProductionLog, FactoryInventory, StockLedger, SSInventory, DistributorInventory, RetailerInventory
from src.app.services.stock_service import StockService

router = APIRouter()

@router.get("/factory/{factory_id}")
def get_factory_stock(factory_id: int, db: Session = Depends(get_db)):
    stock = db.query(FactoryInventory).filter(FactoryInventory.factory_id == factory_id).all()
    return [{"product_id": s.product_id, "batch_number": s.batch_number, "current_stock": s.current_stock_qty} for s in stock]

@router.post("/factory/produce", status_code=201)
def log_factory_production(log_in: ProductionLogCreate, db: Session = Depends(get_db)):
    try:

        production_log = DailyProductionLog(
            product_id=log_in.product_id,
            factory_id=log_in.factory_id,
            quantity_produced=log_in.quantity_produced,
            batch_number=log_in.batch_number,
            production_date=log_in.production_date
        )
        db.add(production_log)

        StockService.update_stock(
            db=db,
            entity_type="Factory",
            entity_id=log_in.factory_id,
            product_id=log_in.product_id,
            qty_change=log_in.quantity_produced,
            ref_doc=f"BATCH-{log_in.batch_number}",
            trans_type="PRODUCTION",
            batch_number=log_in.batch_number
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
    return [{"product_id": s.product_id, "batch_number": s.batch_number, "current_stock": s.current_stock_qty} for s in stock]


@router.get("/ledger", response_model=list[StockLedgerRead])
def get_stock_ledger(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch the master audit trail of all inventory movements securely scoped to the user."""
    query = db.query(StockLedger)

    if not current_user.role:
        return []

    role_name = current_user.role.name

    # 1. Admin gets everything
    if role_name == "Admin":
        return query.order_by(StockLedger.created_at.desc()).limit(100).all()

    # 2. Partners strictly see ONLY their own ledger entries (Fail-Closed)
    if role_name == "SuperStockist":
        partner = db.query(SuperStockist).filter(SuperStockist.user_id == current_user.id).first()
        if not partner: return []
        query = query.filter(StockLedger.entity_type == "SuperStockist", StockLedger.entity_id == partner.id)

    elif role_name == "Distributor":
        partner = db.query(Distributor).filter(Distributor.user_id == current_user.id).first()
        if not partner: return []
        query = query.filter(StockLedger.entity_type == "Distributor", StockLedger.entity_id == partner.id)

    elif role_name == "Retailer":
        partner = db.query(Retailer).filter(Retailer.user_id == current_user.id).first()
        if not partner: return []
        query = query.filter(StockLedger.entity_type == "Retailer", StockLedger.entity_id == partner.id)

    # 3. Internal Teams (ZSM, RSM, ASM, SO) scoped by Geography
    else:
        scope = PermissionService.get_geo_scope(current_user)
        if not scope or "id" in scope:
            return []

        # Find all allowed partner IDs in this geography
        allowed_ss = [s[0] for s in db.query(SuperStockist.id).filter_by(**scope).all()] if hasattr(SuperStockist,
                                                                                                    list(scope.keys())[
                                                                                                        0]) else []
        allowed_dist = [d[0] for d in db.query(Distributor.id).filter_by(**scope).all()] if hasattr(Distributor,
                                                                                                    list(scope.keys())[
                                                                                                        0]) else []
        allowed_ret = [r[0] for r in db.query(Retailer.id).filter_by(**scope).all()] if hasattr(Retailer,
                                                                                                list(scope.keys())[
                                                                                                    0]) else []

        # Filter the ledger by combining the allowed entity IDs using SQLAlchemy's or_ and and_
        query = query.filter(
            or_(
                and_(StockLedger.entity_type == "SuperStockist", StockLedger.entity_id.in_(allowed_ss)),
                and_(StockLedger.entity_type == "Distributor", StockLedger.entity_id.in_(allowed_dist)),
                and_(StockLedger.entity_type == "Retailer", StockLedger.entity_id.in_(allowed_ret))
            )
        )

    return query.order_by(StockLedger.created_at.desc()).limit(100).all()


@router.post("/{entity_type}/{entity_id}/adjust", status_code=200)
def adjust_stock(
        entity_type: str,
        entity_id: int,
        update_in: StockUpdate,
        db: Session = Depends(get_db)
):
    """
    Manual adjustment for shrinkage, damage, returns, or audit corrections.
    entity_type must be: Factory, SuperStockist, Distributor, or Retailer
    """
    formatted_entity_type = entity_type.capitalize()
    if formatted_entity_type == "Superstockist":
        formatted_entity_type = "SuperStockist"

    try:
        stock_record = StockService.update_stock(
            db=db,
            entity_type=formatted_entity_type,
            entity_id=entity_id,
            product_id=update_in.product_id,
            qty_change=update_in.quantity_change,
            ref_doc=update_in.reference_document,
            trans_type=update_in.transaction_type
        )
        db.commit()
        return {
            "message": "Stock adjusted successfully",
            "new_balance": stock_record.current_stock_qty,
            "product_id": update_in.product_id
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise e


@router.get("/distributor/{distributor_id}")
def get_distributor_stock(distributor_id: int, db: Session = Depends(get_db)):
    """Fetches all stock and batches sitting with a specific Distributor"""
    stock = db.query(DistributorInventory).filter(DistributorInventory.distributor_id == distributor_id).all()

    return [
        {
            "product_id": s.product_id,
            "batch_number": s.batch_number,
            "current_stock": s.current_stock_qty
        }
        for s in stock
    ]

# --- NEW ENDPOINT TO FIX 404 ERROR ---
@router.get("/retailer/{retailer_id}")
def get_retailer_stock(retailer_id: int, db: Session = Depends(get_db)):
    """Fetches all stock and batches sitting with a specific Retailer"""
    stock = db.query(RetailerInventory).filter(RetailerInventory.retailer_id == retailer_id).all()

    return [
        {
            "product_id": s.product_id,
            "batch_number": s.batch_number,
            "current_stock": s.current_stock_qty
        }
        for s in stock
    ]