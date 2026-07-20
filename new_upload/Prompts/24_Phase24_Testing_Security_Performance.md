# PHASE 24 — TESTING, SECURITY & PERFORMANCE

## Pre-Requisite
Phases 1–23 complete. All modules implemented and functional.

## Objective
Comprehensive test coverage (unit + integration + e2e), security hardening (rate limiting, CSRF, headers, injection prevention), and performance optimization (query tuning, caching, connection pooling, load testing).

---

## 24.1 Python Test Setup

### Directory Structure
```
backend/
  tests/
    conftest.py                  ← fixtures: app, db, auth helpers
    unit/
      services/
        test_fee_service.py
        test_attendance_service.py
        test_notification_service.py
        test_auth_service.py
        test_report_service.py
      models/
        test_models.py
      utils/
        test_formatters.py
        test_pagination.py
    integration/
      api/
        test_auth_api.py
        test_students_api.py
        test_fees_api.py
        test_attendance_api.py
        test_exams_api.py
        test_staff_api.py
        test_library_api.py
        test_transport_api.py
        test_notifications_api.py
        test_reports_api.py
        test_superadmin_api.py
    security/
      test_rate_limiting.py
      test_sql_injection.py
      test_auth_bypass.py
      test_permissions.py
      test_tenant_isolation.py
```

### `tests/conftest.py`

```python
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.db.session import get_db
from app.models import Base

TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/sms_test"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = AsyncSession(engine)
    try:
        yield async_session
    finally:
        await async_session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def school_and_admin(db, client):
    """Create a school and return admin credentials."""
    ...

@pytest_asyncio.fixture
async def auth_headers(client, school_and_admin):
    """Return Authorization header dict for admin user."""
    response = await client.post("/api/v1/auth/login", ...)
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}
```

---

## 24.2 Integration Test Examples

### `tests/integration/api/test_fees_api.py`

```python
async def test_create_fee_structure(client, auth_headers, ...):
    response = await client.post("/api/v1/fees/structures", headers=auth_headers, json={...})
    assert response.status_code == 201
    assert response.json()["success"] == True

async def test_collect_fee_partial(client, auth_headers, ...):
    # Create student fee → collect partial → check status is 'partial'
    ...

async def test_fee_receipt_pdf_generated(client, auth_headers, payment_id):
    response = await client.get(f"/api/v1/fees/payments/{payment_id}/receipt", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0

async def test_razorpay_signature_verification_fails_bad_signature(client, ...):
    response = await client.post("/api/v1/online-payments/verify",
        json={"razorpay_payment_id": "...", "razorpay_order_id": "...", "razorpay_signature": "bad"})
    assert response.status_code == 400
```

---

## 24.3 Security Tests

### `tests/security/test_tenant_isolation.py`

```python
async def test_school_a_cannot_read_school_b_students(client_a, client_b):
    """Most critical test: multi-tenant isolation."""
    # Create student in school A
    student_id = (await client_a.post("/api/v1/students", ...)).json()["data"]["id"]
    # Try to access it from school B
    response = await client_b.get(f"/api/v1/students/{student_id}")
    assert response.status_code == 404  # 404, not 403 (don't leak existence)

async def test_school_a_cannot_update_school_b_data(client_a, client_b, ...): ...
async def test_parent_cannot_access_other_student(client_parent_a, ...): ...
async def test_teacher_cannot_access_other_school(client_teacher, ...): ...
```

### `tests/security/test_auth_bypass.py`

```python
async def test_expired_token_rejected(client): ...
async def test_revoked_token_rejected(client, auth_headers): ...
    # logout → use same token → should get 401

async def test_tampered_token_rejected(client): ...
    # flip a bit in JWT signature → 401

async def test_impersonation_token_non_renewable(client, super_admin_headers): ...
    # impersonation token → try to refresh → 401
```

### `tests/security/test_permissions.py`

```python
async def test_teacher_cannot_create_fee_structure(client, teacher_headers): ...
    # → 403

async def test_parent_cannot_access_admin_endpoints(client, parent_headers): ...
    # GET /api/v1/students → 403

async def test_permission_required_decorator(client, limited_role_headers): ...
```

---

## 24.4 Rate Limiting

```python
# backend/app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

# Apply in main.py:
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# On endpoints:
@router.post("/auth/login")
@limiter.limit("10/minute")   # 10 login attempts per minute per IP
async def login(request: Request, ...): ...

@router.post("/auth/send-otp")
@limiter.limit("5/minute")
async def send_otp(request: Request, ...): ...

@router.post("/auth/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, ...): ...
```

Install: `pip install slowapi`

---

## 24.5 Security Headers Middleware

```python
# backend/app/middleware/security_headers.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://checkout.razorpay.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https://api.razorpay.com;"
        )
        return response
```

---

## 24.6 SQL Injection Prevention Checklist

1. **Always use parameterized queries** — SQLAlchemy ORM and `text()` with `:param` bindings.
2. **Never use f-strings in SQL** — Static analysis lint rule.
3. Search parameters go through ORM `.filter()` or `.where()` only.
4. File upload validation: allowed extensions, virus scan hook (optional).
5. Input length limits enforced via Pydantic `max_length=`.

```python
# WRONG:
await db.execute(text(f"SELECT * FROM students WHERE name = '{name}'"))

# RIGHT:
await db.execute(text("SELECT * FROM students WHERE name = :name"), {"name": name})
# Or via ORM:
await db.execute(select(Student).where(Student.full_name == name))
```

---

## 24.7 Database Performance Optimizations

### Required Indexes (add in Alembic migration)

```sql
-- Attendance: two-table design (attendance_sessions + student_attendance)
CREATE INDEX IF NOT EXISTS idx_att_sessions_school_date ON attendance_sessions(school_id, session_date);
CREATE INDEX IF NOT EXISTS idx_att_sessions_section ON attendance_sessions(section_id, session_date);
CREATE INDEX IF NOT EXISTS idx_student_attendance_session ON student_attendance(session_id);
CREATE INDEX IF NOT EXISTS idx_student_attendance_student ON student_attendance(student_id);

-- Fees: invoice-level queries
CREATE INDEX IF NOT EXISTS idx_fee_invoices_status ON fee_invoices(school_id, status, due_date);
CREATE INDEX IF NOT EXISTS idx_fee_payments_invoice ON fee_payments(invoice_id, created_at);

-- Notifications: unread queries per user
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read, created_at);

-- Audit logs: partitioned table — create on each partition; school + date most common
CREATE INDEX IF NOT EXISTS idx_audit_logs_school ON audit_logs(school_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_record ON audit_logs(record_type, record_id);

-- Students: enrollment year lookups
CREATE INDEX IF NOT EXISTS idx_enrollments_year ON student_enrollments(academic_year_id, class_id, section_id);

-- Library: overdue issues (table is book_issues)
CREATE INDEX IF NOT EXISTS idx_book_issues_overdue ON book_issues(due_date) WHERE returned_at IS NULL;
```

### SQLAlchemy Query Optimization

```python
# Use selectinload for collections to avoid N+1
from sqlalchemy.orm import selectinload

stmt = (
    select(Student)
    .options(selectinload(Student.enrollments).selectinload(StudentEnrollment.section))
    .where(Student.school_id == school_id)
)

# Use joinedload for single relationships
from sqlalchemy.orm import joinedload
stmt = select(Student).options(joinedload(Student.current_enrollment))
```

---

## 24.8 Connection Pool Configuration

```python
# backend/app/db/session.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,           # base connections
    max_overflow=10,        # extra connections burst
    pool_timeout=30,        # wait time before error
    pool_recycle=3600,      # recycle after 1 hour
    pool_pre_ping=True,     # verify live connection before use
    echo=False,             # True only in development
)
```

---

## 24.9 Redis Caching Strategy Summary

| Resource | Key Pattern | TTL | Invalidated On |
|----------|-------------|-----|----------------|
| School settings | `settings:{school_id}` | 5 min | Settings update |
| Academic years | `academic_years:{school_id}` | 30 min | Year CRUD |
| Dashboard admin | `dashboard:admin:{school_id}:{year_id}` | 2 min | Any data change |
| Permissions | `permissions:{user_id}` | 60 min | Role change / logout |
| Classes & sections | `classes:{school_id}:{year_id}` | 30 min | Class CRUD |
| Fee structures | `fee_structures:{school_id}:{year_id}` | 30 min | Fee structure CRUD |
| Public settings | `public_settings:{school_slug}` | 10 min | Settings update |

---

## 24.10 Load Testing with Locust

### `tests/load/locustfile.py`

```python
from locust import HttpUser, task, between

class ParentUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        res = self.client.post("/api/v1/auth/login", json={...})
        self.token = res.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/dashboard/parent?year_id=...", headers=self.headers)

    @task(2)
    def view_attendance(self):
        self.client.get(f"/api/v1/students/.../attendance/summary?month=3&year=2025", headers=self.headers)

    @task(1)
    def view_fees(self):
        self.client.get(f"/api/v1/students/.../fees/outstanding", headers=self.headers)

class AdminUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def view_admin_dashboard(self):
        self.client.get("/api/v1/dashboard/admin?year_id=...", headers=self.headers)
```

Run: `locust -f tests/load/locustfile.py --headless -u 100 -r 10 --run-time 60s --host http://localhost:8000`

**Target benchmarks:**
- 95th percentile response time < 500ms for all endpoints
- Throughput ≥ 100 req/s on 2-core server
- Zero 5xx errors under 100 concurrent users

---

## 24.11 Frontend Security

1. **XSS Prevention:** All dynamic content via React JSX (auto-escaped). Use `DOMPurify` only for `dangerouslySetInnerHTML` in template preview.

```typescript
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userHtmlInput);
```

2. **CSRF:** Not applicable (JWT-based auth, no cookies). Ensure `Authorization: Bearer` only.

3. **Sensitive Data in Storage:** Only JWT tokens in `localStorage`. No student PII stored client-side.

4. **Input Validation:** All forms use Zod schemas before API calls.

5. **Open Redirects:** After login, validate `redirect` param is same-origin.

---

## 24.12 Security Audit Checklist

- [ ] All endpoints require authentication (check with pytest coverage)
- [ ] All write endpoints require specific permissions
- [ ] Tenant isolation enforced in every repository method (school_id filter)
- [ ] Rate limiting on auth endpoints
- [ ] JWT token revocation on logout (Redis JTI blacklist)
- [ ] Passwords hashed with bcrypt (cost factor ≥ 12)
- [ ] No sensitive data in JWT payload (no passwords, no full PII)
- [ ] File upload: validate MIME type, extension whitelist, size limit
- [ ] Razorpay signature verified on every callback
- [ ] No secrets in code — all via environment variables
- [ ] SQL injection: no f-strings in queries
- [ ] Security headers middleware applied
- [ ] CORS configured to specific origins (not *)

---

## 24.13 Pytest Configuration (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
filterwarnings = ["ignore::DeprecationWarning"]
markers = [
    "slow: marks tests as slow",
    "security: marks security tests",
    "integration: marks integration tests",
]

[tool.coverage.run]
source = ["app"]
omit = ["app/db/migrations/*", "tests/*"]

[tool.coverage.report]
fail_under = 75   # minimum 75% test coverage required
```

---

## 24.14 Deliverables Checklist

- [ ] `tests/conftest.py` with DB fixtures (uses test DB, isolated per function)
- [ ] Integration tests for all module APIs (auth, students, fees, attendance, exams, staff, library, transport, notifications, reports, superadmin)
- [ ] Tenant isolation tests (school A cannot access school B data)
- [ ] Permission bypass tests (all roles tested against unauthorized endpoints)
- [ ] Rate limiting on login, OTP, and password reset endpoints
- [ ] Security headers middleware in place
- [ ] SQL injection lint rule or test coverage
- [ ] All required DB indexes created in Alembic migration
- [ ] Connection pool configured (pool_size=20, max_overflow=10, pool_pre_ping=True)
- [ ] All Redis cache patterns documented and implemented
- [ ] Locust load test file with Admin and Parent user scenarios
- [ ] Load test target: 95th percentile < 500ms at 100 concurrent users
- [ ] `DOMPurify` applied to all HTML template preview rendering
- [ ] Coverage ≥ 75% enforced via `pytest-cov`
