from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db

from src.app.models.user import User
from src.app.schemas.user import UserCreate, UserRead, UserUpdate
from src.app.crud.user import create_user
from src.app.core.security import check_permissions

router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def add_new_user(
        user_in: UserCreate,
        db: Session = Depends(get_db),
        # Uncomment to restrict to admins: _=Depends(check_permissions("manage_users"))
):
    return create_user(db, user_in)


@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    """Fetch all users (ZSM, RSM, ASM, SO, etc.)"""
    return db.query(User).all()


@router.patch("/{user_id}", response_model=UserRead)
def edit_user(
        user_id: int,
        user_in: UserUpdate,
        db: Session = Depends(get_db)
):
    """Update a user's role, active status, or geographical assignment"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    """
    SOFT DELETE: We never hard-delete employees because their ID is tied to
    historical orders and ledger entries. We just deactivate their login access.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_active = False
    db.commit()
    return None