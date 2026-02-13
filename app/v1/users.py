from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.user import UserCreate, UserRead
from src.app.crud.user import create_user
from src.app.core.security import check_permissions

router = APIRouter()


@router.post("/", response_model=UserRead)
def add_new_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    # Only users with 'manage_users' permission can access this
    _=Depends(check_permissions("manage_users"))
):
    return create_user(db, user_in)