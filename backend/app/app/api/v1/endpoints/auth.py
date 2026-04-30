from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.dependencies import get_current_user, redis_client
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    ResetPasswordRequest,
    SendOtpRequest,
    TokenResponse,
    UserResponse,
    VerifyOtpRequest,
)
from app.services.auth_service import AuthService
from app.utils.response import ok

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth/refresh",
    )


@router.post("/login", response_model=dict)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Login with email/username/phone + password."""
    school_id = getattr(request.state, "school_id", None)
    service = AuthService(db, redis_client)
    login_identifier = data.identifier or data.username
    login_resp, refresh_token, _ = await service.login(login_identifier, data.password, school_id)
    _set_refresh_cookie(response, refresh_token)
    return ok(login_resp.model_dump(), "Login successful")


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Issue new access token using refresh cookie."""
    refresh_token_str = request.cookies.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    service = AuthService(db, redis_client)
    access_token, _ = await service.refresh_token(refresh_token_str)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return ok(
        TokenResponse(access_token=access_token, expires_in=expires_in).model_dump(),
        "Token refreshed",
    )


@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Logout — blacklists tokens and clears refresh cookie."""
    from app.core.security import decode_token

    refresh_token_str = request.cookies.get("refresh_token", "")
    # Get the access token JTI from the request
    auth_header = request.headers.get("Authorization", "")
    access_jti = ""
    if auth_header.startswith("Bearer "):
        try:
            payload = decode_token(auth_header[7:])
            access_jti = payload.get("jti", "")
        except Exception:
            pass

    service = AuthService(db, redis_client)
    await service.logout(refresh_token_str, access_jti)
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
    return ok(None, "Logged out successfully")


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Send password reset email (always returns success to prevent enumeration)."""
    school_id = getattr(request.state, "school_id", None)
    service = AuthService(db, redis_client)
    await service.forgot_password(data.email, school_id)
    return ok(None, "If that email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=dict)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using the emailed token."""
    service = AuthService(db, redis_client)
    await service.reset_password(data.token, data.new_password)
    return ok(None, "Password reset successfully")


@router.post("/change-password", response_model=dict)
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Change password for authenticated user."""
    service = AuthService(db, redis_client)
    await service.change_password(str(current_user.id), data.current_password, data.new_password)
    return ok(None, "Password changed successfully")


@router.post("/send-otp", response_model=dict)
async def send_otp(
    data: SendOtpRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Send OTP to phone (rate-limited: 1/min per phone)."""
    school_id = getattr(request.state, "school_id", None)
    service = AuthService(db, redis_client)
    await service.send_otp(data.phone, school_id)
    return ok(None, "OTP sent successfully")


@router.post("/verify-otp", response_model=dict)
async def verify_otp(
    data: VerifyOtpRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP and return login response."""
    school_id = getattr(request.state, "school_id", None)
    service = AuthService(db, redis_client)
    login_resp, refresh_token, _ = await service.verify_otp(data.phone, data.otp, school_id)
    _set_refresh_cookie(response, refresh_token)
    return ok(login_resp.model_dump(), "OTP verified successfully")


@router.get("/me", response_model=dict)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get current authenticated user profile."""
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(db)
    permissions = await repo.get_user_permissions(str(current_user.id))
    user_resp = UserResponse(
        id=current_user.id,
        school_id=current_user.school_id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_super_admin=current_user.is_super_admin,
        avatar_url=current_user.avatar_url,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        permissions=list(permissions),
    )
    return ok(user_resp.model_dump(), "User profile")

