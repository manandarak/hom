from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, BigInteger, DateTime, func
from sqlalchemy.orm import relationship
from src.app.core.database import Base

class ProductMaster(Base):
    __tablename__ = "product_master"
    id = Column(Integer, primary_key=True, index=True)
    sku_code = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    mrp = Column(DECIMAL(10, 2))
    base_price = Column(DECIMAL(10, 2))
    units_per_case = Column(Integer, default=1)

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