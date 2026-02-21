from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional

class StockUpdate(BaseModel):
    product_id: int
    quantity_change: int
    transaction_type: str  # Production, Sale, Return, Adjustment
    reference_document: str

class StockLedgerRead(BaseModel):
    id: int
    created_at: datetime
    entity_type: str
    entity_id: int
    product_id: int
    quantity_change: int
    closing_balance: int
    model_config = ConfigDict(from_attributes=True)

class ProductionLogCreate(BaseModel):
    product_id: int
    factory_id: int
    quantity_produced: int
    batch_number: str
    production_date: date