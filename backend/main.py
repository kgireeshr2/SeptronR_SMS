"""
School Management System — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.middleware import RequestLoggerMiddleware, SchoolContextMiddleware
from app.db.session import engine
from app.api.v1.router import api_router
from app.utils.response import error

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    import os
    from sqlalchemy import text
    import redis.asyncio as aioredis
    from app.db.session import async_session_factory

    logger.info(f"Starting {settings.APP_NAME} v1.0.0 [{settings.APP_ENV}]")

    # Verify DB connection
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✓ Database connection OK")
    except Exception as e:
        logger.error(f"✗ Database connection FAILED: {e}")

    # Verify Redis connection (optional)
    if settings.REDIS_ENABLED:
        try:
            r = aioredis.from_url(settings.REDIS_URL)
            await r.ping()
            await r.aclose()
            logger.info("✓ Redis connection OK")
        except Exception as e:
            logger.error(f"✗ Redis connection FAILED: {e}")
    else:
        logger.warning("⚠ Redis is disabled via REDIS_ENABLED=false")

    # Create uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"✓ Upload directory ready: {settings.UPLOAD_DIR}")

    yield

    # Shutdown
    await engine.dispose()
    logger.info("✓ Database engine disposed")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Exception Handlers ────────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    encoded_errors = jsonable_encoder(
        exc.errors(),
        custom_encoder={bytes: lambda value: value.decode("utf-8", errors="replace")},
    )
    return JSONResponse(
        status_code=422,
        content=error(message="Validation error", data=encoded_errors),
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Convert DB unique/FK constraint violations to 409 Conflict."""
    logger.warning(f"IntegrityError on {request.method} {request.url.path}: {exc.orig}")
    # Extract a user-friendly message from the DB error
    orig_msg = str(exc.orig)
    if "Violation of UNIQUE KEY" in orig_msg or "duplicate key" in orig_msg.lower():
        detail = "A record with the same unique key already exists."
    elif "FOREIGN KEY" in orig_msg or "foreign key" in orig_msg.lower():
        detail = "Referenced record does not exist."
    else:
        detail = "Database constraint violation."
    return JSONResponse(
        status_code=409,
        content=error(message=detail),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=error(message="Internal server error"),
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
    """Returns DB and Redis connectivity status. No authentication required."""
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

    if settings.REDIS_ENABLED:
        try:
            r = aioredis.from_url(settings.REDIS_URL)
            await r.ping()
            await r.aclose()
            redis_ok = True
        except Exception:
            pass
    else:
        redis_ok = True

    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "disabled" if not settings.REDIS_ENABLED else ("ok" if redis_ok else "error"),
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }
