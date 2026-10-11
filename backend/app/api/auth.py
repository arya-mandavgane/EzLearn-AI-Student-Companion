"""
auth.py — User Authentication & Accounts (Phase 1)
Supports registration, login, JWT token issuance, protected /me, and Google OAuth stubs.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import User
from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Student's name")
    email: str = Field(..., min_length=5, description="Email address")
    age: int = Field(..., ge=1, le=150, description="Student's age")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")


class LoginRequest(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    age: Optional[int] = None
    is_active: bool = True
    daily_requests_count: int = 0


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


# ── POST /auth/register ───────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new student account."""
    clean_email = req.email.strip().lower()

    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please log in instead.",
        )

    hashed = get_password_hash(req.password)
    user = User(
        email=clean_email,
        hashed_password=hashed,
        name=req.name.strip(),
        age=req.age,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New user registered: %s (id: %s)", clean_email, user.id)

    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "name": user.name},
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile(
            id=user.id,
            email=user.email,
            name=user.name,
            age=user.age,
            is_active=user.is_active,
            daily_requests_count=user.daily_requests_count or 0,
        ),
    )


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Log in with email and password."""
    clean_email = req.email.strip().lower()

    user = db.query(User).filter(User.email == clean_email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. Please try again.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    logger.info("User logged in: %s", clean_email)

    token = create_access_token(
        subject=user.id,
        extra_claims={"email": user.email, "name": user.name},
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile(
            id=user.id,
            email=user.email,
            name=user.name,
            age=user.age,
            is_active=user.is_active,
            daily_requests_count=user.daily_requests_count or 0,
        ),
    )


# ── GET /auth/me ──────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    """Return profile of the currently logged-in student."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        age=current_user.age,
        is_active=current_user.is_active,
        daily_requests_count=current_user.daily_requests_count or 0,
    )


# ── Google OAuth Stubs ────────────────────────────────────────────────────────

@router.get("/google/login")
def google_login():
    """Google sign-in status."""
    return {
        "status": "not_configured",
        "message": "Google Sign-in credentials are not configured on this server. Please use email & password to sign in.",
    }


@router.get("/google/callback")
def google_callback():
    return {
        "status": "not_configured",
        "message": "Google Sign-in credentials are not configured on this server.",
    }
