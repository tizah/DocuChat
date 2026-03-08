from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentUser
from app.exceptions import ConflictError, ValidationError
from app.models.user import User
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token_value,
    register_user,
    revoke_refresh_token,
    store_refresh_token,
    validate_refresh_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


# --- Schemas ---


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthMessageResponse(BaseModel):
    message: str


# --- Helpers ---


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/api/auth",
        max_age=settings.refresh_token_expire_days * 86400,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")


# --- Routes ---


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: RegisterRequest, response: Response, db: DbSession) -> User:
    if len(request.password) < 8:
        raise ValidationError("Password must be at least 8 characters")

    # Check duplicate email
    result = await db.execute(select(User).where(User.email == request.email.lower().strip()))
    if result.scalar_one_or_none():
        raise ConflictError("Email already registered")

    user = await register_user(request.email, request.password, request.name, db)

    # Issue tokens
    access_token = create_access_token(user.id)
    refresh_value = create_refresh_token_value()
    await store_refresh_token(user.id, refresh_value, db)

    _set_auth_cookies(response, access_token, refresh_value)
    return user


@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest, response: Response, db: DbSession) -> User:
    user = await authenticate_user(request.email, request.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(user.id)
    refresh_value = create_refresh_token_value()
    await store_refresh_token(user.id, refresh_value, db)

    _set_auth_cookies(response, access_token, refresh_value)
    return user


@router.post("/refresh", response_model=AuthMessageResponse)
async def refresh(
    response: Response,
    db: DbSession,
    refresh_token: str | None = Cookie(default=None),
) -> dict:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    token_record = await validate_refresh_token(refresh_token, db)
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Rotate: revoke old, issue new
    await revoke_refresh_token(refresh_token, db)

    new_access = create_access_token(token_record.user_id)
    new_refresh = create_refresh_token_value()
    await store_refresh_token(token_record.user_id, new_refresh, db)

    _set_auth_cookies(response, new_access, new_refresh)
    return {"message": "Tokens refreshed"}


@router.post("/logout", response_model=AuthMessageResponse)
async def logout(
    response: Response,
    db: DbSession,
    refresh_token: str | None = Cookie(default=None),
) -> dict:
    if refresh_token:
        await revoke_refresh_token(refresh_token, db)
    _clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> User:
    return current_user
