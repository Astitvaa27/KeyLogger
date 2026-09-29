"""Authentication routes: register, login, current user, logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserOut, UserRegister
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(user: User) -> Token:
    token = create_access_token(subject=user.id)
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, request: Request, db: DBSession = Depends(get_db)):
    """Register a new user account."""
    existing = db.scalar(
        select(User).where(
            or_(User.email == payload.email, User.username == payload.username)
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email or username already exists",
        )

    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit.record(
        db,
        user_id=user.id,
        action="user.register",
        detail=f"username={user.username}",
        ip_address=request.client.host if request.client else None,
    )
    return _issue_token(user)


def _authenticate(db: DBSession, identifier: str, password: str) -> User:
    user = db.scalar(
        select(User).where(
            or_(User.email == identifier, User.username == identifier)
        )
    )
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, request: Request, db: DBSession = Depends(get_db)):
    """Authenticate with username-or-email + password (JSON body)."""
    user = _authenticate(db, payload.username_or_email, payload.password)
    audit.record(
        db,
        user_id=user.id,
        action="user.login",
        ip_address=request.client.host if request.client else None,
    )
    return _issue_token(user)


@router.post("/login-oauth", response_model=Token, include_in_schema=False)
def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(), db: DBSession = Depends(get_db)
):
    """OAuth2 password-flow endpoint used by the Swagger 'Authorize' button."""
    user = _authenticate(db, form_data.username, form_data.password)
    return _issue_token(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    """Stateless logout.

    JWTs are stateless, so the server records the event for audit purposes; the
    client is responsible for discarding the token.
    """
    audit.record(
        db,
        user_id=current_user.id,
        action="user.logout",
        ip_address=request.client.host if request.client else None,
    )
    return {"detail": "Logged out. Discard the access token on the client."}
