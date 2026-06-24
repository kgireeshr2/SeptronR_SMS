"""Run async DB coroutines from inside (sync) Celery tasks.

The app uses async SQLAlchemy (asyncpg). Celery prefork workers are synchronous and
each task may run on a fresh event loop, so we create a short-lived engine per call
(NullPool) bound to that loop and dispose it afterwards — avoiding the
"future attached to a different loop" errors you get from sharing the app's engine.
"""
from __future__ import annotations

import asyncio
import ssl
from typing import Any, Awaitable, Callable

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _build_engine():
    url = make_url(settings.DATABASE_URL)
    connect_args: dict = {}
    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    if sslmode and sslmode != "disable":
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx
        url = url.set(query=query)
    return create_async_engine(url, poolclass=NullPool, connect_args=connect_args)


def run_async(coro_fn: Callable[[AsyncSession], Awaitable[Any]]) -> Any:
    """Open a worker-local async session, run `coro_fn(session)`, commit, return result.

    `coro_fn` receives an AsyncSession and is responsible for its own queries; this
    helper handles engine lifecycle, commit/rollback, and loop creation.
    """
    async def _runner() -> Any:
        engine = _build_engine()
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with factory() as session:
                try:
                    result = await coro_fn(session)
                    await session.commit()
                    return result
                except Exception:
                    await session.rollback()
                    raise
        finally:
            await engine.dispose()

    return asyncio.run(_runner())
