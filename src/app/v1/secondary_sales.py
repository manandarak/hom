from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.core.security import get_current_user
from src.app.models.user import User
from src.app.services.permission_service import PermissionService
from src.app.models.sales_secondary import SecondaryOrder, SecondaryOrderItems
from src.app.models.partner import Retailer, Distributor
from src.app.models.product import ProductMaster
from src.app.schemas.orders import SecondaryOrderCreate
from src.app.services.stock_service import StockService
from src.app.services.finance_service import FinanceService
from src.app.services.tax_service import TaxService
from src.app.schemas.orders import SecondaryDispatchCreate
from src.app.schemas.orders import SecondaryOrderCreate, DispatchPayload
from src.app.models.geography import Territory, Area, Region, State

router = APIRouter()


@router.post("/", status_code=201)
def record_secondary_sale(sale_in: SecondaryOrderCreate, db: Session = Depends(get_db)):
    """Stage 1: Initialize order as PENDING."""
    try:
        retailer = db.query(Retailer).filter(Retailer.id == sale_in.retailer_id, Retailer.is_active == True).first()
        if not retailer:
            raise HTTPException(status_code=404, detail="Retailer not found.")

        distributor = db.query(Distributor).filter(Distributor.id == sale_in.distributor_id, Distributor.is_active == True).first()
        if not distributor:
            raise HTTPException(status_code=404, detail="Distributor not found.")

        # ... (Keep your existing GST mismatch and calculation logic here) ...
        total_invoice_amount = Decimal("0.00")
        for item in sale_in.items:
            product = db.query(ProductMaster).filter(ProductMaster.id == item.product_id).first()
            base_item_amount = Decimal(str(item.quantity)) * Decimal(str(product.base_price))
            tax_details = TaxService.calculate_gst(base_item_amount, Decimal(str(product.gst_percent)),
                                                   distributor.state_id, retailer_state_id)
            total_invoice_amount += tax_details["final_amount"]

        # --- NEW: WALK UP THE GEOGRAPHIC CHAIN ---
        territory_id = retailer.territory_id
        area_id = None
        region_id = None
        state_id = distributor.state_id
        zone_id = None

        if territory_id:
            territory = db.query(Territory).filter(Territory.id == territory_id).first()
            if territory:
                area_id = territory.area_id
                area = db.query(Area).filter(Area.id == area_id).first()
                if area:
                    region_id = area.region_id
                    region = db.query(Region).filter(Region.id == region_id).first()
                    if region:
                        # State is already known from Distributor, but we can verify Zone
                        state = db.query(State).filter(State.id == state_id).first()
                        if state:
                            zone_id = state.zone_id

        # --- END NEW ---

        # Now include the stamps when creating the order!
        db_order = SecondaryOrder(
            distributor_id=sale_in.distributor_id,
            retailer_id=sale_in.retailer_id,
            total_amount=total_invoice_amount,
            status="PENDING",
            order_date=datetime.now().date(),
            # THE FAT STAMPS:
            zone_id=zone_id,
            state_id=state_id,
            region_id=region_id,
            area_id=area_id,
            territory_id=territory_id
        )
        db.add(db_order)
        db.flush()

        for item in sale_in.items:
            db.add(SecondaryOrderItems(
                secondary_order_id=db_order.id,
                product_id=item.product_id,
                batch_number=item.batch_number,
                quantity_units=item.quantity
            ))

        db.commit()
        return {"message": "Order logged. Pending distributor approval.", "id": db_order.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{order_id}/approve", status_code=status.HTTP_200_OK)
def approve_secondary_order(order_id: int, db: Session = Depends(get_db)):
    """Stage 2: Distributor actively accepts the order."""
    order = db.query(SecondaryOrder).filter(SecondaryOrder.id == order_id).first()
    if not order or order.status not in ["PENDING", "Pending"]:
        raise HTTPException(status_code=400, detail="Order not found or not in PENDING state.")

    order.status = "APPROVED"
    db.commit()
    return {"message": "Order actively approved for dispatch."}


@router.post("/{order_id}/dispatch", status_code=status.HTTP_200_OK)
def dispatch_secondary_order(order_id: int, payload: DispatchPayload, db: Session = Depends(get_db)):
    """Stage 3: Dispatch logs details, deducts sender stock, and creates financial debt."""
    try:
        order = db.query(SecondaryOrder).filter(SecondaryOrder.id == order_id).first()
        if not order or order.status != "APPROVED":
            raise HTTPException(status_code=400, detail="Order must be APPROVED before dispatch.")

        invoice_ref = f"INV-SEC-{order.id}"

        # 1. Deduct Stock from Distributor (Since it has left their warehouse)
        for item in order.items:
            StockService.update_stock(db, "Distributor", order.distributor_id, item.product_id, item.batch_number,
                                      -item.quantity_units, invoice_ref, "SEC_DISPATCH_OUT")

        # 2. Record Financial Receivable (Retailer now officially owes the money)
        FinanceService.record_transaction(db, "Retailer", order.retailer_id, "INVOICE", order.total_amount, invoice_ref)

        order.status = "DISPATCHED"
        db.commit()
        return {"message": "Order dispatched. Stock deducted and ledger updated."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{order_id}/receive")
def receive_secondary_order(order_id: int, db: Session = Depends(get_db)):
    """Stage 4: Retailer physically receives the goods (Adds to their stock)."""
    try:
        order = db.query(SecondaryOrder).filter(SecondaryOrder.id == order_id).first()
        if not order or order.status != "DISPATCHED":
            raise HTTPException(status_code=400, detail="Order must be DISPATCHED before receiving.")

        invoice_ref = f"INV-SEC-{order.id}"

        # 1. Add Stock to Retailer (Since it arrived at their shop)
        for item in order.items:
            StockService.update_stock(db, "Retailer", order.retailer_id, item.product_id, item.batch_number,
                                      item.quantity_units, invoice_ref, "SEC_RECEIVE_IN")

        order.status = "RECEIVED"
        db.commit()

        return {"message": "Goods received. Retailer inventory updated."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_secondary_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(SecondaryOrder).filter(SecondaryOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Secondary Order not found")

        # If it was already dispatched, revert stock and finances
        if order.status in ["DISPATCHED", "RECEIVED"]:
            for item in order.items:
                StockService.update_stock(db, "Distributor", order.distributor_id, item.product_id, item.batch_number,
                                          item.quantity_units, f"CNCL-{order.id}", "CANCEL_OUT")
                # Only deduct retailer if they had already received it
                if order.status == "RECEIVED":
                    StockService.update_stock(db, "Retailer", order.retailer_id, item.product_id, item.batch_number,
                                              -item.quantity_units, f"CNCL-{order.id}", "CANCEL_IN")

            FinanceService.record_transaction(db, "Retailer", order.retailer_id, "CREDIT_NOTE", order.total_amount,
                                              f"CNCL-{order.id}")

        order.status = "CANCELLED"
        db.commit()
        return {"message": "Order cancelled."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def get_all_secondary_orders(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    query = db.query(SecondaryOrder)

    if not current_user.role:
        return []

    role_name = current_user.role.name

    # 1. Admin gets everything
    if role_name == "Admin":
        pass

    # 2. Partners strictly see their own entity's orders (Fail-Closed)
    elif role_name == "Distributor":
        distributor = db.query(Distributor).filter(Distributor.user_id == current_user.id).first()
        if not distributor:
            return []
        query = query.filter(SecondaryOrder.distributor_id == distributor.id)

    elif role_name == "Retailer":
        retailer = db.query(Retailer).filter(Retailer.user_id == current_user.id).first()
        if not retailer:
            return []
        query = query.filter(SecondaryOrder.retailer_id == retailer.id)

    elif role_name == "SuperStockist":
        return []

    # 3. Internal Teams (ZSM, RSM, ASM, SO) scoped by Geography
    else:
        scope = PermissionService.get_geo_scope(current_user)

        # If the permission service returns the failsafe ID, deny access
        if not scope or "id" in scope:
            return []

        # THE FAT TABLE FIX: We delete the Retailer join and filter the SecondaryOrder table directly.
        query = query.filter_by(**scope)

    # Execute final secured query
    orders = query.order_by(SecondaryOrder.id.desc()).all()

    # Format result
    result = []
    for o in orders:
        items_data = [{"product_id": i.product_id, "quantity_units": i.quantity_units, "batch_number": i.batch_number}
                      for i in o.items]

        result.append({
            "id": o.id,
            "invoice_number": f"INV-SEC-{o.id}",
            "distributor_id": o.distributor_id,
            "retailer_id": o.retailer_id,
            "status": o.status or "PENDING",
            "total_amount": float(o.total_amount) if o.total_amount else 0.0,
            "created_at": o.order_date,
            "items": items_data
        })

    return result