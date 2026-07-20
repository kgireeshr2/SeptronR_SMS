# PHASE 1 — PROJECT SETUP & INFRASTRUCTURE

## Pre-Requisite
Complete `00_PREREQUISITE_Project_Setup.md` first. The full monorepo skeleton, Docker Compose, Axios instance, Zustand stores, and PrivateRoute must exist before starting this phase.

## Objective
Wire together the full backend bootstrap and frontend bootstrap so the app is runnable end-to-end, with multi-tenant school context flowing through every request.

---

## 1.1 Backend Bootstrap

### FastAPI Application (`backend/main.py`)
Implement the following in the lifespan context manager:
- On startup: log app version, verify DB connection (`SELECT 1`), verify Redis `PING`, create uploads directory if missing
- On shutdown: dispose SQLAlchemy async engine
- Register global exception handlers:
  - `RequestValidationError` → 422 with `{ success: false, message: "Validation error", data: errors }`
  - `HTTPException` → preserve status code with envelope
  - Unhandled `Exception` → 500 with `{ success: false, message: "Internal server error" }` (never expose stack in production)

### Environment Configuration (`backend/app/core/config.py`)
All settings via Pydantic `BaseSettings` reading from `.env`:
```
APP_NAME, APP_ENV, DEBUG, SECRET_KEY, ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES=15, REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS (comma-separated list)
DATABASE_URL (postgresql+asyncpg://...)
REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
STORAGE_BACKEND (local|s3), UPLOAD_DIR, MAX_FILE_SIZE_MB
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME
SMS_PROVIDER, MSG91_AUTH_KEY, MSG91_SENDER_ID
TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
META_WHATSAPP_TOKEN, META_PHONE_NUMBER_ID
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME, SMTP_FROM_EMAIL
SENDGRID_API_KEY
FCM_SERVER_KEY, FIREBASE_PROJECT_ID
```

### Async PostgreSQL Setup (`backend/app/db/session.py`)
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Alembic Configuration (`backend/alembic/env.py`)
Use async migration pattern with `asyncio.run()`:
```python
from alembic.runtime.migration import MigrationContext
from sqlalchemy.ext.asyncio import async_engine_from_config
# Import ALL models so metadata is populated
from app.db.session import Base
import app.models  # noqa
```

### Middleware Stack (applied in this order — LIFO via FastAPI)
1. **GZipMiddleware** — compress responses > 1 KB
2. **CORSMiddleware** — origins from settings, allow credentials
3. **RequestLoggerMiddleware** — log `[req_id] METHOD /path → status (Xms)`
4. **SchoolContextMiddleware** — extract school slug from `X-School-Slug` header

### Health Check Endpoint
```
GET /health
```
Returns:
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "version": "1.0.0",
  "environment": "development"
}
```
Individually catches DB and Redis failures; returns `"degraded"` status if either is down. **No authentication required.**

### API Router Setup (`backend/app/api/v1/router.py`)
All routes prefixed `/api/v1/`. Create the aggregation router. Each module will add its sub-router here in future phases.

---

## 1.2 Alembic Initial Migration

Run the database schema SQL against PostgreSQL to create all tables. Then generate the first Alembic baseline migration:
```bash
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

Verify all 67 tables are created.

---

## 1.3 Frontend Bootstrap

### Vite + React + TypeScript
- Vite config with absolute import aliases `@/`, `@api/`, `@components/`, etc.
- All paths proxied: `/api` → `http://localhost:8000`, `/ws` → `ws://localhost:8000`

### Tailwind CSS + shadcn/ui Init
```bash
npx shadcn-ui@latest init
```
Choose: style=Default, base color=Slate, CSS variables=Yes.

Install these shadcn components:
```bash
npx shadcn-ui@latest add button input label card dialog dropdown-menu select table tabs tooltip badge avatar separator sheet popover checkbox switch form
```

### TanStack Query Setup (`frontend/src/main.tsx`)
```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      onError: (error: unknown) => {
        const msg = (error as { message?: string })?.message || 'An error occurred';
        toast.error(msg);
      },
    },
  },
});
```

### App Layout (`frontend/src/components/layout/AppLayout.tsx`)
- `<Sidebar>` — role-adaptive navigation links
- `<Navbar>` — academic year selector, bell icon (unread count), user avatar menu
- `<Outlet>` for page content
- `<ErrorBoundary>` wrapping outlet

### Sidebar (`frontend/src/components/layout/Sidebar.tsx`)
Navigation groups (show only if user has `view` permission):
```
MAIN
  Dashboard          → /dashboard
ACADEMIC
  Academic Years     → /admin/academic-years
  Admissions         → /admin/admissions
  Classes & Sections → /admin/classes
  Subjects           → /admin/subjects
  Timetable          → /admin/timetable
PEOPLE
  Students           → /admin/students
  Staff              → /admin/staff
OPERATIONS
  Attendance         → /admin/attendance
  Fees               → /admin/fees
  Exams              → /admin/exams
  Library            → /admin/library
  Transport          → /admin/transport
  Inventory          → /admin/inventory
  Accounting         → /admin/accounting
COMMUNICATION
  Messages           → /admin/communication
  Calendar           → /admin/calendar
  Homework           → /admin/homework
  PTM                → /admin/ptm
ADMIN
  Reports            → /admin/reports
  Audit Logs         → /admin/audit-logs
  Settings           → /admin/settings
  Roles              → /admin/roles
```

Sidebar item component must check `hasPermission(module, 'view')` before rendering.

### Academic Year Selector (Navbar component)
```tsx
// On mount: fetch GET /api/v1/academic-years → populate store
// Show current year name as button → click opens dropdown of all years
// On select: update academicYearStore.selectedYear
// All module pages read selectedYear from store for filters
```

### Notification Bell (Navbar component)
```tsx
// Show unread count badge
// On click: dropdown of latest 5 unread notifications
// WebSocket subscription added in Phase 14
// For now: fetch GET /api/v1/notifications?is_read=false&page_size=5
```

### Route Definitions (`frontend/src/routes/index.tsx`)
```tsx
<Routes>
  {/* Public */}
  <Route path="/login" element={<LoginPage />} />
  <Route path="/forgot-password" element={<ForgotPasswordPage />} />
  <Route path="/reset-password" element={<ResetPasswordPage />} />
  <Route path="/admissions/apply/:slug" element={<PublicAdmissionForm />} />

  {/* Protected */}
  <Route element={<PrivateRoute />}>
    <Route element={<AppLayout />}>
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/admin/academic-years" element={<AcademicYearsPage />} />
      <Route path="/admin/admissions" element={<AdmissionsPage />} />
      <Route path="/admin/classes" element={<ClassesPage />} />
      {/* ... one route per module */}
    </Route>
    {/* Portals */}
    <Route path="/student/*" element={<StudentPortal />} />
    <Route path="/parent/*" element={<ParentPortal />} />
    <Route path="/teacher/*" element={<TeacherPortal />} />
  </Route>

  {/* Catch-all */}
  <Route path="*" element={<NotFoundPage />} />
</Routes>
```

Use `React.lazy()` + `<Suspense>` on every page component.

---

## 1.4 Multi-Tenant Design

### School Identification Strategy
- **Subdomain**: `greenwood.sms.com` → Nginx extracts `greenwood` → `X-School-Slug: greenwood` header
- **Fallback**: JWT payload contains `school_id` claim — used by API after token decode

### SchoolContextMiddleware Behavior
```python
class SchoolContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        school_slug = request.headers.get("X-School-Slug", "").strip().lower()
        request.state.school_slug = school_slug
        request.state.school_id = None  # set by get_current_user after JWT decode
        return await call_next(request)
```

### Dependency: `get_current_school_id`
After JWT decode in `get_current_user`:
```python
request.state.school_id = current_user.school_id
```
All repository methods receive `school_id` as a mandatory filter.

### Super Admin Exception
- Users with `is_super_admin = TRUE` skip the `school_id` filter
- Detected in `permission_required` dependency: skip school scoping
- Dashboard shows cross-school aggregate data

---

## 1.5 Database Models Base Class (`backend/app/models/base.py`)

```python
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.session import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UUIDPrimaryKeyMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

All models inherit from `Base` + mixins.

---

## 1.6 Tests

### `backend/tests/test_health.py`
```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "database" in data
    assert "redis" in data
```

### `backend/tests/conftest.py`
Set up async test database (use separate test DB), override `get_db` dependency, provide `async_client` fixture.

---

## 1.7 Deliverables Checklist

- [ ] `GET /health` returns correct JSON with DB and Redis status
- [ ] Alembic migration applied — 67 tables exist in DB
- [ ] FastAPI docs available at `http://localhost:8000/docs`
- [ ] All middleware applied in correct order (verified via request logs)
- [ ] Docker Compose `up` starts all 8 services cleanly
- [ ] Vite dev server starts at `http://localhost:5173`
- [ ] Tailwind CSS + shadcn/ui components render correctly
- [ ] TanStack Query QueryClient initialized with global error handling
- [ ] Zustand stores initialized and persisted
- [ ] AppLayout renders Sidebar + Navbar (with placeholder content)
- [ ] PrivateRoute redirects unauthenticated users to `/login`
- [ ] React Router routes defined for all modules (pages can be empty stubs)
- [ ] Test coverage: health check test passes
