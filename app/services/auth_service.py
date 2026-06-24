import hashlib
import hmac
import random
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_password,
    decode_token,
)
from app.models.auth import PasswordResetToken
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository
from app.schemas.auth import LoginResponse, TokenResponse, UserResponse, SchoolBasicResponse


class AuthService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis | None):
        self.db = db
        self.redis = redis
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    async def login(self, identifier: str, password: str, school_id: str | None) -> LoginResponse:
        """
        1. Find user by email OR username OR phone within school
        2. Check login attempts (rate limit)
        3. Verify bcrypt password
        4. Issue access + refresh tokens
        5. Store refresh JTI in Redis
        6. Update last_login
        7. Load permissions
        """
        fail_key = f"login_fail:{school_id or 'super'}:{identifier}"
        fail_count = await self.redis.get(fail_key) if self.redis else None
        if fail_count and int(fail_count) >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account locked due to too many failed login attempts. Try again in 15 minutes.",
            )

        user = await self.user_repo.find_by_identifier(identifier, school_id)

        if not user or not verify_password(password, user.password_hash):
            # Increment fail counter
            if self.redis:
                pipe = self.redis.pipeline()
                pipe.incr(fail_key)
                pipe.expire(fail_key, 900)  # 15 minutes
                await pipe.execute()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated. Please contact administrator.",
            )

        # Clear fail counter on success
        if self.redis:
            await self.redis.delete(fail_key)

        # Issue tokens
        access_token, access_jti = create_access_token(
            subject=str(user.id),
            school_id=str(user.school_id) if user.school_id else None,
            is_super_admin=user.is_super_admin,
        )
        refresh_token, refresh_jti = create_refresh_token(subject=str(user.id))

        # Store refresh JTI in Redis
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        if self.redis:
            await self.redis.setex(f"refresh:jti:{refresh_jti}", ttl, str(user.id))

        # Update last login
        await self.user_repo.update_last_login(str(user.id))

        # Load permissions
        permissions = await self.user_repo.get_user_permissions(str(user.id))
        permissions_list = list(permissions)

        # Build school info
        school = None
        if user.school_id:
            from sqlalchemy import select
            from app.models.school import School
            result = await self.db.execute(
                select(School).where(School.id == str(user.school_id))
            )
            school_obj = result.scalar_one_or_none()
            if school_obj:
                school = SchoolBasicResponse.model_validate(school_obj)

        user_response = UserResponse(
            id=user.id,
            school_id=user.school_id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_super_admin=user.is_super_admin,
            avatar_url=user.avatar_url,
            last_login=user.last_login,
            created_at=user.created_at,
            permissions=permissions_list,
        )

        return LoginResponse(
            access_token=access_token,
            user=user_response,
            school=school,
        ), refresh_token, refresh_jti

    async def refresh_token(self, refresh_token_str: str) -> tuple[str, str]:
        """Validate refresh token and issue new access token. Returns (access_token, access_jti)."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
        try:
            payload = decode_token(refresh_token_str)
            if payload.get("type") != "refresh":
                raise credentials_exception
            jti = payload.get("jti")
            user_id = payload.get("sub")
            if not jti or not user_id:
                raise credentials_exception
        except Exception:
            raise credentials_exception

        # Check blacklist/session only when Redis is enabled
        if self.redis:
            if await self.redis.get(f"blacklist:jti:{jti}"):
                raise credentials_exception
            if not await self.redis.get(f"refresh:jti:{jti}"):
                raise credentials_exception

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise credentials_exception

        access_token, access_jti = create_access_token(
            subject=str(user.id),
            school_id=str(user.school_id) if user.school_id else None,
            is_super_admin=user.is_super_admin,
        )
        return access_token, access_jti

    async def logout(self, refresh_token_str: str, access_jti: str) -> None:
        """Blacklist both tokens in Redis."""
        try:
            payload = decode_token(refresh_token_str)
            refresh_jti = payload.get("jti")
            exp = payload.get("exp")
            if refresh_jti:
                # Blacklist refresh token
                remaining = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
                if self.redis:
                    await self.redis.setex(f"blacklist:jti:{refresh_jti}", remaining, "1")
                    await self.redis.delete(f"refresh:jti:{refresh_jti}")
        except Exception:
            pass
        # Blacklist access token
        access_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        if self.redis and access_jti:
            await self.redis.setex(f"blacklist:jti:{access_jti}", access_ttl, "1")

    async def forgot_password(self, email: str, school_id: str | None) -> None:
        """Send password reset email (always returns success to prevent enumeration)."""
        from app.tasks.emails import send_password_reset_email

        user = await self.user_repo.get_by_email(school_id, email)
        if not user:
            return  # Silent — prevent user enumeration

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        reset_token = PasswordResetToken(
            user_id=str(user.id),
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(reset_token)
        await self.db.flush()

        school_name = "SeptroSchool"
        if user.school_id:
            from sqlalchemy import select
            from app.models.school import School
            result = await self.db.execute(
                select(School).where(School.id == str(user.school_id))
            )
            school_obj = result.scalar_one_or_none()
            if school_obj:
                school_name = school_obj.name

        send_password_reset_email.delay(email, token, school_name)

    async def reset_password(self, token: str, new_password: str) -> None:
        """Validate reset token and update password."""
        from sqlalchemy import select

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
            )
        )
        reset_token = result.scalar_one_or_none()
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )
        await self.user_repo.update(
            str(reset_token.user_id),
            {"password_hash": hash_password(new_password)},
        )
        from sqlalchemy import update as sa_update
        await self.db.execute(
            sa_update(PasswordResetToken)
            .where(PasswordResetToken.id == reset_token.id)
            .values(used_at=datetime.now(timezone.utc))
        )
        await self.db.flush()

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        """Change password for an authenticated user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user or not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        await self.user_repo.update(user_id, {"password_hash": hash_password(new_password)})

    async def send_otp(self, phone: str, school_id: str | None) -> None:
        """Rate-limited OTP generation and dispatch via Celery."""
        from app.tasks.notifications import send_sms_otp

        if not self.redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OTP service unavailable while Redis is disabled",
            )

        rate_key = f"otp_rate:{phone}"
        if await self.redis.get(rate_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OTP already sent. Please wait 1 minute before requesting again.",
            )
        # Set rate limit
        await self.redis.setex(rate_key, 60, "1")
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        await self.redis.setex(f"otp:{phone}", 300, otp)
        send_sms_otp.delay(phone, otp)

    async def verify_otp(self, phone: str, otp: str, school_id: str | None) -> tuple:
        """Verify OTP and return login response."""
        if not self.redis:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OTP service unavailable while Redis is disabled",
            )

        stored_otp = await self.redis.get(f"otp:{phone}")
        if not stored_otp or not hmac.compare_digest(stored_otp, otp):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP",
            )
        # Delete OTP on success
        await self.redis.delete(f"otp:{phone}")

        # Find or create user by phone
        user = await self.user_repo.get_by_phone(school_id, phone)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with this phone number",
            )

        # Issue tokens
        access_token, access_jti = create_access_token(
            subject=str(user.id),
            school_id=str(user.school_id) if user.school_id else None,
            is_super_admin=user.is_super_admin,
        )
        refresh_token, refresh_jti = create_refresh_token(subject=str(user.id))
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.setex(f"refresh:jti:{refresh_jti}", ttl, str(user.id))
        await self.user_repo.update_last_login(str(user.id))

        permissions = await self.user_repo.get_user_permissions(str(user.id))
        user_response = UserResponse(
            id=user.id,
            school_id=user.school_id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_super_admin=user.is_super_admin,
            avatar_url=user.avatar_url,
            last_login=user.last_login,
            created_at=user.created_at,
            permissions=list(permissions),
        )
        login_response = LoginResponse(
            access_token=access_token,
            user=user_response,
        )
        return login_response, refresh_token, refresh_jti

