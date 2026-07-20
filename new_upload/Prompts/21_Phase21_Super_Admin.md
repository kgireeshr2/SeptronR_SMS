# PHASE 21 — SUPER ADMIN PANEL

## Pre-Requisite
Phases 1–20 complete. `is_super_admin` flag on the User model, operates across all schools.

## Objective
Separate super admin portal at `/superadmin/*`. Create schools, manage subscriptions, view cross-school analytics, feature flags per school, impersonate school admin, view system-wide audit logs.

---

## 21.1 DB Additions

```sql
-- Add to users table (already exists but ensure field present):
-- is_super_admin BOOLEAN already exists in users table (see Database_Schema.sql line 152)
-- No ALTER needed; ensure it is seeded as TRUE for the first superadmin user.

-- Subscription / Plan model
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,                -- Starter, Professional, Enterprise
    max_students INTEGER,                      -- NULL = unlimited
    max_staff INTEGER,
    enabled_modules TEXT[] NOT NULL DEFAULT '{}',  -- ['attendance','fees','library',...]
    price_monthly_paise INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    starts_at DATE NOT NULL,
    ends_at DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Feature flags per school
CREATE TABLE IF NOT EXISTS school_feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    feature_key VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (school_id, feature_key)
);

-- Impersonation log
CREATE TABLE IF NOT EXISTS impersonation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    super_admin_id UUID NOT NULL REFERENCES users(id),
    impersonated_school_id UUID NOT NULL REFERENCES schools(id),
    impersonated_user_id UUID NOT NULL REFERENCES users(id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ
);
```

---

## 21.2 SQLAlchemy Models

```python
class SubscriptionPlan(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "subscription_plans"
    name: Mapped[str]
    max_students: Mapped[Optional[int]]
    max_staff: Mapped[Optional[int]]
    enabled_modules: Mapped[List[str]] = mapped_column(ARRAY(String))
    price_monthly_paise: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class SchoolSubscription(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "school_subscriptions"
    school_id: Mapped[UUID] = mapped_column(ForeignKey("schools.id"))
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("subscription_plans.id"))
    starts_at: Mapped[date]
    ends_at: Mapped[Optional[date]]
    is_active: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[Optional[str]]

class SchoolFeatureFlag(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "school_feature_flags"
    school_id: Mapped[UUID] = mapped_column(ForeignKey("schools.id"))
    feature_key: Mapped[str]
    is_enabled: Mapped[bool] = mapped_column(default=True)
    __table_args__ = (UniqueConstraint("school_id", "feature_key"),)

class ImpersonationLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "impersonation_logs"
    super_admin_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    impersonated_school_id: Mapped[UUID] = mapped_column(ForeignKey("schools.id"))
    impersonated_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]]
```

---

## 21.3 Dependency: Super Admin Guard

```python
# backend/app/api/dependencies.py

async def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_super_admin:
        raise HTTPException(403, "Super admin access required")
    return current_user
```

---

## 21.4 API Endpoints

All under `/api/v1/superadmin/*`, all guarded by `require_superuser`.

```
School Management
─────────────────
GET  /superadmin/schools            → list all schools (paginated, search)
POST /superadmin/schools            → create new school + seed defaults
GET  /superadmin/schools/{school_id} → school detail
PUT  /superadmin/schools/{school_id} → update school
POST /superadmin/schools/{school_id}/activate    → activate school
POST /superadmin/schools/{school_id}/deactivate  → soft deactivate

Subscription Management
───────────────────────
GET  /superadmin/plans              → list plans
POST /superadmin/plans              → create plan
GET  /superadmin/schools/{id}/subscription → get current subscription
POST /superadmin/schools/{id}/subscription → assign plan

Feature Flags
─────────────
GET  /superadmin/schools/{id}/features   → list features
PUT  /superadmin/schools/{id}/features   → bulk toggle features

System Stats
────────────
GET  /superadmin/stats               → { total_schools, active_schools, total_students, total_staff, total_revenue_paise }

Audit Logs (Cross School)
─────────────────────────
GET  /superadmin/audit-logs          → paginated, filter by school/user/action
    ?school_id=&user_name=&action=&record_type=&date_from=&date_to=

Impersonation
─────────────
POST /superadmin/impersonate         → create limited impersonation token
    body: { school_id, user_id }
    response: { access_token, expires_in: 3600 }  # max 1-hour token
POST /superadmin/impersonate/end     → mark ended_at in log

Users (Cross School)
────────────────────
GET  /superadmin/users               → search users across all schools
GET  /superadmin/users/{user_id}     → user detail (with school context)
POST /superadmin/users/{user_id}/reset-password → force reset
POST /superadmin/users/{user_id}/deactivate     → deactivate account
```

---

## 21.5 School Creation with Full Seeding

```python
async def create_school_with_seed(data: SchoolCreateRequest, db: AsyncSession) -> School:
    """
    1. Create school record with slug (auto-derived from name)
    2. Create default superadmin user for the school (role: Principal/Admin)
    3. Call seed_school_defaults(school_id, db) — creates:
       - 12 default roles with permissions
       - Default leave types (5)
       - Default school_settings (all keys with defaults)
       - Default notification templates (17 types)
       - Default grading scale (A+/A/B/C/D/F)
       - Default academic year for current year
    4. Assign FREE plan subscription
    5. Log audit: super_admin created school
    6. Return school with admin_user credentials
    """
```

---

## 21.6 Impersonation Token

```python
def create_impersonation_token(super_admin_user: User, target_user: User, school_id: str) -> str:
    """
    JWT token with:
    - sub: target_user.id
    - school_id: school_id
    - is_impersonation: True
    - impersonated_by: super_admin_user.id
    - exp: now + 3600 seconds (1 hour max, non-renewable)
    - jti: unique (stored in Redis for revocation: impersonate:{jti})
    """

# In get_current_user dependency: if is_impersonation=True in token,
# log access and inject impersonated school_id context transparently.
```

---

## 21.7 Frontend: `/superadmin/*`

**Layout:** Separate root layout (not school sidebar), minimal navbar with "Super Admin Panel" branding and logout.

Pages:
```
/superadmin/dashboard          — system stats overview
/superadmin/schools            — school list table
/superadmin/schools/new        — create school wizard
/superadmin/schools/:id        — school detail (subscription, features, users, audit)
/superadmin/audit-logs         — cross-school audit log with heavy filtering
```

**Schools List Page:**
- Columns: Name | Domain/Slug | Plan | Students | Staff | Status | Created | Actions
- Actions: View | Activate/Deactivate | Impersonate

**School Detail Page (tabs):**
- Overview: basic info + edit form
- Subscription: current plan + plan assignment
- Features: toggle grid (each feature key as toggle)
- Users: all school users list (read-only)
- Audit: recent audit log activity for this school
- Impersonate: button that opens user selector modal → calls impersonate API → opens new tab with injected token

**System Stats Dashboard:**
```
[Total Schools] [Active] [Total Students] [Total Staff]
[Monthly Revenue chart (last 12 months)]
[Schools by Plan — Pie Chart]
```

### `frontend/src/api/superadmin.ts`
```typescript
export const superAdminApi = {
  listSchools: (params?: any) => api.get('/superadmin/schools', { params }),
  createSchool: (data: any) => api.post('/superadmin/schools', data),
  updateSchool: (id: string, data: any) => api.put(`/superadmin/schools/${id}`, data),
  activateSchool: (id: string) => api.post(`/superadmin/schools/${id}/activate`),
  deactivateSchool: (id: string) => api.post(`/superadmin/schools/${id}/deactivate`),
  getStats: () => api.get('/superadmin/stats'),
  listAuditLogs: (params: any) => api.get('/superadmin/audit-logs', { params }),
  impersonate: (schoolId: string, userId: string) =>
    api.post('/superadmin/impersonate', { school_id: schoolId, user_id: userId }),
  getFeatures: (schoolId: string) => api.get(`/superadmin/schools/${schoolId}/features`),
  updateFeatures: (schoolId: string, features: Record<string, boolean>) =>
    api.put(`/superadmin/schools/${schoolId}/features`, features),
};
```

---

## 21.8 Available Feature Keys Reference

```python
FEATURE_KEYS = [
    "module_library",
    "module_transport",
    "module_inventory",
    "module_accounting",
    "module_homework",
    "module_ptm",
    "module_calendar",
    "module_templates",
    "online_payments",
    "whatsapp_notifications",
    "push_notifications",
    "sms_notifications",
    "parent_portal",
    "biometric_attendance",
    "gps_tracking",
    "bulk_sms_broadcast",
]
```

Frontend module guards check `school_feature_flags` to show/hide navigation items.

---

## 21.9 Tests

```python
async def test_non_superuser_denied_superadmin_routes(): ...
async def test_create_school_seeds_all_defaults(): ...
async def test_impersonation_token_max_1_hour(): ...
async def test_impersonation_log_recorded(): ...
async def test_feature_flag_toggle_hides_module(): ...
async def test_cross_school_audit_log_filter(): ...
async def test_deactivated_school_users_cannot_login(): ...
```

---

## 21.10 Deliverables Checklist

- [ ] `subscription_plans`, `school_subscriptions`, `school_feature_flags`, `impersonation_logs` tables and models
- [ ] `require_superuser` dependency guard
- [ ] All 20+ super admin endpoints
- [ ] School creation with full seed (roles, settings, notifications, grading, academic year)
- [ ] Impersonation: short-lived JWT, Redis-tracked, logged
- [ ] Feature flag enforcement in frontend module guards
- [ ] Separate `/superadmin/*` frontend layout and routes
- [ ] Cross-school audit log with all filters
- [ ] System stats dashboard with charts
- [ ] School detail tabs (overview, subscription, features, users, audit, impersonate)
