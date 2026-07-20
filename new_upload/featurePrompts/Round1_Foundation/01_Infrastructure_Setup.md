# Feature Prompt 01 — Infrastructure Setup

## Round: 1 of 4 — Foundation
## Prerequisites: None (this is the starting point)

---

## Objective

Bootstrap the complete project infrastructure: Docker Compose environment, FastAPI backend (with middleware, health check, Alembic migrations), Celery workers, and React/Vite frontend skeleton. By the end of this prompt the app starts locally, `/health` returns `{"status":"ok"}`, the database schema is created with all 67 tables, and the frontend Vite dev server loads.

---

## 1. Project Folder Structure to Create

```
SMS/
├── docker-compose.yml
├── docker-compose.prod.yml
├── nginx/
│   └── nginx.conf
├── backend/
│   ├── Dockerfile
│   ├── main.py
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── .env.example
│   ├── alembic/
│   │   ├── env.py
│   │   └── script.py.mako
│   └── app/
│       ├── __init__.py
│       ├── main.py          ← FastAPI app factory
│       ├── core/
│       │   ├── config.py    ← Pydantic BaseSettings
│       │   ├── security.py  ← JWT helpers
│       │   ├── dependencies.py
│       │   ├── exceptions.py
│       │   └── middleware.py
│       ├── db/
│       │   └── session.py
│       ├── models/           ← all SQLAlchemy models (stubs for other phases)
│       │   └── base.py
│       ├── schemas/
│       ├── repositories/
│       ├── services/
│       ├── api/
│       │   └── v1/
│       │       ├── router.py
│       │       └── endpoints/
│       ├── tasks/
│       │   └── celery_app.py
│       ├── templates/
│       └── utils/
│           ├── response.py
│           └── pagination.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── tailwind.config.ts
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── api/
        │   └── axios.ts
        ├── store/
        │   ├── authStore.ts
        │   └── academicYearStore.ts
        ├── hooks/
        ├── components/
        │   ├── layout/
        │   │   ├── AppLayout.tsx
        │   │   ├── Navbar.tsx
        │   │   └── Sidebar.tsx
        │   └── shared/
        │       ├── LoadingSkeleton.tsx
        │       ├── PageHeader.tsx
        │       ├── DataTable.tsx
        │       ├── ErrorBoundary.tsx
        │       └── PermissionGuard.tsx
        ├── pages/
        │   ├── auth/
        │   │   └── LoginPage.tsx
        │   └── Dashboard.tsx
        ├── routes/
        │   ├── index.tsx
        │   └── PrivateRoute.tsx
        ├── types/
        │   └── index.ts
        └── utils/
            ├── constants.ts
            ├── formatters.ts
            └── cn.ts
```

---

## 2. Docker Compose (`docker-compose.yml`)

Create `docker-compose.yml` with the following 8 services on network `sms_network`:

```yaml
version: "3.9"
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: sms_db
      POSTGRES_USER: sms_user
      POSTGRES_PASSWORD: sms_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sms_user -d sms_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    env_file:
      - ./backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    env_file:
      - ./backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q notifications,emails,reports,scheduled --concurrency=4

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    volumes:
      - ./backend:/app
    env_file:
      - ./backend/.env
    depends_on:
      redis:
        condition: service_healthy
    command: celery -A app.tasks.celery_app beat --loglevel=info

  flower:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5555:5555"
    env_file:
      - ./backend/.env
    depends_on:
      redis:
        condition: service_healthy
    command: celery -A app.tasks.celery_app flower --port=5555

  frontend:
    image: node:20-alpine
    working_dir: /app
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    command: sh -c "npm install && npm run dev -- --host 0.0.0.0"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  uploads:

networks:
  default:
    name: sms_network
```

---

## 3. Backend: `backend/requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.7.3
pydantic-settings==2.3.1
redis==5.0.5
celery==5.4.0
bcrypt==4.1.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
aiofiles==23.2.1
httpx==0.27.0
weasyprint==62.3
jinja2==3.1.4
openpyxl==3.1.4
qrcode[pil]==7.4.2
pillow==10.3.0
razorpay==1.4.1
twilio==9.2.2
sendgrid==6.11.0
firebase-admin==6.5.0
boto3==1.34.131
python-slugify==8.0.4
arrow==1.3.0
reportlab==4.2.2
pypdf==4.2.0
slowapi==0.1.9
prometheus-fastapi-instrumentator==7.0.0
icalendar==6.0.0
```

---

## 4. Backend: `backend/app/core/config.py`

Use Pydantic `BaseSettings` with `model_config = SettingsConfigDict(env_file=".env")`.

Include fields:
```python
# Database
DATABASE_URL: str  # postgresql+asyncpg://...

# Redis
REDIS_URL: str  # redis://redis:6379/0
CELERY_BROKER_URL: str  # redis://redis:6379/1
CELERY_RESULT_BACKEND: str  # redis://redis:6379/2

# Auth
SECRET_KEY: str
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# App
APP_ENV: str = "development"
DEBUG: bool = True
ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
UPLOAD_DIR: str = "./uploads"
MAX_UPLOAD_SIZE_MB: int = 10

# SMTP
SMTP_HOST: str = ""
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
DEFAULT_FROM_EMAIL: str = "noreply@school.com"

# SMS (MSG91)
MSG91_AUTH_KEY: str = ""
MSG91_SENDER_ID: str = "SCHOOL"
MSG91_TEMPLATE_ID: str = ""

# Twilio (alternative SMS)
TWILIO_ACCOUNT_SID: str = ""
TWILIO_AUTH_TOKEN: str = ""
TWILIO_PHONE_NUMBER: str = ""

# WhatsApp (Meta Cloud API)
META_WHATSAPP_TOKEN: str = ""
META_PHONE_NUMBER_ID: str = ""

# Firebase FCM
FCM_SERVER_KEY: str = ""

# AWS S3 (optional)
AWS_ACCESS_KEY_ID: str = ""
AWS_SECRET_ACCESS_KEY: str = ""
AWS_S3_BUCKET: str = ""
AWS_REGION: str = "ap-south-1"

# Razorpay
RAZORPAY_KEY_ID: str = ""
RAZORPAY_KEY_SECRET: str = ""

settings = Settings()
```

---

## 5. Backend: `backend/app/db/session.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## 6. Backend: `backend/app/core/security.py`

Implement:
- `hash_password(plain: str) -> str` — bcrypt hash
- `verify_password(plain: str, hashed: str) -> bool`
- `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str`
  - Payload: `{sub: user_id, school_id, email, is_super_admin, jti: uuid4, exp, iat}`
- `decode_token(token: str) -> dict` — raises `HTTPException(401)` on invalid/expired

---

## 7. Backend: `backend/app/core/middleware.py`

### `RequestLoggerMiddleware`
```python
class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid4())
        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)
        logger.info(f"[{request_id}] {request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)")
        response.headers["X-Request-ID"] = request_id
        return response
```

### `SchoolContextMiddleware`
```python
class SchoolContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        school_slug = request.headers.get("X-School-Slug", "")
        request.state.school_slug = school_slug
        return await call_next(request)
```

---

## 8. Backend: `backend/main.py` (entry point)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import settings
from app.core.middleware import RequestLoggerMiddleware, SchoolContextMiddleware
from app.db.session import engine
from app.api.v1.router import api_router
import redis.asyncio as aioredis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ping DB and Redis
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    redis_client = aioredis.from_url(settings.REDIS_URL)
    await redis_client.ping()
    app.state.redis = redis_client
    yield
    # Shutdown
    await redis_client.close()
    await engine.dispose()

app = FastAPI(
    title="School Management System API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Middleware (added in reverse order — last added runs first)
app.add_middleware(SchoolContextMiddleware)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
app.include_router(api_router, prefix="/api/v1")

# Health check (no auth required)
@app.get("/health")
async def health_check(request: Request):
    db_ok, redis_ok = True, True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    try:
        await request.app.state.redis.ping()
    except Exception:
        redis_ok = False
    status = "ok" if db_ok and redis_ok else "degraded"
    return {"status": status, "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error"}
```

---

## 9. Backend: `backend/app/utils/response.py`

```python
from fastapi.encoders import jsonable_encoder
from typing import Any

def ok(data: Any = None, message: str = "Success", pagination: dict | None = None):
    return {
        "success": True,
        "data": jsonable_encoder(data),
        "message": message,
        "pagination": pagination,
    }

def error(message: str = "An error occurred", data: Any = None):
    return {
        "success": False,
        "data": jsonable_encoder(data),
        "message": message,
        "pagination": None,
    }
```

---

## 10. Backend: `backend/app/utils/pagination.py`

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

async def paginate(db: AsyncSession, query, page: int = 1, page_size: int = 20):
    """Execute a paginated query. Returns (items, pagination_meta)."""
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    # Fetch page
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.scalars().all()
    pagination = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
    return items, pagination
```

---

## 11. Backend: `backend/app/tasks/celery_app.py`

```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "sms_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_queues={
        "notifications": {"exchange": "notifications"},
        "emails": {"exchange": "emails"},
        "reports": {"exchange": "reports"},
        "scheduled": {"exchange": "scheduled"},
    },
    task_default_queue="notifications",
)
# Auto-discover tasks from all app.tasks.* modules
celery_app.autodiscover_tasks(["app.tasks"])
```

---

## 12. Backend: `backend/alembic/env.py`

Implement async Alembic env with:
```python
import asyncio
from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from app.models.base import Base
from app.core.config import settings

# Import ALL models so Alembic can see them for autogenerate
from app.models import (
    auth, rbac, school, academic, admissions, classes,
    students, staff, attendance, fees, exams, library,
    transport, inventory, accounting, communications,
    calendar, homework_ptm, document_templates, audit, super_admin
)

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
target_metadata = Base.metadata

async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.", poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())
```

---

## 13. Backend: `backend/app/models/base.py`

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

class SoftDeleteMixin:
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
```

---

## 14. Backend: `backend/app/core/exceptions.py`

Register global exception handlers on the FastAPI app:
- `RequestValidationError` → 422, return `{"success": false, "message": "Validation error", "data": errors}`
- `HTTPException` → pass-through, wrap in response envelope
- `Exception` (catch-all) → 500, log traceback, return `{"success": false, "message": "Internal server error"}`

---

## 15. Backend: `backend/app/api/v1/router.py`

Create a stub router that will grow as features are added:
```python
from fastapi import APIRouter
api_router = APIRouter()
# Routes added by each feature prompt
```

---

## 16. Backend: `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libcairo2 libffi-dev libssl-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 17. Nginx: `nginx/nginx.conf`

```nginx
events { worker_connections 1024; }

http {
    upstream backend  { server backend:8000; }
    upstream frontend { server frontend:5173; }

    server {
        listen 80;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header X-School-Slug $host;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
        }

        location /health {
            proxy_pass http://backend;
        }

        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
        }
    }
}
```

---

## 18. Frontend: `frontend/package.json`

Include these dependencies:
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.24.0",
    "@tanstack/react-query": "^5.45.0",
    "@tanstack/react-table": "^8.17.3",
    "zustand": "^4.5.4",
    "axios": "^1.7.2",
    "react-hook-form": "^7.52.0",
    "@hookform/resolvers": "^3.6.0",
    "zod": "^3.23.8",
    "recharts": "^2.12.7",
    "@fullcalendar/react": "^6.1.14",
    "@fullcalendar/daygrid": "^6.1.14",
    "@fullcalendar/timegrid": "^6.1.14",
    "@fullcalendar/list": "^6.1.14",
    "@fullcalendar/interaction": "^6.1.14",
    "date-fns": "^3.6.0",
    "lucide-react": "^0.395.0",
    "sonner": "^1.5.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.3.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-select": "^2.1.0",
    "@radix-ui/react-tabs": "^1.1.0",
    "@radix-ui/react-toast": "^1.2.0",
    "@radix-ui/react-checkbox": "^1.1.0",
    "@radix-ui/react-label": "^2.1.0",
    "@radix-ui/react-popover": "^1.1.0",
    "@radix-ui/react-avatar": "^1.1.0",
    "@radix-ui/react-badge": "^1.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.5.2",
    "vite": "^5.3.1",
    "tailwindcss": "^3.4.4",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38"
  }
}
```

---

## 19. Frontend: `frontend/src/api/axios.ts`

```typescript
import axios from 'axios';
import { useAuthStore } from '@store/authStore';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,  // send httpOnly refresh cookie
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
let isRefreshing = false;
let refreshQueue: Array<(token: string) => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push((token) => {
            original.headers.Authorization = `Bearer ${token}`;
            resolve(api(original));
          });
        });
      }
      isRefreshing = true;
      try {
        const res = await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true });
        const newToken = res.data.data.access_token;
        useAuthStore.getState().setAccessToken(newToken);
        refreshQueue.forEach((cb) => cb(newToken));
        refreshQueue = [];
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 20. Frontend: Zustand Stores

### `frontend/src/store/authStore.ts`
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  fullName: string;
  avatarUrl?: string;
  isSuperAdmin: boolean;
  roles: string[];
}

interface SchoolInfo {
  id: string;
  name: string;
  slug: string;
  logoUrl?: string;
}

interface AuthState {
  accessToken: string | null;
  currentUser: User | null;
  schoolInfo: SchoolInfo | null;
  permissions: string[];  // ["students:view", "fees:create", ...]
  setAccessToken: (token: string) => void;
  setUser: (user: User, school: SchoolInfo | null, permissions: string[]) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      currentUser: null,
      schoolInfo: null,
      permissions: [],
      setAccessToken: (token) => set({ accessToken: token }),
      setUser: (user, school, permissions) =>
        set({ currentUser: user, schoolInfo: school, permissions }),
      logout: () => set({ accessToken: null, currentUser: null,
                          schoolInfo: null, permissions: [] }),
    }),
    { name: 'sms-auth' }
  )
);
```

### `frontend/src/store/academicYearStore.ts`
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AcademicYear { id: string; name: string; isCurrent: boolean; }

interface AcademicYearState {
  selectedYear: AcademicYear | null;
  years: AcademicYear[];
  setSelectedYear: (year: AcademicYear) => void;
  setYears: (years: AcademicYear[]) => void;
}

export const useAcademicYearStore = create<AcademicYearState>()(
  persist(
    (set) => ({
      selectedYear: null,
      years: [],
      setSelectedYear: (year) => set({ selectedYear: year }),
      setYears: (years) => set({ years }),
    }),
    { name: 'sms-academic-year' }
  )
);
```

---

## 21. Frontend: `frontend/src/hooks/usePermission.ts`

```typescript
import { useAuthStore } from '@store/authStore';

export const usePermission = () => {
  const { permissions, currentUser } = useAuthStore();
  const hasPermission = (module: string, action: string): boolean => {
    if (currentUser?.isSuperAdmin) return true;
    return permissions.includes(`${module}:${action}`);
  };
  const hasAnyPermission = (module: string, actions: string[]): boolean =>
    actions.some((a) => hasPermission(module, a));
  return { hasPermission, hasAnyPermission };
};
```

---

## 22. Frontend: `frontend/src/components/shared/PermissionGuard.tsx`

```typescript
import { usePermission } from '@hooks/usePermission';
import { ReactNode } from 'react';

interface Props {
  module: string;
  action: string;
  children: ReactNode;
  fallback?: ReactNode;
}

export const PermissionGuard = ({ module, action, children, fallback = null }: Props) => {
  const { hasPermission } = usePermission();
  return hasPermission(module, action) ? <>{children}</> : <>{fallback}</>;
};
```

---

## 23. Frontend: `frontend/src/routes/PrivateRoute.tsx`

```typescript
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@store/authStore';

export const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const { accessToken } = useAuthStore();
  const location = useLocation();
  if (!accessToken) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
};
```

---

## 24. Frontend: `frontend/src/utils/formatters.ts`

```typescript
import { format } from 'date-fns';

export const formatCurrency = (paise: number, currency = '₹'): string =>
  `${currency}${(paise / 100).toFixed(2)}`;

export const formatDate = (iso: string, fmt = 'dd MMM yyyy'): string => {
  try { return format(new Date(iso), fmt); } catch { return iso; }
};

export const truncate = (str: string, len = 50): string =>
  str.length > len ? `${str.slice(0, len)}...` : str;

export const getInitials = (name: string): string =>
  name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
```

---

## 25. Frontend: `frontend/src/utils/constants.ts`

```typescript
export const MODULES = [
  'dashboard', 'schools', 'users', 'roles', 'academic_years',
  'admissions', 'classes', 'subjects', 'timetable', 'staff',
  'leaves', 'payroll', 'students', 'attendance', 'fees',
  'exams', 'library', 'transport', 'inventory', 'accounting',
  'communication', 'calendar', 'homework', 'ptm', 'reports',
  'audit_logs', 'settings',
] as const;

export const ACTIONS = ['view', 'create', 'update', 'delete', 'export', 'approve', 'manage'] as const;

export const GENDER_OPTIONS = ['Male', 'Female', 'Other'] as const;
export const BLOOD_GROUP_OPTIONS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as const;
export const CATEGORY_OPTIONS = ['General', 'OBC', 'SC', 'ST', 'EWS'] as const;
```

---

## 26. First Alembic Migration

Create `backend/alembic/versions/001_initial_schema.py`.

The migration should create ALL tables used across all phases (even if empty). Running `alembic upgrade head` must succeed without errors. Import all models in `env.py` before running `autogenerate`, OR write the migration manually based on the models defined in all feature prompts. At minimum, create placeholder tables for all models.

---

## 27. Backend `.env.example`

```env
DATABASE_URL=postgresql+asyncpg://sms_user:sms_password@postgres:5432/sms_db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
SECRET_KEY=change-this-to-a-very-long-random-string-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
APP_ENV=development
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@school.com
MSG91_AUTH_KEY=
MSG91_SENDER_ID=SCHOOL
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
META_WHATSAPP_TOKEN=
META_PHONE_NUMBER_ID=
FCM_SERVER_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_REGION=ap-south-1
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

---

## Verification Checklist

After implementing this prompt, verify:

- [ ] `docker compose up -d` starts all 8 services without errors
- [ ] `GET http://localhost:8000/health` returns `{"status":"ok","database":"ok","redis":"ok"}`
- [ ] `GET http://localhost:8000/api/docs` shows FastAPI Swagger UI
- [ ] `docker compose run backend alembic upgrade head` completes without errors
- [ ] `http://localhost:5173` loads the React app (login page or blank)
- [ ] `http://localhost:5555` shows Flower Celery monitor
- [ ] All 8 containers are running: `docker compose ps`
- [ ] Axios interceptor attaches `Authorization: Bearer` header when token exists
- [ ] `useAuthStore.logout()` clears all auth state from `localStorage`
