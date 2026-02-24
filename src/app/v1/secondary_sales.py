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
from src.app.schemas.orders import SecondaryOrderCreate, SecondaryOrderRead
from src.app.services.stock_service import StockService
from src.app.services.finance_service import FinanceService
from src.app.services.tax_service import TaxService
from src.app.crud.secondary_sales import create_secondary_order

router = APIRouter()


@router.post("/", status_code=201)
def record_secondary_sale(sale_in: SecondaryOrderCreate, db: Session = Depends(get_db)):
    try:
        # 1. Fetch Partners
        retailer = db.query(Retailer).filter(Retailer.id == sale_in.retailer_id, Retailer.is_active == True).first()
        if not retailer:
            raise HTTPException(status_code=404, detail="Retailer not found or inactive.")

        distributor = db.query(Distributor).filter(Distributor.id == sale_in.distributor_id, Distributor.is_active == True).first()
        if not distributor:
            raise HTTPException(status_code=404, detail="Distributor not found or inactive.")

        # 2. STRICT LINKAGE CHECK (Prevents Poaching)
        if retailer.linked_distributor_id != distributor.id:
            raise HTTPException(
                status_code=400,
                detail=f"Unauthorized: Retailer '{retailer.shop_name}' is not linked to this Distributor."
            )

        # 3. GEOGRAPHY CHECK FIX (State vs State)
        retailer_state_id = TaxService.get_retailer_state_id(db, retailer.territory_id)
        if not retailer_state_id:
            raise HTTPException(status_code=400, detail="Could not resolve Retailer's State for Tax/Geography check.")

        if distributor.state_id != retailer_state_id:
            raise HTTPException(
                status_code=400,
                detail=f"Geography mismatch. Distributor operates in State {distributor.state_id}, but Retailer is in State {retailer_state_id}."
            )

        # 4. Set variables for GST Calculation
        seller_state_id = distributor.state_id
        buyer_state_id = retailer_state_id

        total_invoice_amount = Decimal("0.00")
        total_cgst = Decimal("0.00")
        total_sgst = Decimal("0.00")
        total_igst = Decimal("0.00")
        invoice_number = f"INV-SEC-{sale_in.retailer_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 5. Process Items
        for item in sale_in.items:
            product = db.query(ProductMaster).filter(ProductMaster.id == item.product_id,
                                                     ProductMaster.is_active == True).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found or inactive.")

            base_item_amount = Decimal(str(item.quantity)) * Decimal(str(product.base_price))

            tax_details = TaxService.calculate_gst(
                base_amount=base_item_amount,
                gst_percent=Decimal(str(product.gst_percent)),
                seller_state_id=seller_state_id,
                buyer_state_id=buyer_state_id
            )

            total_invoice_amount += tax_details["final_amount"]
            total_cgst += tax_details["cgst"]
            total_sgst += tax_details["sgst"]
            total_igst += tax_details["igst"]

            StockService.update_stock(
                db=db, entity_type="Distributor", entity_id=sale_in.distributor_id,
                product_id=item.product_id, batch_number=item.batch_number,
                qty_change=-item.quantity, ref_doc=invoice_number, trans_type="SECONDARY_SALE_OUT"
            )

            StockService.update_stock(
                db=db, entity_type="Retailer", entity_id=sale_in.retailer_id,
                product_id=item.product_id, batch_number=item.batch_number,
                qty_change=item.quantity, ref_doc=invoice_number, trans_type="SECONDARY_SALE_IN"
            )

        FinanceService.record_transaction(
            db=db, party_type="Retailer", party_id=sale_in.retailer_id,
            trans_type="INVOICE", amount=total_invoice_amount, ref_doc=invoice_number
        )

        db_order = create_secondary_order(
            db=db, retailer_id=sale_in.retailer_id, distributor_id=sale_in.distributor_id,
            items_in=[item.model_dump() for item in sale_in.items],
            total_amount=total_invoice_amount
        )

        db.commit()

        return {
            "message": "Secondary sale recorded safely.",
            "invoice_number": invoice_number,
            "amount_billed": total_invoice_amount,
            "tax_breakdown": {"CGST": total_cgst, "SGST": total_sgst, "IGST": total_igst}
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_secondary_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(SecondaryOrder).filter(SecondaryOrder.id == order_id).first()

        if not order:
            raise HTTPException(status_code=404, detail="Secondary Order not found")

        if order.status != "Pending":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel order. Current status is '{order.status}'."
            )

        for item in order.items:
            StockService.update_stock(
                db=db, entity_type="Retailer", entity_id=order.retailer_id,
                product_id=item.product_id, batch_number=item.batch_number,
                qty_change=-item.quantity_units, ref_doc=f"CANCEL-SEC-{order.id}", trans_type="CANCEL_SECONDARY_IN"
            )

            StockService.update_stock(
                db=db, entity_type="Distributor", entity_id=order.distributor_id,
                product_id=item.product_id, batch_number=item.batch_number,
                qty_change=item.quantity_units, ref_doc=f"CANCEL-SEC-{order.id}", trans_type="CANCEL_SECONDARY_OUT"
            )

        if order.total_amount and order.total_amount > 0:
            FinanceService.record_transaction(
                db=db, party_type="Retailer", party_id=order.retailer_id,
                trans_type="CREDIT_NOTE", amount=Decimal(str(order.total_amount)), ref_doc=f"CANCEL-INV-SEC-{order.id}"
            )

        order.status = "Cancelled"
        db.commit()
        return {"message": f"Secondary Order {order.id} has been cancelled successfully, stock and finances reverted."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[SecondaryOrderRead])
def get_all_secondary_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # INJECTING CURRENT USER HERE FOR SECURITY
):
    """Fetch secondary orders filtered dynamically based on user role and geographic scope."""
    query = db.query(SecondaryOrder)

    # If user has no role assigned, deny access
    if not current_user.role:
        return []

    # 1. Admin or specifically allowed user sees everything
    user_permissions = [p.name for p in current_user.role.permissions] if current_user.role.permissions else []
    if current_user.role.name == "Admin" or "view_all_orders" in user_permissions:
        return query.order_by(SecondaryOrder.id.desc()).all()

    # 2. External Partners (Distributors / Retailers) see only their own accounts
    if current_user.role.name == "Distributor":
        distributor = db.query(Distributor).filter(Distributor.user_id == current_user.id).first()
        if distributor:
            query = query.filter(SecondaryOrder.distributor_id == distributor.id)
        return query.order_by(SecondaryOrder.id.desc()).all()

    elif current_user.role.name == "Retailer":
        retailer = db.query(Retailer).filter(Retailer.user_id == current_user.id).first()
        if retailer:
            query = query.filter(SecondaryOrder.retailer_id == retailer.id)
        return query.order_by(SecondaryOrder.id.desc()).all()

    # 3. Internal Hierarchy (ZSM, RSM, SO, ASM) - Enforce Geographic Scope!
    query = query.join(Retailer, SecondaryOrder.retailer_id == Retailer.id)

    if current_user.assigned_territory_id:
        query = query.filter(Retailer.territory_id == current_user.assigned_territory_id)
    elif current_user.assigned_area_id:
        # Assuming Retailer model is linked hierarchically down to Area/Region/State
        # For true strictness, you'd join up to the level, but if territory maps neatly, you filter through Territory.
        # Simple fallback if territory handles everything:
        pass # Add complex joins here if needed, otherwise stick to Territory/Zone logic
    elif current_user.assigned_zone_id:
        # Example: Filter by joining Territory -> Area -> Region -> Zone (if your models support it)
        pass

    return query.order_by(SecondaryOrder.id.desc()).all()