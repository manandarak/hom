from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import Optional

class PaymentCreate(BaseModel):
    party_type: str  # SuperStockist, Distributor, Retailer
    party_id: int
    amount: float
    reference_document: str # e.g. "NEFT-TXN-123456"
    payment_mode: Optional[str] = "Bank Transfer"

class FinancialLedgerRead(BaseModel):
    id: int
    created_at: datetime
    party_type: str
    party_id: int
    transaction_type: str
    reference_document: Optional[str]
    debit_amount: Decimal
    credit_amount: Decimal
    closing_balance: Decimal
    model_config = ConfigDict(from_attributes=True)