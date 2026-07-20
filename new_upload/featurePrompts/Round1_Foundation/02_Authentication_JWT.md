# Feature Prompt 02 — Authentication & JWT

## Round: 1 of 4 — Foundation
## Prerequisites: Prompt 01 (Infrastructure Setup) complete

---

## Objective

Implement the complete authentication system: login with username/email/password, OTP-based phone login (for parents), JWT access + refresh token rotation, token blacklist via Redis, forgot/reset password via email, and the `GET /auth/me` endpoint. All 9 endpoints must be tested and working.

---

## 1. Database Models (`backend/app/models/auth.py`)

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Constraints
    __table_args__ = (
        # email unique per school (super admin: school_id=NULL so use partial index)
        # Enforced via partial unique index in migration
    )

    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    device_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)  # login / password_reset
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

---

## 2. Alembic Migration

Add to migration:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    email VARCHAR(255),
    phone VARCHAR(20),
    username VARCHAR(100),
    password_hash TEXT,
    full_name VARCHAR(200) NOT NULL,
    avatar_url VARCHAR(500),
    fcm_token VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_super_admin BOOLEAN DEFAULT FALSE NOT NULL,
    last_login_at TIMESTAMPTZ,
    failed_login_count INTEGER DEFAULT 0 NOT NULL,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Unique email per school
CREATE UNIQUE INDEX uq_users_email_school ON users(school_id, email)
    WHERE email IS NOT NULL AND school_id IS NOT NULL;
-- Super admin: unique email globally when school_id is null
CREATE UNIQUE INDEX uq_users_email_superadmin ON users(email)
    WHERE school_id IS NULL AND email IS NOT NULL;

CREATE INDEX ix_users_school_id ON users(school_id);
CREATE INDEX ix_users_phone ON users(phone) WHERE phone IS NOT NULL;

CREATE TABLE refresh_tokens (...);
CREATE TABLE password_reset_tokens (...);
CREATE TABLE otp_records (...);
```

---

## 3. Pydantic Schemas (`backend/app/schemas/auth.py`)

```python
from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime

class LoginRequest(BaseModel):
    username: str  # accepts email OR username
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserProfile"
    school: "SchoolBasic | None"
    permissions: list[str]  # ["students:view", "fees:create", ...]

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class SendOTPRequest(BaseModel):
    phone: str
    purpose: str = "login"

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str
    purpose: str = "login"

class UserProfile(BaseModel):
    id: UUID
    email: str | None
    phone: str | None
    fullName: str
    avatarUrl: str | None
    isSuperAdmin: bool
    roles: list[str]
    isActive: bool

    model_config = {"from_attributes": True}

class SchoolBasic(BaseModel):
    id: UUID
    name: str
    slug: str
    logoUrl: str | None

    model_config = {"from_attributes": True}

class FCMTokenUpdate(BaseModel):
    token: str
```

---

## 4. Repository (`backend/app/repositories/user_repository.py`)

```python
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.auth import User, RefreshToken, PasswordResetToken, OTPRecord

async def get_user_by_email(db: AsyncSession, email: str, school_id: UUID | None = None) -> User | None:
    """Find user by email. For school users, scope to school_id."""
    ...

async def get_user_by_username(db: AsyncSession, username: str, school_id: UUID | None = None) -> User | None:
    ...

async def get_user_by_phone(db: AsyncSession, phone: str, school_id: UUID | None = None) -> User | None:
    ...

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    ...

async def create_refresh_token(db: AsyncSession, user_id: UUID, token_hash: str,
                                device_info: str | None, ip: str | None,
                                expires_at: datetime) -> RefreshToken:
    ...

async def get_refresh_token(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    ...

async def revoke_refresh_token(db: AsyncSession, token_hash: str) -> None:
    ...

async def create_password_reset_token(db: AsyncSession, user_id: UUID,
                                       token_hash: str, expires_at: datetime) -> PasswordResetToken:
    ...

async def get_password_reset_token(db: AsyncSession, token_hash: str) -> PasswordResetToken | None:
    ...

async def create_otp_record(db: AsyncSession, phone: str, otp_hash: str,
                             purpose: str, expires_at: datetime) -> OTPRecord:
    ...

async def get_latest_otp(db: AsyncSession, phone: str, purpose: str) -> OTPRecord | None:
    ...

async def update_user_last_login(db: AsyncSession, user_id: UUID) -> None:
    ...

async def increment_failed_login(db: AsyncSession, user_id: UUID) -> int:
    """Increment failed_login_count. Return new count."""
    ...

async def reset_failed_login(db: AsyncSession, user_id: UUID) -> None:
    ...

async def lock_user_account(db: AsyncSession, user_id: UUID, until: datetime) -> None:
    ...

async def get_user_permissions(db: AsyncSession, user_id: UUID) -> list[str]:
    """Return list of 'module:action' strings for the user via their roles."""
    ...
```

---

## 5. Service (`backend/app/services/auth_service.py`)

Implement all business logic:

```python
import hashlib, secrets, random, string
from datetime import datetime, timedelta, timezone
from uuid import UUID
import redis.asyncio as aioredis
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.security import verify_password, hash_password, create_access_token, decode_token
from app.repositories import user_repository
from app.tasks.notifications import send_otp_sms_task, send_password_reset_email_task

MAX_FAILED_LOGINS = 5
ACCOUNT_LOCKOUT_MINUTES = 30
OTP_EXPIRY_MINUTES = 10
OTP_RATE_LIMIT_SECONDS = 60

async def login(db, redis_client, username: str, password: str, ip: str, device_info: str):
    """
    1. Find user by email OR username (try email first, then username).
    2. Raise 401 if not found.
    3. Check account lockout (locked_until).
    4. Verify password — on failure: increment failed_login_count; if >=5: lock for 30min.
    5. Reset failed_login_count on success.
    6. Build JWT payload including permissions list.
    7. Store JTI in Redis: SET jti:{jti} "valid" EX {ACCESS_TOKEN_EXPIRE_MINUTES*60}.
    8. Create refresh token: hash(secrets.token_hex(32)), store in DB.
    9. Update last_login_at.
    10. Return LoginResponse.
    """
    ...

async def refresh_token(db, redis_client, refresh_token_value: str, ip: str):
    """
    1. Hash the incoming refresh token, find in DB.
    2. Check is_revoked=False and expires_at > now.
    3. Check user still active.
    4. Issue new access token with fresh JTI.
    5. Optionally rotate: revoke old refresh token, create new one.
    6. Return RefreshResponse.
    """
    ...

async def logout(db, redis_client, user_id: UUID, jti: str, refresh_token_value: str | None):
    """
    1. Add JTI to Redis blacklist.
    2. Revoke refresh token in DB if provided.
    """
    ...

async def forgot_password(db, email: str):
    """
    1. Find user by email (don't reveal if not found — return success either way).
    2. Generate URL-safe token = secrets.token_urlsafe(32).
    3. Hash token with SHA-256, store in password_reset_tokens with 1-hour expiry.
    4. Enqueue Celery task: send_password_reset_email_task(email, token, user.full_name).
    """
    ...

async def reset_password(db, token: str, new_password: str):
    """
    1. Hash the incoming token, find in DB.
    2. Check not used and not expired.
    3. Update user password_hash.
    4. Mark token as used (used_at = now).
    5. Revoke all existing refresh tokens for this user.
    """
    ...

async def change_password(db, user_id: UUID, current_password: str, new_password: str):
    """Verify current password, then update hash."""
    ...

async def send_otp(db, redis_client, phone: str, purpose: str):
    """
    1. Rate limit: check Redis key otp_rate:{phone}:{purpose}. If exists: raise 429.
    2. Generate 6-digit OTP.
    3. Hash OTP.
    4. Store OTPRecord in DB (expires in 10 minutes).
    5. Set Redis rate limit key with TTL=60s.
    6. Enqueue SMS task.
    """
    ...

async def verify_otp(db, redis_client, phone: str, otp: str, purpose: str, ip: str, device_info: str):
    """
    1. Find latest unused OTP for (phone, purpose).
    2. Increment attempts. If >3: raise 429.
    3. Verify OTP hash.
    4. Check not expired.
    5. Mark OTP as used.
    6. Find or create user by phone.
    7. On purpose=login: call login flow (skip password step), return LoginResponse.
    """
    ...
```

---

## 6. API Endpoints (`backend/app/api/v1/endpoints/auth.py`)

All routes under prefix `/auth`:

```python
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import *
from app.services import auth_service
from app.utils.response import ok
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with username/email + password. Returns access token + sets httpOnly refresh cookie."""
    result = await auth_service.login(
        db, request.app.state.redis, data.username, data.password,
        ip=request.client.host, device_info=request.headers.get("User-Agent", "")
    )
    response = JSONResponse(content=ok(result))
    response.set_cookie(
        key="refresh_token", value=result["refresh_token"],
        httponly=True, secure=True, samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    return response

@router.post("/refresh")
async def refresh(request: Request, db: AsyncSession = Depends(get_db)):
    """Rotate refresh token. Reads httpOnly cookie."""
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(status_code=401, detail="No refresh token")
    result = await auth_service.refresh_token(
        db, request.app.state.redis, refresh_token_value,
        ip=request.client.host
    )
    response = JSONResponse(content=ok(result))
    response.set_cookie("refresh_token", result.get("new_refresh_token", refresh_token_value),
                        httponly=True, secure=True, samesite="strict",
                        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return response

@router.post("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db),
                 current_user=Depends(get_current_user)):
    refresh_token_value = request.cookies.get("refresh_token")
    await auth_service.logout(db, request.app.state.redis,
                               current_user.id, current_user.jti, refresh_token_value)
    response = JSONResponse(content=ok(message="Logged out"))
    response.delete_cookie("refresh_token")
    return response

@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db=Depends(get_db)):
    await auth_service.forgot_password(db, data.email)
    return ok(message="If the email exists, a reset link has been sent")

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db=Depends(get_db)):
    await auth_service.reset_password(db, data.token, data.new_password)
    return ok(message="Password has been reset")

@router.post("/change-password")
async def change_password(data: ChangePasswordRequest, db=Depends(get_db),
                          current_user=Depends(get_current_user)):
    await auth_service.change_password(db, current_user.id, data.current_password, data.new_password)
    return ok(message="Password changed")

@router.post("/send-otp")
@limiter.limit("1/minute")
async def send_otp(request: Request, data: SendOTPRequest, db=Depends(get_db)):
    await auth_service.send_otp(db, request.app.state.redis, data.phone, data.purpose)
    return ok(message="OTP sent")

@router.post("/verify-otp")
@limiter.limit("5/minute")
async def verify_otp(request: Request, data: VerifyOTPRequest, response: Response, db=Depends(get_db)):
    result = await auth_service.verify_otp(
        db, request.app.state.redis, data.phone, data.otp, data.purpose,
        ip=request.client.host, device_info=request.headers.get("User-Agent", "")
    )
    resp = JSONResponse(content=ok(result))
    resp.set_cookie("refresh_token", result["refresh_token"],
                    httponly=True, secure=True, samesite="strict",
                    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return resp

@router.get("/me")
async def get_me(db=Depends(get_db), current_user=Depends(get_current_user)):
    """Return current user profile + permissions + school info."""
    # Reload full user + permissions from DB (not just JWT claims)
    permissions = await user_repository.get_user_permissions(db, current_user.id)
    return ok({"user": UserProfile.model_validate(current_user),
               "permissions": permissions})

@router.post("/fcm-token")
async def update_fcm_token(data: FCMTokenUpdate, db=Depends(get_db),
                           current_user=Depends(get_current_user)):
    current_user.fcm_token = data.token
    await db.commit()
    return ok(message="FCM token updated")
```

---

## 7. `backend/app/core/dependencies.py`

```python
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import decode_token
from app.models.auth import User
from app.repositories.user_repository import get_user_by_id, get_user_permissions

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")
    jti = payload.get("jti")
    school_id = payload.get("school_id")

    # Check JTI blacklist in Redis
    redis_client = request.app.state.redis
    blacklisted = await redis_client.get(f"jti_blacklist:{jti}")
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Attach extra info to user object for downstream usage
    user.jti = jti
    user.school_id = school_id  # from JWT claim
    request.state.school_id = school_id
    return user


def permission_required(module: str, action: str):
    """FastAPI dependency factory. Use as: Depends(permission_required('students','create'))"""
    async def _check(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        if current_user.is_super_admin:
            return current_user
        permissions = await get_user_permissions(db, current_user.id)
        if f"{module}:{action}" not in permissions:
            raise HTTPException(status_code=403,
                detail=f"Permission denied: {module}:{action}")
        return current_user
    return _check
```

---

## 8. Celery Tasks (`backend/app/tasks/emails.py`)

```python
from app.tasks.celery_app import celery_app

@celery_app.task(queue="emails", max_retries=3, default_retry_delay=60)
def send_password_reset_email_task(to_email: str, reset_token: str, user_name: str):
    """Send password reset email with link containing token."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "Password Reset Request"
    body = f"Hi {user_name},\n\nClick this link to reset your password: {reset_url}\n\nExpires in 1 hour."
    # Use SMTP or SendGrid
    _send_email(to_email, subject, body)
```

```python
# backend/app/tasks/notifications.py
@celery_app.task(queue="notifications", max_retries=3, default_retry_delay=60)
def send_otp_sms_task(phone: str, otp: str):
    """Send OTP via MSG91 or Twilio."""
    # MSG91: POST https://api.msg91.com/api/v5.1/flow/
    # Fallback: Twilio client.messages.create(...)
    ...
```

---

## 9. Frontend: Login Page (`frontend/src/pages/auth/LoginPage.tsx`)

Build a login form with:
- Email/username field
- Password field with show/hide toggle
- "Forgot password?" link
- Submit button
- Zod schema validation (email or min 3-char username, password min 8 chars)
- `useLogin` TanStack Query mutation
- On success: store tokens via `useAuthStore.setUser()`, navigate based on role:
  - `is_super_admin` → `/superadmin`
  - roles includes `school_admin` OR `principal` → `/dashboard`
  - roles includes `teacher` OR `class_teacher` → `/dashboard`
  - roles includes `parent` → `/parent`
  - roles includes `student` → `/student`
  - default → `/dashboard`
- Show error toast on failed login
- Show "Account locked" message if 423 response

---

## 10. Frontend: API Layer (`frontend/src/api/auth.ts`)

```typescript
import api from './axios';
import type { LoginRequest, LoginResponse, UserProfile } from '@/types';

export const loginApi = async (data: LoginRequest) => {
  const res = await api.post<{ success: boolean; data: LoginResponse }>('/auth/login', data);
  return res.data.data;
};

export const logoutApi = async () => api.post('/auth/logout');

export const refreshTokenApi = async () => {
  const res = await api.post<{ data: { access_token: string } }>('/auth/refresh');
  return res.data.data;
};

export const getMeApi = async () => {
  const res = await api.get<{ data: { user: UserProfile; permissions: string[] } }>('/auth/me');
  return res.data.data;
};

export const forgotPasswordApi = async (email: string) =>
  api.post('/auth/forgot-password', { email });

export const resetPasswordApi = async (token: string, newPassword: string) =>
  api.post('/auth/reset-password', { token, new_password: newPassword });

export const changePasswordApi = async (currentPassword: string, newPassword: string) =>
  api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword });

export const sendOtpApi = async (phone: string) =>
  api.post('/auth/send-otp', { phone });

export const verifyOtpApi = async (phone: string, otp: string) =>
  api.post('/auth/verify-otp', { phone, otp });

export const updateFCMTokenApi = async (token: string) =>
  api.post('/auth/fcm-token', { token });
```

---

## 11. Frontend: Custom Hooks (`frontend/src/hooks/useAuth.ts`)

```typescript
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useAuthStore } from '@store/authStore';
import { loginApi, logoutApi } from '@api/auth';

export const useLogin = () => {
  const navigate = useNavigate();
  const { setUser, setAccessToken } = useAuthStore();

  return useMutation({
    mutationFn: loginApi,
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      setUser(data.user, data.school, data.permissions);
      toast.success('Welcome back!');
      // Role-based redirect
      if (data.user.isSuperAdmin) navigate('/superadmin');
      else navigate('/dashboard');
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.message || 'Login failed';
      toast.error(msg);
    },
  });
};

export const useLogout = () => {
  const { logout } = useAuthStore();
  const navigate = useNavigate();
  return useMutation({
    mutationFn: logoutApi,
    onSettled: () => {
      logout();
      navigate('/login');
    },
  });
};
```

---

## 12. Frontend: Forgot & Reset Password Pages

Create `ForgotPasswordPage.tsx`:
- Single email input with Zod validation
- Submit → `forgotPasswordApi` → show success message: "Check your email for a reset link"

Create `ResetPasswordPage.tsx`:
- Read `token` from URL query param
- New password + confirm password fields
- Validate match + min 8 chars
- Submit → `resetPasswordApi(token, newPassword)`
- On success: redirect to `/login` with success toast

---

## 13. Add Routes to `frontend/src/routes/index.tsx`

```typescript
// Public routes (no auth required)
/login         → LoginPage
/forgot-password → ForgotPasswordPage
/reset-password  → ResetPasswordPage

// All other routes → wrapped in <PrivateRoute>
```

---

## 14. Register Auth Router in Backend

In `backend/app/api/v1/router.py`:
```python
from app.api.v1.endpoints import auth
api_router.include_router(auth.router)
```

---

## Verification Checklist

- [ ] `POST /api/v1/auth/login` with valid credentials returns `access_token` + sets `refresh_token` httpOnly cookie
- [ ] `POST /api/v1/auth/login` with wrong password returns 401; after 5 failures returns 423 (locked)
- [ ] `POST /api/v1/auth/refresh` with valid cookie returns new `access_token`
- [ ] `POST /api/v1/auth/logout` blacklists JTI in Redis
- [ ] `GET /api/v1/auth/me` with valid token returns user profile
- [ ] `POST /api/v1/auth/forgot-password` enqueues email task (check Flower)
- [ ] `POST /api/v1/auth/send-otp` is rate-limited to 1/min per phone
- [ ] Login with invalid token returns 401
- [ ] Blacklisted token returns 401 on next request
- [ ] Frontend login form → successful login → redirect to `/dashboard`
- [ ] `useAuthStore` persists to `localStorage` and survives page refresh
