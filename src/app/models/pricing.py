from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, ForeignKey, Date
from src.app.core.database import Base


class TradeScheme(Base):
    __tablename__ = "trade_schemes"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product_master.id"), nullable=False)
    scheme_name = Column(String(100), nullable=False)  # e.g., "Summer Mega Sale"

    # The Triggers & Rewards
    min_qty = Column(Integer, nullable=False)  # "Buy X..."
    discount_percent = Column(DECIMAL(5, 2), default=0.00)  # "...get Y% off..."
    free_qty = Column(Integer, default=0)  # "...and Z items free!"

    # Validity
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)