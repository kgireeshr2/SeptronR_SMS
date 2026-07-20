# PREREQUISITE — PROJECT SETUP & FILE STRUCTURE

## Context
You are building a production-grade, multi-tenant **School Management System (SMS/ERP)**  
Stack: **FastAPI (Python) · PostgreSQL 15 · Redis 7 · Celery 5 | React 18 (TypeScript) · Tailwind CSS · shadcn/ui**

This is the very first step. Create the entire monorepo skeleton — every folder, every config file, every boilerplate — so that all subsequent phase prompts can build on a consistent, working foundation.

---

## 1. Technology Stack Reference

| Layer | Technology |
|-------|-----------|
| Backend framework | FastAPI (async) |
| ORM | SQLAlchemy 2.x async + Alembic |
| Database | PostgreSQL 15+ |
| Cache / Queue | Redis 7 + Celery 5 |
| Auth | JWT access + refresh tokens, OAuth2 Password Bearer |
| File Storage | Local dev / AWS S3 + MinIO prod |
| PDF Engine | WeasyPrint + Jinja2 |
| SMS | Twilio / MSG91 |
| WhatsApp | Meta Cloud API |
| Email | SMTP / SendGrid |
| Push Notifications | Firebase FCM |
| WebSocket | FastAPI native WebSocket |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio + httpx |
| Containers | Docker + Docker Compose |
| Frontend framework | React 18 + TypeScript + Vite |
| Routing | React Router v6 |
| Data fetching | TanStack Query v5 |
| Global state | Zustand |
| UI library | shadcn/ui + Tailwind CSS v3 |
| Charts | Recharts |
| Calendar | FullCalendar.io (React) |
| Forms | React Hook Form + Zod |
| Tables | TanStack Table v8 |
| Print/PDF | react-to-print + html2canvas |
| Drag & Drop | dnd-kit |
| Rich text | TipTap editor |
| Icons | Lucide React |
| Date utilities | date-fns |
| Real-time | Native WebSocket |

---

## 2. Monorepo Root Structure to Create

```
sms/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── router.py           ← aggregates all module routers
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               ← Pydantic BaseSettings
│   │   │   ├── security.py             ← JWT encode/decode, password hashing
│   │   │   ├── dependencies.py         ← get_current_user, permission_required
│   │   │   └── middleware.py           ← SchoolContextMiddleware, RequestLogger
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py              ← async engine + SessionLocal factory
│   │   │   └── base.py                 ← Base = declarative_base(), imports all models
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   └── __init__.py
│   │   ├── repositories/
│   │   │   └── __init__.py
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   └── celery_app.py           ← Celery instance + config
│   │   ├── templates/
│   │   │   └── .gitkeep               ← Jinja2 HTML templates for PDFs
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── pagination.py
│   │       ├── file_upload.py
│   │       └── response.py             ← standard response envelope helper
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/                   ← migration files go here
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_health.py
│   ├── .env.example
│   ├── .env                            ← gitignored
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── main.py                         ← FastAPI app entry point
│
├── frontend/
│   ├── public/
│   │   ├── manifest.json               ← PWA manifest
│   │   └── icons/                      ← PWA icons
│   ├── src/
│   │   ├── api/                        ← Axios instances & API call functions
│   │   │   └── axios.ts                ← base Axios instance with interceptors
│   │   ├── components/
│   │   │   ├── ui/                     ← shadcn/ui base components
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Navbar.tsx
│   │   │   └── shared/
│   │   │       ├── DataTable.tsx
│   │   │       ├── PageHeader.tsx
│   │   │       ├── LoadingSkeleton.tsx
│   │   │       ├── PermissionGuard.tsx
│   │   │       └── ErrorBoundary.tsx
│   │   ├── pages/                      ← one folder per module
│   │   │   └── .gitkeep
│   │   ├── hooks/                      ← custom React hooks
│   │   │   └── usePermission.ts
│   │   ├── store/                      ← Zustand global stores
│   │   │   ├── authStore.ts
│   │   │   ├── notificationStore.ts
│   │   │   └── academicYearStore.ts
│   │   ├── types/                      ← TypeScript interfaces
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   ├── formatters.ts
│   │   │   ├── validators.ts
│   │   │   └── constants.ts
│   │   ├── routes/
│   │   │   ├── index.tsx               ← route definitions
│   │   │   └── PrivateRoute.tsx        ← auth guard
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── .env.example
│   ├── .env                            ← gitignored
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   └── components.json                 ← shadcn/ui config
│
├── nginx/
│   ├── nginx.conf
│   └── ssl/                            ← gitignored; certs go here
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .gitignore
└── README.md
```

---

## 3. Files to Generate — Backend

### `backend/requirements.txt`
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.7.1
pydantic-settings==2.3.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
aiofiles==23.2.1
redis[asyncio]==5.0.4
celery==5.4.0
flower==2.0.1
httpx==0.27.0
weasyprint==62.3
jinja2==3.1.4
boto3==1.34.100
twilio==9.1.0
firebase-admin==6.5.0
openpyxl==3.1.2
python-slugify==8.0.4
slowapi==0.1.9
email-validator==2.1.1
Pillow==10.3.0
qrcode[pil]==7.4.2
pandas==2.2.2
icalendar==5.0.12
pytz==2024.1
pypdf==4.2.0
python-magic==0.4.27
gunicorn==22.0.0
prometheus-fastapi-instrumentator==7.0.0
```

### `backend/requirements-dev.txt`
```
-r requirements.txt
pytest==8.2.0
pytest-asyncio==0.23.7
pytest-cov==5.0.0
httpx==0.27.0
factory-boy==3.3.0
faker==25.2.0
black==24.4.2
ruff==0.4.4
mypy==1.10.0
```

### `backend/.env.example`
```
# Application
APP_NAME="School Management System"
APP_ENV=development
SECRET_KEY=your-secret-key-min-32-chars-change-in-prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Database
DATABASE_URL=postgresql+asyncpg://sms_user:sms_pass@localhost:5432/sms_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# File Storage (local dev)
STORAGE_BACKEND=local
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10

# AWS S3 (production)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ap-south-1
S3_BUCKET_NAME=

# SMS (MSG91 or Twilio)
SMS_PROVIDER=msg91
MSG91_AUTH_KEY=
MSG91_SENDER_ID=SCHOOL
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=

# WhatsApp (Meta Cloud API)
META_WHATSAPP_TOKEN=
META_PHONE_NUMBER_ID=
META_WHATSAPP_VERIFY_TOKEN=

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_NAME="School SMS"
SMTP_FROM_EMAIL=noreply@school.com

# SendGrid (alternative)
SENDGRID_API_KEY=

# Firebase
FCM_SERVER_KEY=
FIREBASE_PROJECT_ID=
FIREBASE_SERVICE_ACCOUNT_JSON=

# Flower
FLOWER_PORT=5555
FLOWER_BASIC_AUTH=admin:admin
```

### `backend/main.py`
```python
"""
School Management System — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.middleware import RequestLoggerMiddleware, SchoolContextMiddleware
from app.db.session import engine, Base
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup: verify DB and Redis connectivity (optional eager check)
    yield
    # Shutdown: close engine
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware (applied in LIFO order) ────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(SchoolContextMiddleware)

# ── API Routes ────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check():
    """Returns DB and Redis connectivity status."""
    from app.db.session import async_session_factory
    from sqlalchemy import text
    import redis.asyncio as aioredis

    db_ok = False
    redis_ok = False

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        redis_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
```

### `backend/app/core/config.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "School Management System"
    APP_ENV: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    STORAGE_BACKEND: str = "local"      # "local" | "s3"
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str = ""

    SMS_PROVIDER: str = "msg91"
    MSG91_AUTH_KEY: str = ""
    MSG91_SENDER_ID: str = "SCHOOL"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    META_WHATSAPP_TOKEN: str = ""
    META_PHONE_NUMBER_ID: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "School SMS"
    SMTP_FROM_EMAIL: str = "noreply@school.com"

    SENDGRID_API_KEY: str = ""

    FCM_SERVER_KEY: str = ""
    FIREBASE_PROJECT_ID: str = ""


settings = Settings()
```

### `backend/app/db/session.py`
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a database session."""
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

### `backend/app/utils/response.py`
```python
from typing import Any, Optional
from pydantic import BaseModel


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = "Success"
    pagination: Optional[PaginationMeta] = None


def ok(data: Any = None, message: str = "Success", pagination: Optional[PaginationMeta] = None) -> dict:
    return APIResponse(success=True, data=data, message=message, pagination=pagination).model_dump()


def error(message: str = "An error occurred", data: Any = None) -> dict:
    return APIResponse(success=False, data=data, message=message).model_dump()
```

### `backend/app/utils/pagination.py`
```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.response import PaginationMeta


async def paginate(session: AsyncSession, query, count_query, page: int = 1, page_size: int = 20):
    """Generic pagination helper for SQLAlchemy async queries."""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    offset = (page - 1) * page_size

    total_result = await session.execute(count_query)
    total = total_result.scalar_one_or_none() or 0

    paginated_query = query.offset(offset).limit(page_size)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    meta = PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)
    return items, meta
```

### `backend/app/core/middleware.py`
```python
import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy import select

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status code and duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"[{request_id}] {request.method} {request.url.path}")
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000
        logger.info(f"[{request_id}] → {response.status_code} ({duration:.1f}ms)")
        return response


class SchoolContextMiddleware(BaseHTTPMiddleware):
    """
    Extracts school_id from:
      1. X-School-Slug header (set by Nginx from subdomain)
      2. JWT claim 'school_id' (set after token decode in auth dependency)
    Sets request.state.school_id and request.state.school_slug.
    """

    async def dispatch(self, request: Request, call_next):
        school_slug = request.headers.get("X-School-Slug", "")
        request.state.school_slug = school_slug
        request.state.school_id = None  # populated by get_current_user dependency
        return await call_next(request)
```

### `backend/app/api/v1/router.py`
```python
from fastapi import APIRouter

api_router = APIRouter()

# Modules will be included here as they are built, e.g.:
# from app.api.v1.endpoints import auth, students, staff, fees, ...
# api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
```

### `backend/app/tasks/celery_app.py`
```python
from celery import Celery
from app.core.config import settings

celery = Celery(
    "sms_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.notifications",
        "app.tasks.reports",
        "app.tasks.emails",
        "app.tasks.scheduled",
    ],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.notifications.*": {"queue": "notifications"},
        "app.tasks.reports.*": {"queue": "reports"},
        "app.tasks.emails.*": {"queue": "emails"},
        "app.tasks.scheduled.*": {"queue": "scheduled"},
    },
)
```

### `backend/alembic.ini`
Configure pointing to `backend/alembic/` directory with `sqlalchemy.url` overridden by `env.py` from environment variable.

### `backend/alembic/env.py`
Use async migration pattern:
```python
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool
from alembic import context
from app.core.config import settings
from app.db.session import Base
import app.models  # noqa: F401 — import all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
fileConfig(config.config_file_name)
target_metadata = Base.metadata

# Use run_migrations_online with asyncio runner
```

### `backend/Dockerfile`
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev libssl-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## 4. Files to Generate — Frontend

### `frontend/package.json` (key dependencies)
```json
{
  "name": "sms-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.1",
    "@tanstack/react-query": "^5.40.0",
    "@tanstack/react-table": "^8.17.3",
    "@tanstack/react-virtual": "^3.5.0",
    "zustand": "^4.5.2",
    "axios": "^1.7.2",
    "react-hook-form": "^7.51.5",
    "zod": "^3.23.8",
    "@hookform/resolvers": "^3.6.0",
    "lucide-react": "^0.383.0",
    "recharts": "^2.12.7",
    "@fullcalendar/react": "^6.1.14",
    "@fullcalendar/daygrid": "^6.1.14",
    "@fullcalendar/timegrid": "^6.1.14",
    "@fullcalendar/list": "^6.1.14",
    "@fullcalendar/interaction": "^6.1.14",
    "@dnd-kit/core": "^6.1.0",
    "@dnd-kit/sortable": "^8.0.0",
    "@tiptap/react": "^2.4.0",
    "@tiptap/starter-kit": "^2.4.0",
    "date-fns": "^3.6.0",
    "react-to-print": "^2.15.1",
    "html2canvas": "^1.4.1",
    "sonner": "^1.5.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.3.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "@radix-ui/react-popover": "^1.0.7",
    "@radix-ui/react-checkbox": "^1.0.4",
    "@radix-ui/react-switch": "^1.0.3",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-badge": "^1.0.0",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-label": "^2.0.2"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.4.5",
    "vite": "^5.2.12",
    "tailwindcss": "^3.4.4",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19",
    "@typescript-eslint/eslint-plugin": "^7.12.0",
    "@typescript-eslint/parser": "^7.12.0",
    "eslint": "^8.57.0",
    "eslint-plugin-react-hooks": "^4.6.2",
    "vitest": "^1.6.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.4.5"
  }
}
```

### `frontend/tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@api/*": ["./src/api/*"],
      "@components/*": ["./src/components/*"],
      "@pages/*": ["./src/pages/*"],
      "@hooks/*": ["./src/hooks/*"],
      "@store/*": ["./src/store/*"],
      "@types/*": ["./src/types/*"],
      "@utils/*": ["./src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### `frontend/vite.config.ts`
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@api': path.resolve(__dirname, './src/api'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@store': path.resolve(__dirname, './src/store'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
```

### `frontend/tailwind.config.ts`
Configure content paths, extend theme with custom colors (brand primary, sidebar background, status colors), enable dark mode via `class`.

### `frontend/src/api/axios.ts`
```typescript
import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { useAuthStore } from '@store/authStore';

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: attach access token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: auto-refresh on 401
let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => (error ? prom.reject(error) : prom.resolve(token!)));
  failedQueue = [];
};

api.interceptors.response.use(
  (response: AxiosResponse) => response.data,                     // unwrap envelope
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }
      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {}, { withCredentials: true });
        const newToken = data.data.accessToken;
        useAuthStore.getState().setAccessToken(newToken);
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error.response?.data || error);
  }
);

export default api;
```

### `frontend/src/store/authStore.ts`
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  avatarUrl?: string;
  isSuperAdmin: boolean;
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
  permissions: string[];   // format: "module:action"
  isAuthenticated: boolean;
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
      isAuthenticated: false,
      setAccessToken: (token) => set({ accessToken: token, isAuthenticated: true }),
      setUser: (user, school, permissions) =>
        set({ currentUser: user, schoolInfo: school, permissions, isAuthenticated: true }),
      logout: () => set({ accessToken: null, currentUser: null, schoolInfo: null, permissions: [], isAuthenticated: false }),
    }),
    {
      name: 'sms-auth',
      partialize: (state) => ({ currentUser: state.currentUser, schoolInfo: state.schoolInfo, permissions: state.permissions }),
    }
  )
);
```

### `frontend/src/store/academicYearStore.ts`
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AcademicYear {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
}

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

### `frontend/src/hooks/usePermission.ts`
```typescript
import { useAuthStore } from '@store/authStore';

export function usePermission() {
  const permissions = useAuthStore((s) => s.permissions);

  const hasPermission = (module: string, action: string): boolean => {
    const isSuperAdmin = useAuthStore.getState().currentUser?.isSuperAdmin;
    if (isSuperAdmin) return true;
    return permissions.includes(`${module}:${action}`);
  };

  const hasAnyPermission = (checks: Array<[string, string]>): boolean =>
    checks.some(([m, a]) => hasPermission(m, a));

  return { hasPermission, hasAnyPermission };
}
```

### `frontend/src/components/shared/PermissionGuard.tsx`
```typescript
import React from 'react';
import { usePermission } from '@hooks/usePermission';

interface Props {
  module: string;
  action: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const PermissionGuard: React.FC<Props> = ({ module, action, children, fallback = null }) => {
  const { hasPermission } = usePermission();
  return hasPermission(module, action) ? <>{children}</> : <>{fallback}</>;
};
```

### `frontend/src/routes/PrivateRoute.tsx`
```typescript
import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@store/authStore';

export const PrivateRoute: React.FC = () => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const location = useLocation();
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />;
  return <Outlet />;
};
```

### `frontend/src/routes/index.tsx`
Set up all routes with React.lazy + Suspense for code splitting. Include PrivateRoute wrappers and role-based redirects.

### `frontend/src/utils/constants.ts`
```typescript
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  SCHOOL_ADMIN: 'school_admin',
  PRINCIPAL: 'principal',
  VICE_PRINCIPAL: 'vice_principal',
  TEACHER: 'teacher',
  CLASS_TEACHER: 'class_teacher',
  ACCOUNTANT: 'accountant',
  LIBRARIAN: 'librarian',
  TRANSPORT_MANAGER: 'transport_manager',
  INVENTORY_MANAGER: 'inventory_manager',
  RECEPTIONIST: 'receptionist',
  PARENT: 'parent',
  STUDENT: 'student',
} as const;

export const MODULES = [
  'dashboard', 'schools', 'users', 'roles', 'academic_years', 'admissions',
  'classes', 'subjects', 'timetable', 'staff', 'leaves', 'payroll', 'students',
  'attendance', 'fees', 'exams', 'library', 'transport', 'inventory',
  'accounting', 'communication', 'calendar', 'homework', 'ptm',
  'reports', 'audit_logs', 'settings',
] as const;

export const ACTIONS = ['view', 'create', 'update', 'delete', 'export', 'approve', 'manage'] as const;

export const GENDER_OPTIONS = ['Male', 'Female', 'Other'];
export const BLOOD_GROUP_OPTIONS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
```

### `frontend/src/utils/formatters.ts`
```typescript
import { format, parseISO } from 'date-fns';

/** Format paise to rupee string: 150000 → "₹1,500.00" */
export const formatCurrency = (paise: number, currency = 'INR'): string => {
  const amount = paise / 100;
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency }).format(amount);
};

/** Format ISO date string to display date */
export const formatDate = (dateStr: string, fmt = 'dd/MM/yyyy'): string => {
  try { return format(parseISO(dateStr), fmt); } catch { return dateStr; }
};

/** Truncate text */
export const truncate = (text: string, length = 50): string =>
  text.length > length ? `${text.slice(0, length)}...` : text;

/** Generate initials from full name */
export const getInitials = (name: string): string =>
  name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
```

---

## 5. Docker Compose

### `docker-compose.yml`
```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: sms_db
      POSTGRES_USER: sms_user
      POSTGRES_PASSWORD: sms_pass
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
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q notifications,emails,reports,scheduled --concurrency=4
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    env_file: ./backend/.env
    depends_on:
      - backend

  celery_beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info --scheduler celery.beat:PersistentScheduler
    volumes:
      - ./backend:/app
    env_file: ./backend/.env
    depends_on:
      - backend

  flower:
    build: ./backend
    command: celery -A app.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"
    env_file: ./backend/.env
    depends_on:
      - redis

  frontend:
    image: node:20-alpine
    working_dir: /app
    command: sh -c "npm install && npm run dev -- --host"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000/api/v1

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    ports:
      - "80:80"
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  uploads:
```

### `nginx/nginx.conf`
```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:5173;
}

server {
    listen 80;
    server_name localhost;

    client_max_body_size 20M;
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # API routes
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # Pass subdomain as school slug
        proxy_set_header X-School-Slug $host;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check
    location /health {
        proxy_pass http://backend;
    }

    # Frontend (dev proxy)
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 6. `.gitignore`
```
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage

# Environment
.env
.env.*
!.env.example

# Alembic
alembic/versions/*.pyc

# Node
node_modules/
dist/
.cache/
*.local

# Uploads
backend/uploads/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# SSL
nginx/ssl/

# Docker
docker-compose.override.yml
```

---

## 7. Coding Standards (Apply Throughout ALL Phases)

### Backend
- Repository pattern: all DB queries in `/repositories/`, never in routes
- Service layer: all business logic in `/services/`
- Routes: validate input → call service → return response only
- **Response envelope** always:
  ```json
  { "success": true, "data": {}, "message": "Success", "pagination": null }
  ```
- HTTP status codes: 200, 201, 400, 401, 403, 404, 422, 500
- All datetimes stored as UTC
- All mutable tables include `updated_at` auto-updated via SQLAlchemy `onupdate=func.now()`
- **Soft delete**: `is_active=False` + `deleted_at` + `deleted_by`; never hard delete; all lists filter `WHERE is_active = TRUE`
- **Money**: stored as `INTEGER` (paise/cents); displayed as decimal in frontend
- snake_case Python; camelCase JSON responses
- Docstrings on all service functions
- `permission_required(module, action)` dependency on every protected route
- Audit log calls on all mutating operations (CREATE/UPDATE/DELETE)

### Frontend
- Every API call in `/api/*.ts`, never inline in components
- Custom hooks (e.g., `useStudents()`) wrap TanStack Query
- Error boundary at layout level
- Toast notifications (Sonner) for all async results
- Loading skeletons on all data-fetching components
- All forms: React Hook Form + Zod validation
- Page structure: `<PageHeader>` (title + breadcrumb + actions) → filter bar → data table → pagination
- `<PermissionGuard module="x" action="y">` for conditional rendering
- No `any` TypeScript types
- Dark mode via Tailwind `dark:` classes
- ARIA labels on interactive elements

---

## 8. Database Setup

Run the complete `Database_Schema.sql` against your PostgreSQL instance:
```bash
psql -U sms_user -d sms_db -f Database_Schema.sql
```

This creates all 67 tables, 70+ indexes, 22 enum types, and seeds:
- All permissions (~100 rows)
- Super Admin role and user (username: `superadmin`, password: `Admin@1234` — **change immediately**)
- Default grading scale (CBSE 10-point)

---

## 9. Deliverables Checklist

- [ ] Full monorepo folder structure created
- [ ] All backend boilerplate files written and working
- [ ] `GET /health` returns `{"status":"ok","database":"ok","redis":"ok"}`
- [ ] All frontend boilerplate files written
- [ ] Vite dev server starts without error
- [ ] Docker Compose brings up all 8 services
- [ ] Axios instance with JWT interceptor and auto-refresh configured
- [ ] Zustand stores: authStore, academicYearStore, notificationStore
- [ ] PrivateRoute and PermissionGuard components working
- [ ] Alembic initialized and env.py reads from `.env`
- [ ] README.md with setup instructions

---

## 10. README Content

Include:
- Project overview
- Prerequisites (Docker, Node 20, Python 3.12)
- Quick start with Docker Compose
- Manual setup (backend venv, pip install, alembic upgrade, run; frontend npm install, dev)
- Environment variables reference
- Default super admin credentials + change-password warning
- Development workflow and coding conventions link
