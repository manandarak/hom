from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from src.app.core.config import settings
from src.app.core.security import verify_password, create_access_token
from src.app.crud.user import get_user_by_username


class AuthService:
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str):
        user = get_user_by_username(db, username)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def generate_token(user_username: str):
        # This calls the function you imported from security.py
        # Make sure the parameter name matches (subject vs data)
        return create_access_token(data={"sub": user_username})