from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.finance import PaymentCreate, FinancialLedgerRead
from src.app.services.finance_service import FinanceService
from src.app.models.finance import FinancialLedger
from sqlalchemy import func
from src.app.models.partner import SuperStockist, Distributor, Retailer
from src.app.core.security import get_current_user
from src.app.models.user import User
from src.app.services.permission_service import PermissionService

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


from src.app.core.security import get_current_user
from src.app.models.user import User
from src.app.services.permission_service import PermissionService


@router.get("/summary", summary="Get Scoped Finance Summary")
def get_company_finance_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Calculates receivables and recent transactions scoped to the user's hierarchy."""

    scope = PermissionService.get_geo_scope(current_user)

    # Base queries for outstanding balances
    ss_query = db.query(func.sum(SuperStockist.outstanding_balance))
    dist_query = db.query(func.sum(Distributor.outstanding_balance))
    ret_query = db.query(func.sum(Retailer.outstanding_balance))

    # Base query for ledger transactions
    ledger_query = db.query(FinancialLedger)

    # Apply geographic scope if not Admin
    if scope and "id" not in scope and current_user.role.name != "Admin":
        # Apply filters for the outstanding metrics
        for key, value in scope.items():
            if value is not None:
                if hasattr(SuperStockist, key): ss_query = ss_query.filter(getattr(SuperStockist, key) == value)
                if hasattr(Distributor, key): dist_query = dist_query.filter(getattr(Distributor, key) == value)
                if hasattr(Retailer, key): ret_query = ret_query.filter(getattr(Retailer, key) == value)

        # To scope transactions, we don't have a direct geographic join yet,
        # so we fetch the allowed Partner IDs first.
        allowed_ss = [s[0] for s in db.query(SuperStockist.id).filter_by(**scope).all()] if hasattr(SuperStockist,
                                                                                                    list(scope.keys())[
                                                                                                        0]) else []
        allowed_dist = [d[0] for d in db.query(Distributor.id).filter_by(**scope).all()] if hasattr(Distributor,
                                                                                                    list(scope.keys())[
                                                                                                        0]) else []
        allowed_ret = [r[0] for r in db.query(Retailer.id).filter_by(**scope).all()] if hasattr(Retailer,
                                                                                                list(scope.keys())[
                                                                                                    0]) else []

        ledger_query = ledger_query.filter(
            (FinancialLedger.party_type == "SuperStockist" and FinancialLedger.party_id.in_(allowed_ss)) |
            (FinancialLedger.party_type == "Distributor" and FinancialLedger.party_id.in_(allowed_dist)) |
            (FinancialLedger.party_type == "Retailer" and FinancialLedger.party_id.in_(allowed_ret))
        )

    ss_owed = ss_query.scalar() or 0.00
    dist_owed = dist_query.scalar() or 0.00
    ret_owed = ret_query.scalar() or 0.00
    total_receivables = float(ss_owed) + float(dist_owed) + float(ret_owed)

    recent_transactions = ledger_query.order_by(FinancialLedger.created_at.desc()).limit(50).all()

    return {
        "metrics": {
            "total_receivables": total_receivables,
            "breakdown": {
                "super_stockists": float(ss_owed),
                "distributors": float(dist_owed),
                "retailers": float(ret_owed)
            }
        },
        "recent_global_transactions": recent_transactions
    }