from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# pool_pre_ping is broken with aiomysql (ping() missing 'reconnect' arg)
_is_mysql = settings.DATABASE_URL.startswith("mysql")

_engine_kwargs = dict(
    echo=settings.DEBUG,
    pool_pre_ping=not _is_mysql,
    pool_size=3,
    max_overflow=2,
    pool_recycle=1800,       # recycle connections every 30 min
    pool_timeout=30,
)

if _is_mysql:
    _engine_kwargs["connect_args"] = {
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30,
    }

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

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
