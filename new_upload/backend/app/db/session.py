import ssl

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# asyncpg does not understand libpq's `sslmode` query param (that's psycopg2).
# Managed Postgres providers (Aiven, etc.) hand out URLs ending in
# `?sslmode=require`, so translate it into an asyncpg `ssl` connect_arg. We use a
# context that encrypts but skips CA verification (equivalent to sslmode=require)
# to avoid having to distribute the provider's CA cert.
_url = make_url(settings.DATABASE_URL)
_connect_args: dict = {}
_query = dict(_url.query)
_sslmode = _query.pop("sslmode", None)
if _sslmode and _sslmode != "disable":
    if settings.DB_SSL_ROOT_CERT or settings.DB_SSL_VERIFY:
        # Verified TLS — authenticate the DB server (sslmode=verify-full equivalent),
        # preventing a man-in-the-middle on the database link. Provide the provider CA
        # via DB_SSL_ROOT_CERT (e.g. the Aiven CA) when it isn't in the system trust store.
        _ctx = ssl.create_default_context(cafile=(settings.DB_SSL_ROOT_CERT or None))
        _ctx.check_hostname = True
        _ctx.verify_mode = ssl.CERT_REQUIRED
    else:
        # Encrypt WITHOUT verification (no CA distributed). Acceptable for dev; set
        # DB_SSL_VERIFY=true (and DB_SSL_ROOT_CERT if needed) to harden in production.
        import logging as _logging
        _logging.getLogger("app.db.session").warning(
            "DB TLS is encrypt-without-verify (DB_SSL_VERIFY=false) — server identity is NOT authenticated."
        )
        _ctx = ssl.create_default_context()
        _ctx.check_hostname = False
        _ctx.verify_mode = ssl.CERT_NONE
    _connect_args["ssl"] = _ctx
    _url = _url.set(query=_query)

engine = create_async_engine(
    _url,
    echo=settings.DEBUG,
    pool_pre_ping=True,      # asyncpg supports this correctly
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,       # recycle connections every 30 min (cloud idle timeouts)
    connect_args=_connect_args,
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
