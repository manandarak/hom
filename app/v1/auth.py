from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.services.auth_services import AuthService
# This is the function that actually exists in your security.py
from src.app.core.security import create_access_token

router = APIRouter()


@router.post("/login")
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. Authenticate the user
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # 2. Generate the token
    # We call create_access_token directly (not via AuthService)
    # We pass 'subject' because that's how it's defined in your security.py
    access_token = create_access_token(subject=user.username)

    return {"access_token": access_token, "token_type": "bearer"}