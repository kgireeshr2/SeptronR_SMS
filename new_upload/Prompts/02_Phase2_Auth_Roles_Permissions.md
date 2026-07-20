# PHASE 2 — AUTHENTICATION, ROLES & PERMISSIONS

## Pre-Requisite
Phase 1 complete. FastAPI app running, DB tables exist (users, roles, permissions, role_permissions, user_roles, password_reset_tokens), Alembic applied.

## Objective
Full authentication system (JWT + OTP + refresh + logout) and a complete RBAC system with a permission matrix UI.

---

## 2.1 Database Tables (Already in Schema — Verify Exist)

```sql
-- Section 3: Auth
users (
    id UUID PK, school_id UUID FK→schools (NULL for super admin),
    username VARCHAR(100), email VARCHAR(200), phone VARCHAR(20),
    password_hash TEXT, otp_secret VARCHAR(64),
    is_active BOOL DEFAULT TRUE, is_verified BOOL DEFAULT FALSE,
    avatar_url TEXT, last_login TIMESTAMPTZ,
    is_super_admin BOOL DEFAULT FALSE,
    created_at, updated_at, deleted_at, deleted_by UUID FK→users,
    UNIQUE(school_id, email), UNIQUE(school_id, username),
    CHECK(email IS NOT NULL OR phone IS NOT NULL)
)

password_reset_tokens (
    id UUID PK, user_id UUID FK→users,
    token_hash TEXT UNIQUE, expires_at TIMESTAMPTZ,
    used_at TIMESTAMPTZ, created_at
)

-- Section 4: RBAC
roles (
    id UUID PK, school_id UUID FK→schools (NULL = platform role),
    name VARCHAR(100), slug VARCHAR(100),
    description TEXT, is_system BOOL DEFAULT FALSE,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(school_id, slug)
)

permissions (
    id UUID PK, module VARCHAR(60), action VARCHAR(30),
    description TEXT,
    UNIQUE(module, action)
)

role_permissions (
    role_id UUID FK→roles, permission_id UUID FK→permissions,
    PRIMARY KEY(role_id, permission_id)
)

user_roles (
    user_id UUID FK→users, role_id UUID FK→roles,
    assigned_by UUID FK→users, assigned_at TIMESTAMPTZ,
    PRIMARY KEY(user_id, role_id)
)
```

---

## 2.2 SQLAlchemy Models

### `backend/app/models/auth.py`
Define ORM models for: `User`, `PasswordResetToken`

Key model details:
- `User.password_hash` — never return in any schema
- `User.otp_secret` — never return in any schema
- `User.school_id` — nullable (NULL = super admin)
- `User.deleted_at` — soft delete timestamp
- Relationship: `User.roles` via `user_roles` association table

### `backend/app/models/rbac.py`
Define ORM models for: `Role`, `Permission`, `RolePermission`, `UserRole`

---

## 2.3 Pydantic Schemas

### `backend/app/schemas/auth.py`
```python
# Requests
class LoginRequest(BaseModel):
    username: str           # accepts email OR username OR phone
    password: str

class RefreshRequest(BaseModel):
    pass                    # refresh token read from httpOnly cookie

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

class SendOtpRequest(BaseModel):
    phone: str

class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str = Field(min_length=6, max_length=6)

# Responses
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int         # seconds

class UserResponse(BaseModel):
    id: UUID
    school_id: Optional[UUID]
    username: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_active: bool
    is_verified: bool
    is_super_admin: bool
    avatar_url: Optional[str]
    last_login: Optional[datetime]
    created_at: datetime
    permissions: List[str]  # ["students:view", "fees:create", ...]

    model_config = ConfigDict(from_attributes=True)

class LoginResponse(BaseModel):
    access_token: str
    user: UserResponse
    school: Optional[SchoolBasicResponse]
```

### `backend/app/schemas/rbac.py`
```python
class RoleCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str]

class RoleUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    is_active: Optional[bool]

class RoleResponse(BaseModel):
    id: UUID
    school_id: Optional[UUID]
    name: str
    slug: str
    description: Optional[str]
    is_system: bool
    is_active: bool
    permissions: List[str]  # ["students:view", ...]
    model_config = ConfigDict(from_attributes=True)

class PermissionResponse(BaseModel):
    id: UUID
    module: str
    action: str
    description: Optional[str]

class AssignPermissionsRequest(BaseModel):
    permission_ids: List[UUID]

class AssignRolesRequest(BaseModel):
    role_ids: List[UUID]
```

---

## 2.4 Security Utilities (`backend/app/core/security.py`)

```python
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, school_id: Optional[str] = None,
                        is_super_admin: bool = False) -> tuple[str, str]:
    """Returns (token, jti)."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,         # user_id
        "school_id": school_id,
        "is_super_admin": is_super_admin,
        "jti": jti,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti


def create_refresh_token(subject: str) -> tuple[str, str]:
    """Returns (token, jti)."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "jti": jti,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
```

---

## 2.5 Dependencies (`backend/app/core/dependencies.py`)

```python
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from app.db.session import get_db
from app.core.security import decode_token
from app.core.config import settings
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Decode JWT, check blacklist, load user with permissions."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        if not user_id or not jti:
            raise credentials_exception
        # Check blacklist
        if await redis_client.get(f"blacklist:jti:{jti}"):
            raise credentials_exception
    except Exception:
        raise credentials_exception

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise credentials_exception

    # Set school context
    request.state.school_id = str(user.school_id) if user.school_id else None
    request.state.current_user = user
    return user


def permission_required(module: str, action: str):
    """FastAPI dependency factory for permission checking."""
    async def _check(
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        if current_user.is_super_admin:
            return current_user
        repo = UserRepository(db)
        permissions = await repo.get_user_permissions(current_user.id)
        perm_key = f"{module}:{action}"
        if perm_key not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {perm_key}",
            )
        return current_user
    return _check
```

---

## 2.6 Repository Layer

### `backend/app/repositories/user_repository.py`
```python
class UserRepository:
    def __init__(self, db: AsyncSession): self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]: ...
    async def get_by_email(self, school_id: str, email: str) -> Optional[User]: ...
    async def get_by_username(self, school_id: str, username: str) -> Optional[User]: ...
    async def get_by_phone(self, school_id: str, phone: str) -> Optional[User]: ...
    async def create(self, data: dict) -> User: ...
    async def update(self, user_id: str, data: dict) -> User: ...
    async def get_user_permissions(self, user_id: str) -> set[str]:
        """Returns set of 'module:action' strings via JOIN user_roles → role_permissions → permissions."""
    async def update_last_login(self, user_id: str) -> None: ...
    async def list_by_school(self, school_id: str, page: int, page_size: int, filters: dict): ...
```

### `backend/app/repositories/role_repository.py`
```python
class RoleRepository:
    async def list_by_school(self, school_id: str) -> List[Role]: ...
    async def get_by_id(self, role_id: str) -> Optional[Role]: ...
    async def create(self, school_id: str, data: dict) -> Role: ...
    async def update(self, role_id: str, data: dict) -> Role: ...
    async def delete(self, role_id: str) -> None: ...
    async def assign_permissions(self, role_id: str, permission_ids: List[str]) -> None: ...
    async def get_permissions(self, role_id: str) -> List[Permission]: ...
    async def clone_role(self, role_id: str, new_name: str, school_id: str) -> Role: ...
```

---

## 2.7 Service Layer

### `backend/app/services/auth_service.py`
```python
class AuthService:

    async def login(self, identifier: str, password: str, school_id: str) -> LoginResponse:
        """
        1. Find user by email OR username OR phone within school
        2. Check is_active
        3. Verify bcrypt password
        4. Generate access_token + refresh_token
        5. Store refresh_token JTI in Redis with TTL
        6. Update last_login
        7. Load permissions
        8. Return LoginResponse
        """

    async def refresh_token(self, refresh_token_str: str) -> TokenResponse:
        """
        1. Decode refresh token
        2. Check not blacklisted in Redis
        3. Re-issue new access token
        """

    async def logout(self, refresh_token_str: str, access_jti: str) -> None:
        """
        1. Decode refresh token → get JTI
        2. Blacklist refresh JTI in Redis (TTL = remaining expiry)
        3. Blacklist access JTI in Redis
        """

    async def forgot_password(self, email: str, school_id: str) -> None:
        """
        1. Find user by email
        2. Generate secure token (secrets.token_urlsafe(32))
        3. Hash it (sha256) and store in password_reset_tokens with expires_at = now + 1 hour
        4. Enqueue Celery task: send_reset_email(user.email, token)
        """

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        1. Hash token → lookup in password_reset_tokens
        2. Check not expired, not used
        3. Update user.password_hash
        4. Mark token.used_at = now
        """

    async def send_otp(self, phone: str, school_id: str) -> None:
        """
        1. Rate limit: check Redis key 'otp_rate:{phone}' — if exists → raise 429
        2. Set rate limit key TTL 60s
        3. Generate 6-digit OTP
        4. Store in Redis 'otp:{phone}' with TTL 300s (5 min)
        5. Enqueue Celery SMS task: send_sms(phone, otp)
        """

    async def verify_otp(self, phone: str, otp: str, school_id: str) -> LoginResponse:
        """
        1. Get OTP from Redis 'otp:{phone}'
        2. Compare (constant-time)
        3. Delete OTP from Redis on success
        4. Find/create user by phone
        5. Return tokens + user
        """
```

---

## 2.8 API Route Handlers

### `backend/app/api/v1/endpoints/auth.py`

```
POST /api/v1/auth/login           → 200 LoginResponse (sets refresh httpOnly cookie)
POST /api/v1/auth/refresh         → 200 TokenResponse (reads refresh from cookie)
POST /api/v1/auth/logout          → 200 (clears cookie)
POST /api/v1/auth/forgot-password → 200 (no data; always returns success to prevent enumeration)
POST /api/v1/auth/reset-password  → 200
POST /api/v1/auth/change-password → 200 [auth required]
POST /api/v1/auth/send-otp        → 200 (rate limited: slowapi 1/min per phone)
POST /api/v1/auth/verify-otp      → 200 LoginResponse
GET  /api/v1/auth/me              → 200 UserResponse [auth required]
```

**Cookie handling for refresh token:**
```python
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=settings.APP_ENV == "production",
    samesite="strict",
    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    path="/api/v1/auth/refresh",
)
```

### `backend/app/api/v1/endpoints/roles.py`

```
GET    /api/v1/roles                         → list all roles for school
POST   /api/v1/roles                         → create role
GET    /api/v1/roles/{id}                    → get role with permissions
PUT    /api/v1/roles/{id}                    → update role
DELETE /api/v1/roles/{id}                    → delete (block if is_system=True)
GET    /api/v1/roles/{id}/permissions        → list permissions assigned to role
POST   /api/v1/roles/{id}/permissions        → replace permission set
POST   /api/v1/roles/{id}/clone             → clone role with new name
GET    /api/v1/permissions                   → full permission registry
```

All endpoints: `permission_required("roles", "view"|"create"|"update"|"delete"|"manage")`

---

## 2.9 Celery Tasks

### `backend/app/tasks/emails.py`
```python
@celery.task(name="tasks.send_password_reset_email", queue="emails")
def send_password_reset_email(email: str, token: str, school_name: str):
    """Send password reset email via SMTP."""
    # Use Jinja2 template: templates/email/reset_password.html
    # Subject: "Reset your password — {school_name}"
    # Link: {FRONTEND_URL}/reset-password?token={token}
```

### `backend/app/tasks/notifications.py` (stub for OTP)
```python
@celery.task(name="tasks.send_sms_otp", queue="notifications")
def send_sms_otp(phone: str, otp: str):
    """Send OTP via SMS provider (MSG91 or Twilio)."""
```

---

## 2.10 Frontend — Auth Pages

### `frontend/src/pages/auth/LoginPage.tsx`
- React Hook Form + Zod schema:
  ```typescript
  const schema = z.object({
    username: z.string().min(1, "Required"),
    password: z.string().min(1, "Required"),
  });
  ```
- Show/hide password toggle
- Loading state on submit button
- On success: set Zustand store → navigate based on primary role:
  - `super_admin` → `/super-admin/dashboard`
  - `school_admin`/`principal`/`vice_principal` → `/dashboard`
  - `teacher`/`class_teacher` → `/teacher/dashboard`
  - `student` → `/student/portal`
  - `parent` → `/parent/portal`
- On error: show toast with server message
- "Forgot password?" link

### `frontend/src/pages/auth/ForgotPasswordPage.tsx`
- Email input → submit → show success message (always, to prevent enumeration)

### `frontend/src/pages/auth/ResetPasswordPage.tsx`
- Read `?token=` from URL
- New password + confirm password fields
- Zod: passwords must match, min 8 chars

### `frontend/src/api/auth.ts`
```typescript
export const authApi = {
  login: (data: LoginRequest) => api.post<LoginResponse>('/auth/login', data),
  refresh: () => api.post<TokenResponse>('/auth/refresh'),
  logout: () => api.post('/auth/logout'),
  forgotPassword: (email: string) => api.post('/auth/forgot-password', { email }),
  resetPassword: (data: ResetPasswordRequest) => api.post('/auth/reset-password', data),
  changePassword: (data: ChangePasswordRequest) => api.post('/auth/change-password', data),
  sendOtp: (phone: string) => api.post('/auth/send-otp', { phone }),
  verifyOtp: (data: VerifyOtpRequest) => api.post<LoginResponse>('/auth/verify-otp', data),
  me: () => api.get<UserResponse>('/auth/me'),
};
```

---

## 2.11 Frontend — Role/Permission Manager Page

### Route: `/admin/roles`
Permission required: `roles:view`

### `frontend/src/pages/admin/RolesPage.tsx`
- Table of roles: columns = Name, Slug, Type (System/Custom), Status, Permissions Count, Actions
- Actions: Edit (open modal), Clone, Delete (disabled for system roles)
- "Create Role" button (opens create dialog)

### Permission Matrix Component (`PermissionMatrix.tsx`)
```
         | view | create | update | delete | export | approve | manage
---------|------|--------|--------|--------|--------|---------|-------
students |  ✓   |   ✓    |   ✓    |        |   ✓    |         |
fees     |  ✓   |        |        |        |   ✓    |   ✓     |
exams    |  ✓   |        |        |        |        |   ✓     |
...
```
- Each cell: `<Checkbox>` bound to React state
- Row header: "Select All" toggle for entire module
- Column header: "Select All" toggle for entire action
- "Save Changes" → `POST /roles/{id}/permissions` with full array of permission IDs
- Optimistic updates via TanStack Query `useMutation`

### Role Assignment (User Edit Modal — built in Phase 5/6)
- Multi-select of available roles for the school
- Shows current roles with remove option
- `POST /users/{id}/roles`

### `frontend/src/api/roles.ts`
```typescript
export const rolesApi = {
  list: () => api.get<RoleResponse[]>('/roles'),
  get: (id: string) => api.get<RoleResponse>(`/roles/${id}`),
  create: (data: RoleCreate) => api.post<RoleResponse>('/roles', data),
  update: (id: string, data: RoleUpdate) => api.put<RoleResponse>(`/roles/${id}`, data),
  delete: (id: string) => api.delete(`/roles/${id}`),
  getPermissions: (id: string) => api.get<PermissionResponse[]>(`/roles/${id}/permissions`),
  assignPermissions: (id: string, permissionIds: string[]) =>
    api.post(`/roles/${id}/permissions`, { permissionIds }),
  clone: (id: string, name: string) => api.post<RoleResponse>(`/roles/${id}/clone`, { name }),
  allPermissions: () => api.get<PermissionResponse[]>('/permissions'),
};
```

---

## 2.12 School Onboarding Service

### `backend/app/services/school_service.py`
When creating a new school, automatically:
```python
async def seed_school_defaults(school_id: str, db: AsyncSession):
    """
    Called after school creation. Creates:
    1. System roles (school_admin, principal, vice_principal, teacher,
       class_teacher, accountant, librarian, transport_manager,
       inventory_manager, receptionist, parent, student) with correct permissions
    2. Default leave types (Casual 12d, Sick 12d, Earned 15d,
       Maternity 180d, Paternity 15d, Unpaid unlimited)
    3. Default school settings (all keys from Section 24.5 of schema)
    4. Default grading scale (CBSE 10-point from Section 24.8)
    5. Default fee categories, income categories, expense categories
    6. Default notification templates (all 15 from Section 24.6)
    """
```

---

## 2.13 Security Rules

- Passwords: bcrypt with cost factor 12
- Password minimum 8 chars (enforced in Pydantic schema)
- OTP: 6-digit numeric, 5-minute TTL, rate-limited 1/minute per phone
- JWT blacklist stored in Redis: key `blacklist:jti:{jti}`, TTL = remaining token lifetime
- Refresh token: httpOnly cookie, SameSite=Strict, Secure in production
- Login failed attempts: track in Redis `login_fail:{school_id}:{identifier}` — after 5 failures, lock for 15 min
- Password reset tokens: sha256-hashed before storage, 1-hour expiry, single-use

---

## 2.14 Tests

```python
# backend/tests/test_auth.py

async def test_login_success(): ...
async def test_login_wrong_password(): ...       # → 401
async def test_login_inactive_user(): ...        # → 401
async def test_refresh_token(): ...
async def test_logout_blacklists_token(): ...
async def test_access_with_blacklisted_token(): ... # → 401
async def test_forgot_password_sends_email(): ...
async def test_reset_password(): ...
async def test_send_otp_rate_limit(): ...        # second call within 1 min → 429
async def test_verify_otp_success(): ...
async def test_permission_required_blocks(): ... # → 403 without permission
async def test_permission_required_allows(): ... # passes with correct role
```

---

## 2.15 Deliverables Checklist

- [ ] All 9 auth endpoints working with correct HTTP status codes
- [ ] JWT access + refresh token issued on login
- [ ] Refresh token stored in httpOnly cookie
- [ ] Token blacklist working in Redis (logout invalidates tokens)
- [ ] OTP flow: rate-limited 1/min → stores in Redis → Celery SMS task queued
- [ ] Password reset: email sent via Celery → token hashed in DB → reset works
- [ ] `permission_required` dependency blocks unauthorized access (403)
- [ ] Role CRUD API working
- [ ] Permission matrix API: get and replace permissions for a role
- [ ] School onboarding seeds all 12 system roles with correct permissions
- [ ] Login page: form validation, show/hide password, role-based redirect
- [ ] Forgot password and reset password flows working end-to-end
- [ ] Permission matrix UI: checkboxes, toggle all row/column, save
- [ ] `usePermission()` hook and `<PermissionGuard>` working
- [ ] Test coverage: all auth scenarios covered
