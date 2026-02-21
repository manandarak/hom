from sqlalchemy import Column, Integer, String, DECIMAL, BigInteger, DateTime, func
from src.app.core.database import Base


class FinancialLedger(Base):
    __tablename__ = "financial_ledger"

    id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # Who is the transaction for? (SuperStockist, Distributor, Retailer)
    party_type = Column(String(50), nullable=False)
    party_id = Column(Integer, nullable=False)

    # What caused this money movement? (INVOICE, PAYMENT, CREDIT_NOTE)
    transaction_type = Column(String(50), nullable=False)
    reference_document = Column(String(100))  # e.g., "INV-1029" or "TXN-UPI-9928"

    # The Math
    debit_amount = Column(DECIMAL(12, 2), default=0.00)  # Amount added to their debt
    credit_amount = Column(DECIMAL(12, 2), default=0.00)  # Amount paid off
    closing_balance = Column(DECIMAL(12, 2), nullable=False)  # Total outstanding after this txn