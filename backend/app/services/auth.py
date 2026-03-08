import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import RefreshToken, User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Decode an access token and return the user_id, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def create_refresh_token_value() -> str:
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def register_user(email: str, password: str, name: str, db: AsyncSession) -> User:
    user = User(
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        name=name.strip(),
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def store_refresh_token(user_id: str, token_value: str, db: AsyncSession) -> None:
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token_value),
        expires_at=expires_at,
    )
    db.add(refresh_token)
    await db.flush()


async def validate_refresh_token(token_value: str, db: AsyncSession) -> RefreshToken | None:
    token_hash = hash_token(token_value)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    refresh_token = result.scalar_one_or_none()
    if not refresh_token:
        return None
    if refresh_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        await db.delete(refresh_token)
        await db.flush()
        return None
    return refresh_token


async def revoke_refresh_token(token_value: str, db: AsyncSession) -> None:
    token_hash = hash_token(token_value)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    refresh_token = result.scalar_one_or_none()
    if refresh_token:
        await db.delete(refresh_token)
        await db.flush()
