"""
Authentication endpoints: register, login, token refresh, and user profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_active_user
from app.models.user import UserDB
from app.schemas.auth_schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefreshRequest,
    UserResponse,
    UserUpdate,
    WorkspaceCreate,
    WorkspaceResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account and return token pair."""
    service = AuthService(db)
    try:
        user = service.register(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return service.create_tokens(user)


@auth_router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email and password, receive token pair."""
    service = AuthService(db)
    user = service.authenticate(email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return service.create_tokens(user)


@auth_router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new token pair."""
    service = AuthService(db)
    tokens = service.refresh_tokens(payload.refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return tokens


@auth_router.get("/me", response_model=UserResponse)
def get_me(current_user: UserDB = Depends(get_current_active_user)):
    """Get the currently authenticated user's profile."""
    return current_user


@auth_router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile."""
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user


@auth_router.get("/workspaces", response_model=list[WorkspaceResponse])
def get_my_workspaces(
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all workspaces the current user belongs to."""
    service = AuthService(db)
    return service.get_user_workspaces(current_user.id)
