from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, BigInteger, Date
from sqlalchemy.orm import relationship
from src.app.core.database import Base


class PrimaryOrder(Base):
    __tablename__ = "primary_order"

    id = Column(BigInteger, primary_key=True, index=True)
    order_number = Column(String(100), unique=True)
    type = Column(String(50))  
    from_entity_id = Column(Integer)
    to_entity_id = Column(Integer)
    status = Column(String(50), default="Pending")

    # Virtual Elements (ORM Relationships)
    items = relationship("PrimaryOrderItems", back_populates="order")
    invoice = relationship("PrimaryInvoice", back_populates="order", uselist=False)


class PrimaryOrderItems(Base):
    __tablename__ = "primary_order_items"

    id = Column(BigInteger, primary_key=True, index=True)
    primary_order_id = Column(BigInteger, ForeignKey("primary_order.id"))
    product_id = Column(Integer, ForeignKey("product_master.id"))
    quantity_cases = Column(Integer)

    order = relationship("PrimaryOrder", back_populates="items")


class PrimaryInvoice(Base):
    __tablename__ = "primary_invoice"

    id = Column(BigInteger, primary_key=True, index=True)
    primary_order_id = Column(BigInteger, ForeignKey("primary_order.id"))
    invoice_number = Column(String(100), unique=True)
    final_amount = Column(DECIMAL(12, 2))
    invoice_date = Column(Date)

    order = relationship("PrimaryOrder", back_populates="invoice")