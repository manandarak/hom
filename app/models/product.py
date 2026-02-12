from sqlalchemy import Column, Integer, String, DECIMAL
from src.app.core.database import Base


class ProductMaster(Base):
    __tablename__ = "product_master"
    __table_args__ = {'extend_existing': True}  # <--- Add this

    id = Column(Integer, primary_key=True, index=True)
    sku_code = Column(String(50), unique=True, index=True)
    name = Column(String(255), nullable=False)
    mrp = Column(DECIMAL(10, 2))
    base_price = Column(DECIMAL(10, 2))
    units_per_case = Column(Integer, default=1)