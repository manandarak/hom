from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from src.app.models.sales_secondary import SecondaryOrder, SecondaryOrderItems
from src.app.schemas.orders import SecondaryOrderCreate
from src.app.core.database import get_db
from src.app.schemas.orders import SecondaryOrderCreate
from src.app.services.stock_service import StockService
from src.app.crud.secondary_sales import create_secondary_order
from fastapi import APIRouter, Depends, HTTPException, status
# Important Imports
from src.app.models.partner import Retailer, Distributor
from src.app.models.product import ProductMaster
from src.app.services.finance_service import FinanceService
from src.app.services.tax_service import TaxService  # <-- NEW TAX ENGINE

router = APIRouter()


@router.post("/", status_code=201)
def record_secondary_sale(sale_in: SecondaryOrderCreate, db: Session = Depends(get_db)):
    try:
        # ==========================================
        # 1. VALIDATION GAPS & SECURITY CHECKS
        # ==========================================
        retailer = db.query(Retailer).filter(Retailer.id == sale_in.retailer_id).first()
        if not retailer:
            raise HTTPException(status_code=404, detail="Retailer not found")

        distributor = db.query(Distributor).filter(Distributor.id == sale_in.distributor_id).first()
        if not distributor:
            raise HTTPException(status_code=404, detail="Distributor not found")

        # SECURITY FIX: Ensure the Retailer actually belongs to this Distributor!
        if retailer.linked_distributor_id != distributor.id:
            raise HTTPException(
                status_code=403,
                detail=f"Security Violation: Retailer '{retailer.shop_name}' is not authorized to buy from this Distributor."
            )

        # ==========================================
        # 2. DETERMINE GEOGRAPHY FOR GST
        # ==========================================
        seller_state_id = distributor.state_id
        buyer_state_id = TaxService.get_retailer_state_id(db, retailer.territory_id)

        if not buyer_state_id:
            raise HTTPException(status_code=400, detail="Could not resolve Retailer's State for Tax Calculation.")

        total_invoice_amount = 0.00
        total_cgst = 0.00
        total_sgst = 0.00
        total_igst = 0.00
        invoice_number = f"INV-SEC-{sale_in.retailer_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # ==========================================
        # 3. PROCESS ITEMS, TAXES & STOCK
        # ==========================================
        for item in sale_in.items:
            product = db.query(ProductMaster).filter(ProductMaster.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")

            # --- TAX CALCULATION FIX ---
            base_item_amount = item.quantity * float(product.base_price)

            tax_details = TaxService.calculate_gst(
                base_amount=base_item_amount,
                gst_percent=float(product.gst_percent),
                seller_state_id=seller_state_id,
                buyer_state_id=buyer_state_id
            )

            # Accumulate totals for the final invoice
            total_invoice_amount += tax_details["final_amount"]
            total_cgst += tax_details["cgst"]
            total_sgst += tax_details["sgst"]
            total_igst += tax_details["igst"]

            # --- Move Physical Stock ---
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

        # ==========================================
        # 4. CHARGE RETAILER (Finance Ledger)
        # ==========================================
        FinanceService.record_transaction(
            db=db, party_type="Retailer", party_id=sale_in.retailer_id,
            trans_type="INVOICE", amount=total_invoice_amount, ref_doc=invoice_number
        )

        # 5. Log Header to Database
        db_order = create_secondary_order(
            db=db, retailer_id=sale_in.retailer_id, distributor_id=sale_in.distributor_id,
            items_in=[item.model_dump() for item in sale_in.items]
        )

        db.commit()

        # You can now expose the exact tax breakdown to the frontend!
        return {
            "message": "Secondary sale recorded safely.",
            "invoice_number": invoice_number,
            "amount_billed": total_invoice_amount,
            "tax_breakdown": {
                "CGST": total_cgst,
                "SGST": total_sgst,
                "IGST": total_igst
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_secondary_order(order_id: int, db: Session = Depends(get_db)):
    """Cancels a secondary order if it is still pending."""
    order = db.query(SecondaryOrder).filter(SecondaryOrder.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Secondary Order not found")

    if order.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order. Current status is '{order.status}'."
        )

    order.status = "Cancelled"
    db.commit()
    return {"message": f"Secondary Order {order.id} has been cancelled successfully."}


@router.put("/{order_id}", status_code=status.HTTP_200_OK)
def update_secondary_order(order_id: int, update_in: SecondaryOrderCreate, db: Session = Depends(get_db)):
    """Updates the items in a secondary order before fulfillment."""
    order = db.query(SecondaryOrder).filter(SecondaryOrder.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Secondary Order not found")

    if order.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update order in '{order.status}' status."
        )

    # Update Header Information (if they changed the distributor or retailer)
    order.distributor_id = update_in.distributor_id
    order.retailer_id = update_in.retailer_id

    # 1. Delete the old items completely
    db.query(SecondaryOrderItems).filter(SecondaryOrderItems.secondary_order_id == order_id).delete()
    db.flush()

    # 2. Insert the fresh, corrected items
    for item in update_in.items:
        new_item = SecondaryOrderItems(
            secondary_order_id=order.id,
            product_id=item.product_id,
            batch_number=item.batch_number,
            quantity_units=item.quantity  # Note: mapped to quantity_units in secondary
        )
        db.add(new_item)

    db.commit()
    return {"message": f"Secondary Order {order.id} updated successfully."}