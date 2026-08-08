from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse
from app.security import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.email, user.role), role=user.role,
                         full_name=user.full_name, email=user.email)

@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"email": user.email, "role": user.role, "full_name": user.full_name}
