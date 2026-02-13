from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from src.app.core.database import Base
from sqlalchemy import Table

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    role_id = Column(Integer, ForeignKey("roles.id"))

    # Hierarchy Scoping
    assigned_zone_id = Column(Integer, ForeignKey("zone.id"), nullable=True)
    assigned_region_id = Column(Integer, ForeignKey("region.id"), nullable=True)
    assigned_area_id = Column(Integer, ForeignKey("area.id"), nullable=True)
    assigned_territory_id = Column(Integer, ForeignKey("territory.id"), nullable=True)

    zone = relationship("Zone")
    region = relationship("Region")
    area = relationship("Area")
    territory = relationship("Territory")


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    # This attribute must be named "roles" if Role uses back_populates="roles"
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

    # This attribute "permissions" matches the back_populates in the Permission class
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
