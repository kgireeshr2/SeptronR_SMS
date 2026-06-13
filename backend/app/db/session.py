from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


_is_mysql = settings.DATABASE_URL.startswith("mysql")

# pool_pre_ping validates each pooled connection before use and transparently
# replaces ones the server has dropped — essential against managed/shared MySQL
# hosts that reset idle or remote connections ([Errno 104] reset by peer).
_engine_kwargs = dict(
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=2,
    pool_recycle=1800,       # recycle connections every 30 min
    pool_timeout=30,
)

if _is_mysql:
    _engine_kwargs["connect_args"] = {
        "connect_timeout": 10,
    }

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)


# ── asyncmy pre-ping compatibility fix ──────────────────────────────────────
# SQLAlchemy's pymysql do_ping inspects pymysql's Connection.ping signature to
# decide whether to call ping() with no args. When pymysql defaults reconnect
# to False, it calls ping() with no args — but the asyncmy adapter's
# ping(self, reconnect) requires that positional arg, raising
# "ping() missing required positional argument: 'reconnect'" on EVERY checkout.
# Forcing _send_false_to_ping=True makes do_ping call ping(False), which asyncmy
# accepts — so pool_pre_ping works correctly on asyncmy. (_send_false_to_ping is
# a non-data memoized_property, so setting it on the instance shadows it.)
if _is_mysql:
    try:
        engine.sync_engine.dialect._send_false_to_ping = True
    except Exception:
        pass

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
