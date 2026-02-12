from sqlalchemy.orm import Session
from src.app.models.user import User, Role
from src.app.schemas.user import UserCreate
from passlib.context import CryptContext

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_users_by_role(db: Session, role_id: int):
    return db.query(User).filter(User.role_id == role_id).all()


def create_user(db: Session, user_in: UserCreate):
    hashed_password = pwd_context.hash(user_in.password)

    db_user = User(
        username=user_in.username,
        password_hash=hashed_password,
        is_active=user_in.is_active,
        role_id=user_in.role_id,
        assigned_zone_id=user_in.assigned_zone_id,
        assigned_region_id=user_in.assigned_region_id,
        assigned_area_id=user_in.assigned_area_id,
        assigned_territory_id=user_in.assigned_territory_id
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_roles(db: Session):
    return db.query(Role).all()


def update_user_status(db: Session, user_id: int, active_status: bool):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.is_active = active_status
        db.commit()
    return db_user