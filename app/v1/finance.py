from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.finance import PaymentCreate, FinancialLedgerRead
from src.app.services.finance_service import FinanceService
from src.app.models.finance import FinancialLedger

router = APIRouter()

@router.post("/payments", status_code=status.HTTP_201_CREATED)
def receive_payment(payment_in: PaymentCreate, db: Session = Depends(get_db)):
    """Logs a payment received from a partner and reduces their outstanding balance."""
    try:
        entry = FinanceService.record_transaction(
            db=db,
            party_type=payment_in.party_type,
            party_id=payment_in.party_id,
            trans_type="PAYMENT",
            amount=payment_in.amount,
            ref_doc=payment_in.reference_document
        )
        db.commit()
        return {
            "message": "Payment recorded successfully",
            "new_outstanding_balance": entry.closing_balance
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ledger/{party_type}/{party_id}", response_model=list[FinancialLedgerRead])
def get_party_ledger(party_type: str, party_id: int, db: Session = Depends(get_db)):
    """Fetches the financial history/statement of account for a specific partner."""
    return db.query(FinancialLedger).filter(
        FinancialLedger.party_type == party_type,
        FinancialLedger.party_id == party_id
    ).order_by(FinancialLedger.created_at.desc()).all()