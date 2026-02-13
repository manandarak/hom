from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, DECIMAL, Boolean
from sqlalchemy.orm import relationship
from src.app.core.database import Base


class SuperStockist(Base):
    __tablename__ = "super_stockist"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zone.id"), nullable=False)

    # Your original fields
    firm_name = Column(String(150), nullable=True)
    credit_limit = Column(DECIMAL(12, 2), nullable=True)

    # The new fields we just added!
    contact_number = Column(String(20), nullable=True)
    gstin = Column(String(50), nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=True)

    # Relationships
    zone = relationship("Zone")
    user = relationship("User")


class Distributor(Base):
    __tablename__ = "distributor"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    state_id = Column(Integer, ForeignKey("state.id"), nullable=False)
    parent_ss_id = Column(Integer, ForeignKey("super_stockist.id"), nullable=True)
    is_direct_party = Column(Boolean, default=False)
    firm_name = Column(String(150), nullable=True)

    # Fields added via ALTER
    contact_number = Column(String(20))
    gstin = Column(String(50))
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=True)

    user = relationship("User")
    super_stockist = relationship("SuperStockist")
   


class Retailer(Base):
    __tablename__ = "retailer"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    territory_id = Column(Integer, ForeignKey("territory.id"), nullable=False)
    linked_distributor_id = Column(Integer, ForeignKey("distributor.id"), nullable=True)
    shop_name = Column(String(150), nullable=True)
    shop_type = Column(String(100), nullable=True)

    # Fields added via ALTER
    contact_number = Column(String(20))
    gstin = Column(String(50))
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=True)

    user = relationship("User")
    distributor = relationship("Distributor")
    territory = relationship("Territory")