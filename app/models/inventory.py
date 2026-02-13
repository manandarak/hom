from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, BigInteger, DateTime, Date, func
from sqlalchemy.orm import relationship
from src.app.core.database import Base
from datetime import datetime, date

class StockLedger(Base):
    """The History of Truth - Every movement is recorded here"""
    __tablename__ = "stock_ledger"
    id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    entity_type = Column(String)
    entity_id = Column(Integer)
    product_id = Column(Integer, ForeignKey("product_master.id"))
    transaction_type = Column(String)
    reference_document = Column(String)
    quantity_change = Column(Integer)
    closing_balance = Column(Integer)

class FactoryInventory(Base):
    __tablename__ = "factory_inventory"
    id = Column(Integer, primary_key=True)
    factory_id = Column(Integer, ForeignKey("factory_master.id"))
    product_id = Column(Integer, ForeignKey("product_master.id"))
    current_stock_qty = Column(Integer, default=0)

class SSInventory(Base):
    __tablename__ = "ss_inventory"
    id = Column(Integer, primary_key=True)
    ss_id = Column(Integer, ForeignKey("super_stockist.id"))
    product_id = Column(Integer, ForeignKey("product_master.id"))
    current_stock_qty = Column(Integer, default=0)

class DistributorInventory(Base):
    __tablename__ = "distributor_inventory"
    id = Column(Integer, primary_key=True)
    distributor_id = Column(Integer, ForeignKey("distributor.id"))
    product_id = Column(Integer, ForeignKey("product_master.id"))
    current_stock_qty = Column(Integer, default=0)


class FactoryMaster(Base):
    __tablename__ = "factory_master"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100))
    # Add other columns if your MySQL table has them,
    # but this is enough to satisfy the Foreign Key!


class DailyProductionLog(Base):
    __tablename__ = "daily_production_log"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=False)

    # Assuming from your screenshot you have a factory_master table.
    # If not, you can remove the ForeignKey for now and just leave it as Integer.
    factory_id = Column(Integer, ForeignKey("factory_master.id"), nullable=False)

    quantity_produced = Column(Integer, nullable=False)
    batch_number = Column(String(50), nullable=False)
    production_date = Column(Date, nullable=False)