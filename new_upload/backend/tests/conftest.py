import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.db.session import Base, get_db
from app.core.config import settings
from app.core.security import hash_password
import app.models  # noqa: F401 — ensures ALL models are in Base.metadata for create_all

# Override DB URL to use test database (MSSQL odbc_connect format)
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "Database%3Dsms%3B", "Database%3Dsms_test%3B"
)

# NullPool: no connection re-use across event loops — critical for aioodbc + anyio
test_engine = create_async_engine(
    TEST_DATABASE_URL, echo=False, poolclass=NullPool
)
TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the event loop for the whole test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Create test database tables (idempotent, no drop to avoid circular FKs)."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Note: we intentionally skip drop_all — the staff<->departments circular FK
    # prevents clean topological sort for DROP.  Tables persist in sms_test DB
    # which is fine since create_all is idempotent (checkfirst=True by default).
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_db):
    """Provide a transactional test DB session that rolls back after each test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


def _make_app_client():
    """Return a configured (app, ASGITransport) pair with Celery eager mode."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from main import app as _app
    from app.tasks.celery_app import celery as celery_app
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=False)
    return _app


@pytest_asyncio.fixture
async def async_client(db_session):
    """Provide an async HTTP client with overridden DB dependency (function-scoped)."""
    app = _make_app_client()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session")
async def session_http_client(setup_db):
    """Session-scoped HTTP client for creating shared fixture data once per session.

    Uses its own DB session (not overriding get_db) so that the app talks to
    the test database directly via the configured TEST_DATABASE_URL.
    The test database URL is set globally via the app settings override below.
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Patch the DATABASE_URL in the app settings to point at sms_test
    from app.core.config import settings as app_settings
    _orig_url = app_settings.DATABASE_URL
    app_settings.DATABASE_URL = TEST_DATABASE_URL

    from main import app as _app
    from app.tasks.celery_app import celery as celery_app
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=False)

    # Override the DB engine in the app's session module to use the test engine
    import app.db.session as db_session_module
    _orig_engine = db_session_module.engine
    _orig_session_factory = db_session_module.async_session_factory
    db_session_module.engine = test_engine
    db_session_module.async_session_factory = TestingSessionLocal

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    _app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    _app.dependency_overrides.clear()
    db_session_module.engine = _orig_engine
    db_session_module.async_session_factory = _orig_session_factory
    app_settings.DATABASE_URL = _orig_url


async def create_test_superadmin(username: str, email: str, password: str = "Admin@1234") -> None:
    """Create (or re-hash) a super-admin user in sms_test."""
    from sqlalchemy import text as sa_text, update as sa_update
    pw_hash = hash_password(password)
    async with TestingSessionLocal() as session:
        result = await session.execute(
            sa_text("SELECT id FROM users WHERE email = :email"),
            {"email": email}
        )
        existing = result.fetchone()
        if not existing:
            from app.models.auth import User
            user = User(
                id=uuid.uuid4(),
                username=username,
                email=email,
                password_hash=pw_hash,
                is_active=True,
                is_verified=True,
                is_super_admin=True,
            )
            session.add(user)
        else:
            # Update password hash so login is guaranteed to work
            await session.execute(
                sa_text("UPDATE users SET password_hash = :ph, is_active = 1, is_verified = 1, is_super_admin = 1 WHERE email = :email"),
                {"ph": pw_hash, "email": email}
            )
        await session.commit()
