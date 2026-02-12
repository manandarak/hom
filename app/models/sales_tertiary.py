from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Date
from src.app.core.database import Base


class EndConsumer(Base):
    __tablename__ = "end_consumer"

    id = Column(Integer, primary_key=True, index=True)
    territory_id = Column(Integer, ForeignKey("territories.id"))
    name = Column(String(255))
    type = Column(String(50))  # "Barber"
    mobile_number = Column(String(15))


class TertiaryOrder(Base):
    __tablename__ = "tertiary_order"

    id = Column(BigInteger, primary_key=True, index=True)
    request_date = Column(Date)
    end_consumer_id = Column(Integer, ForeignKey("end_consumer.id"))
    assigned_so_id = Column(BigInteger, ForeignKey("users.id"))
    fulfilled_by_retailer_id = Column(Integer, ForeignKey("retailer.id"))
    status = Column(String(50))



