"""Security utilities: JWT token creation/decoding and password hashing."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import uuid

from jose import JWTError, jwt
import bcrypt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt (cost=12)."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# Alias for compatibility
get_password_hash = hash_password


def create_access_token(
    subject: str,
    school_id: Optional[str] = None,
    is_super_admin: bool = False,
) -> tuple[str, str]:
    """
    Create a short-lived JWT access token.

    Args:
        subject: User ID (UUID string)
        school_id: School UUID string (None for super admin)
        is_super_admin: Whether the user is a super admin

    Returns:
        (encoded JWT string, jti)
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "school_id": school_id,
        "is_super_admin": is_super_admin,
        "jti": jti,
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti


def create_refresh_token(subject: str) -> tuple[str, str]:
    """
    Create a long-lived JWT refresh token.

    Args:
        subject: User ID (UUID string)

    Returns:
        (encoded JWT string, jti)
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "jti": jti,
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises:
        JWTError: if token is invalid or expired
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
