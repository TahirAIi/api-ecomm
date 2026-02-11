from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.core.config import settings
from app.services.user import get_user_service
from app.schemas.user import User, UserCreate, PasswordUpdate
from app.api.deps import get_db
from app.schemas.token import Token
from app.api.deps import get_current_active_user
from app.services.user import UserService

router = APIRouter()


@router.post("/register", response_model=User, status_code=201)
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service)
) -> Any:
    if user_service.is_email_taken(db, email=user_in.email):
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = user_service.create(db, obj_in=user_in)
    return user


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    user = user_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.uuid, expires_delta=access_token_expires)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> Any:
    return current_user


@router.put("/me/password", response_model=dict)
def update_password(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    password_data: PasswordUpdate,
    user_service: UserService = Depends(get_user_service)
) -> Any:
    if not user_service.authenticate(
        db, email=current_user.email, password=password_data.current_password
    ):
        raise HTTPException(status_code=400, detail="Incorrect password")
    user_service.update_password(
        db, user=current_user, new_password=password_data.new_password
    )
    return {"msg": "Password updated successfully"}
