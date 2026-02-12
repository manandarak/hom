from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.user import UserCreate, UserRead
from src.app.crud.user import create_user

router = APIRouter()

@router.post("/", response_model=UserRead)
def add_new_user(user_in: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_in)