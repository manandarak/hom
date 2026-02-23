from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.models.sales_secondary import SecondaryOrder, SecondaryOrderItems
from src.app.models.partner import Retailer, Distributor
from src.app.models.product import ProductMaster
from src.app.schemas.orders import SecondaryOrderCreate
from src.app.services.stock_service import StockService
from src.app.services.finance_service import FinanceService
from src.app.services.tax_service import TaxService
from src.app.crud.secondary_sales import create_secondary_order
from src.app.schemas.orders import SecondaryOrderRead

router = APIRouter()


@router.post("/", status_code=201)
def record_secondary_sale(sale_in: SecondaryOrderCreate, db: Session = Depends(get_db)):
    try:
        retailer = db.query(Retailer).filter(Retailer.id == sale_in.retailer_id, Retailer.is_active == True).first()
        if not retailer:
            raise HTTPException(status_code=404, detail="Retailer not found or inactive.")

        distributor = db.query(Distributor).filter(Distributor.id == sale_in.distributor_id, Distributor.is_active == True).first()
        if not distributor:
            raise HTTPException(status_code=404, detail="Distributor not found or inactive.")

        if distributor.territory_id != retailer.territory_id:
            raise HTTPException(
                status_code=400,
                detail=f"Territory mismatch. Distributor is in territory {distributor.territory_id}, but Retailer is in {retailer.territory_id}."
            )

        seller_state_id = distributor.state_id
        buyer_state_id = TaxService.get_retailer_state_id(db, retailer.territory_id)

        if not buyer_state_id:
            raise HTTPException(status_code=400, detail="Could not resolve Retailer's State for Tax Calculation.")

        total_invoice_amount = Decimal("0.00")
        total_cgst = Decimal("0.00")
        total_sgst = Decimal("0.00")
        total_igst = Decimal("0.00")
        invoice_number = f"INV-SEC-{sale_in.retailer_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

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
                db=db,
                entity_type="Retailer",
                entity_id=order.retailer_id,
                product_id=item.product_id,
                batch_number=item.batch_number,
                qty_change=-item.quantity_units,
                ref_doc=f"CANCEL-SEC-{order.id}",
                trans_type="CANCEL_SECONDARY_IN"
            )

            StockService.update_stock(
                db=db,
                entity_type="Distributor",
                entity_id=order.distributor_id,
                product_id=item.product_id,
                batch_number=item.batch_number,
                qty_change=item.quantity_units,
                ref_doc=f"CANCEL-SEC-{order.id}",
                trans_type="CANCEL_SECONDARY_OUT"
            )

        if order.total_amount and order.total_amount > 0:
            FinanceService.record_transaction(
                db=db,
                party_type="Retailer",
                party_id=order.retailer_id,
                trans_type="CREDIT_NOTE",
                amount=Decimal(str(order.total_amount)),
                ref_doc=f"CANCEL-INV-SEC-{order.id}"
            )

        order.status = "Cancelled"
        db.commit()
        return {"message": f"Secondary Order {order.id} has been cancelled successfully, stock and finances reverted."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[SecondaryOrderRead])
def get_all_secondary_orders(db: Session = Depends(get_db)):
    """Fetch all secondary orders for the table view"""
    return db.query(SecondaryOrder).order_by(SecondaryOrder.id.desc()).all()