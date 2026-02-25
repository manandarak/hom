from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db

# Security & User models needed for data scoping
from src.app.core.security import get_current_user
from src.app.models.user import User

from src.app.models.sales_secondary import SecondaryOrder, SecondaryOrderItems
from src.app.models.partner import Retailer, Distributor
from src.app.models.product import ProductMaster
from src.app.schemas.orders import SecondaryOrderCreate
from src.app.services.stock_service import StockService
from src.app.services.finance_service import FinanceService
from src.app.services.tax_service import TaxService

router = APIRouter()


@router.post("/", status_code=201)
def record_secondary_sale(sale_in: SecondaryOrderCreate, db: Session = Depends(get_db)):
    """
    Initializes a secondary sale.
    Sets status to PENDING. Does NOT move stock or update financial ledger yet.
    """
    try:
        # 1. Fetch and Validate Partners
        retailer = db.query(Retailer).filter(Retailer.id == sale_in.retailer_id, Retailer.is_active == True).first()
        if not retailer:
            raise HTTPException(status_code=404, detail="Retailer not found or inactive.")

        distributor = db.query(Distributor).filter(Distributor.id == sale_in.distributor_id,
                                                   Distributor.is_active == True).first()
        if not distributor:
            raise HTTPException(status_code=404, detail="Distributor not found or inactive.")

        # 2. Smart Linkage & Geography Validation
        if retailer.linked_distributor_id and retailer.linked_distributor_id != distributor.id:
            raise HTTPException(
                status_code=400,
                detail=f"Unauthorized: Retailer '{retailer.shop_name}' is explicitly linked to a different Distributor."
            )

        retailer_state_id = TaxService.get_retailer_state_id(db, retailer.territory_id)
        if distributor.state_id != retailer_state_id:
            raise HTTPException(
                status_code=400,
                detail="Geography mismatch. Distributor and Retailer must be in the same State."
            )

        # 3. Calculate Preliminary Total (to save in order)
        total_invoice_amount = Decimal("0.00")
        for item in sale_in.items:
            product = db.query(ProductMaster).filter(ProductMaster.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found.")

            base_item_amount = Decimal(str(item.quantity)) * Decimal(str(product.base_price))
            tax_details = TaxService.calculate_gst(
                base_amount=base_item_amount,
                gst_percent=Decimal(str(product.gst_percent)),
                seller_state_id=distributor.state_id,
                buyer_state_id=retailer_state_id
            )
            total_invoice_amount += tax_details["final_amount"]

        # 4. Create Order in PENDING status
        db_order = SecondaryOrder(
            distributor_id=sale_in.distributor_id,
            retailer_id=sale_in.retailer_id,
            total_amount=total_invoice_amount,
            status="PENDING",  # Crucial change
            order_date=datetime.now().date()
        )
        db.add(db_order)
        db.flush()

        # 5. Add Items
        for item in sale_in.items:
            db_item = SecondaryOrderItems(
                secondary_order_id=db_order.id,
                product_id=item.product_id,
                batch_number=item.batch_number,
                quantity_units=item.quantity
            )
            db.add(db_item)

        db.commit()

        return {
            "message": "Secondary sale logged. Awaiting retailer receipt to finalize stock and ledger.",
            "id": db_order.id,
            "status": "PENDING"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/receive")
def receive_secondary_order(order_id: int, db: Session = Depends(get_db)):
    """
    Finalizes the sale: Moves stock from Distributor to Retailer
    and generates the financial ledger entry (Receivable).
    """
    try:
        order = db.query(SecondaryOrder).filter(SecondaryOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Secondary Order not found")
        if order.status != "PENDING":
            raise HTTPException(status_code=400, detail=f"Order cannot be received. Current status: {order.status}")

        invoice_ref = f"INV-SEC-{order.id}"

        # 1. Automated Stock Transfer
        for item in order.items:
            # Deduct from Distributor
            StockService.update_stock(
                db=db, entity_type="Distributor", entity_id=order.distributor_id,
                product_id=item.product_id, batch_number=item.batch_number,
                qty_change=-item.quantity_units, ref_doc=invoice_ref, trans_type="SECONDARY_SALE_OUT"
            )
            # Add to Retailer
            StockService.update_stock(
                db=db, entity_type="Retailer", entity_id=order.retailer_id,
                product_id=item.product_id, batch_number=item.batch_number,
                qty_change=item.quantity_units, ref_doc=invoice_ref, trans_type="SECONDARY_SALE_IN"
            )

        # 2. Automated Financial Ledger Entry (Money now officially owed)
        FinanceService.record_transaction(
            db=db, party_type="Retailer", party_id=order.retailer_id,
            trans_type="INVOICE", amount=order.total_amount, ref_doc=invoice_ref
        )

        order.status = "RECEIVED"
        db.commit()

        return {"message": "Goods received. Inventory transferred and Financial Ledger updated."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_secondary_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(SecondaryOrder).filter(SecondaryOrder.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Secondary Order not found")

        # If it was already received, we need to revert stock and finances
        if order.status == "RECEIVED":
            for item in order.items:
                StockService.update_stock(db, "Retailer", order.retailer_id, item.product_id, item.batch_number,
                                          -item.quantity_units, f"CNCL-{order.id}", "CANCEL_IN")
                StockService.update_stock(db, "Distributor", order.distributor_id, item.product_id, item.batch_number,
                                          item.quantity_units, f"CNCL-{order.id}", "CANCEL_OUT")

            FinanceService.record_transaction(db, "Retailer", order.retailer_id, "CREDIT_NOTE", order.total_amount,
                                              f"CNCL-{order.id}")

        order.status = "Cancelled"
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

    user_permissions = [p.name for p in current_user.role.permissions] if current_user.role.permissions else []

    if current_user.role.name == "Admin" or "view_all_orders" in user_permissions:
        pass
    elif current_user.role.name == "Distributor":
        distributor = db.query(Distributor).filter(Distributor.user_id == current_user.id).first()
        if distributor:
            query = query.filter(SecondaryOrder.distributor_id == distributor.id)
    elif current_user.role.name == "Retailer":
        retailer = db.query(Retailer).filter(Retailer.user_id == current_user.id).first()
        if retailer:
            query = query.filter(SecondaryOrder.retailer_id == retailer.id)
    else:
        query = query.join(Retailer, SecondaryOrder.retailer_id == Retailer.id)
        if current_user.assigned_territory_id:
            query = query.filter(Retailer.territory_id == current_user.assigned_territory_id)

    orders = query.order_by(SecondaryOrder.id.desc()).all()

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