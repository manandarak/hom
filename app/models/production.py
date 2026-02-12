from sqlalchemy import Column, Integer, String, Date, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from src.app.core.database import Base


class FactoryMaster(Base):
    __tablename__ = "factory_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(255))


class DailyProductionLog(Base):
    __tablename__ = "daily_production_log"

    id = Column(BigInteger, primary_key=True, index=True)
    production_date = Column(Date, nullable=False)
    factory_id = Column(Integer, ForeignKey("factory_master.id"))
    product_id = Column(Integer, ForeignKey("product_master.id"))
    batch_number = Column(String(50))
    quantity_produced = Column(Integer)
    qc_status = Column(String(20))  # Passed, Failed, Pending