# Feature Prompt 29 — Super Admin Portal

## Round: 4 of 4 — Advanced Features
## Prerequisites: Prompts 01–04 complete

---

## Objective

Implement a super-admin portal for platform management: school management, impersonation/login-as, subscription/feature flags, platform analytics, and global audit logs.

---

## 1. Database Models (`backend/app/models/super_admin.py`)

```python
import uuid
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class FeatureFlag(Base, TimestampMixin):
    __tablename__ = "feature_flags"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flag_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_globally_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    school_overrides: Mapped[dict] = mapped_column(JSONB, default={})
    # school_overrides: { "school_id_str": true/false }

class SchoolSubscription(Base, TimestampMixin):
    __tablename__ = "school_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")  # free/basic/premium/enterprise
    max_students: Mapped[int] = mapped_column(Integer, default=500)
    max_staff: Mapped[int] = mapped_column(Integer, default=50)
    valid_until: Mapped[str | None] = mapped_column(nullable=True)  # TIMESTAMPTZ
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

class ImpersonationLog(Base, TimestampMixin):
    __tablename__ = "impersonation_logs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    super_admin_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    target_user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True], nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ended_at: Mapped[str | None] = mapped_column(nullable=True)  # TIMESTAMPTZ
```

---

## 2. Alembic Migration

```sql
CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_key VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_globally_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    school_overrides JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

INSERT INTO feature_flags (flag_key, description) VALUES
('parent_portal', 'Parent Portal PWA access'),
('online_payment', 'Razorpay online payment'),
('whatsapp_notifications', 'WhatsApp via Meta API'),
('biometric_attendance', 'Biometric import for attendance');

CREATE TABLE school_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL UNIQUE REFERENCES schools(id) ON DELETE CASCADE,
    plan VARCHAR(50) DEFAULT 'free' NOT NULL,
    max_students INTEGER DEFAULT 500 NOT NULL,
    max_staff INTEGER DEFAULT 50 NOT NULL,
    valid_until TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE impersonation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    super_admin_id UUID NOT NULL,
    target_user_id UUID NOT NULL,
    school_id UUID NOT NULL,
    reason TEXT,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

---

## 3. Feature Flag Check

```python
# backend/app/utils/feature_flags.py
async def is_feature_enabled(redis, db, school_id: UUID, flag_key: str) -> bool:
    """
    Check feature flag for school:
    1. Check Redis cache: `ff:{school_id}:{flag_key}` (TTL 5min).
    2. Load FeatureFlag from DB.
    3. Return school_overrides.get(school_id_str, is_globally_enabled).
    """
```

Guard usage in endpoints:
```python
if not await is_feature_enabled(redis, db, school_id, "parent_portal"):
    raise HTTPException(403, "Feature not enabled for this school")
```

---

## 4. Impersonation Flow

```python
async def impersonate_user(db, redis, super_admin, target_user_id, school_id, reason) -> str:
    """
    1. Verify super_admin has SUPER_ADMIN role.
    2. Load target_user.
    3. Create ImpersonationLog.
    4. Generate short-lived JWT (30min) with:
       sub=target_user.id, school_id=school_id, impersonated_by=super_admin.id
    5. Redis key: `impersonate:{token_jti}` = super_admin.id TTL 1800s
    6. Return token.
    """
```

---

## 5. API Endpoints (prefix `/super-admin` — requires role=SUPER_ADMIN)

```
GET    /super-admin/schools                   → list all schools + subscriptions
POST   /super-admin/schools                   → create new school
PUT    /super-admin/schools/{id}              → update school details
POST   /super-admin/schools/{id}/subscription → update subscription/plan
POST   /super-admin/schools/{id}/suspend      → suspend school access
GET    /super-admin/stats                     → platform-wide stats
GET    /super-admin/audit-logs                → platform-wide audit logs

POST   /super-admin/impersonate               → get impersonation token
POST   /super-admin/impersonate/end           → end impersonation

GET    /super-admin/feature-flags             → list all flags
PUT    /super-admin/feature-flags/{key}       → toggle flag globally or per school
```

---

## 6. Frontend: Super Admin Portal (`/super-admin`)

- School list with status, plan, student/staff count
- School detail with subscription editor
- Feature flags management matrix
- Impersonate button with reason prompt
- Platform analytics (charts: total schools, students, active today)
- Global audit log viewer

---

## Verification Checklist

- [ ] All `/super-admin/*` endpoints blocked for non-SUPER_ADMIN roles (return 403)
- [ ] Impersonation JWT includes `impersonated_by` claim
- [ ] `ImpersonationLog.ended_at` set when impersonation token expires or is revoked
- [ ] Feature flag checks cached in Redis for 5 minutes
- [ ] `school_overrides` JSONB supports per-school toggle overrides
- [ ] School suspension sets `school.is_active=False`, blocking all API access
- [ ] Platform stats query all schools' data in aggregate
