"""
Database-agnostic type aliases — replaces sqlalchemy.dialects.postgresql types.
Works transparently with SQL Server, PostgreSQL, MySQL, SQLite.
"""
import uuid as _uuid

from sqlalchemy import Uuid, JSON
from sqlalchemy import Enum as _SAEnum
from sqlalchemy.types import TypeDecorator


# ── UUID ──────────────────────────────────────────────────────────────────────
# Uuid(as_uuid=True) → UNIQUEIDENTIFIER on MSSQL, native UUID on PG, CHAR(32) on
# MySQL/SQLite. On non-native backends SQLAlchemy's Uuid bind processor calls
# value.hex, which fails with "'str' object has no attribute 'hex'" when the app
# passes a string UUID (e.g. str(user.id) from a JWT). asyncpg silently accepted
# strings; MySQL/asyncmy does not. This TypeDecorator coerces str → uuid.UUID on
# bind so every query that filters/updates by a UUID column works regardless of
# whether the caller passed a UUID object or a string. DDL is unchanged (still
# renders via the Uuid impl), so it matches already-created tables.
class UUID(TypeDecorator):  # noqa: N801
    impl = Uuid
    cache_ok = True

    def __init__(self, as_uuid: bool = True, **kwargs):
        super().__init__(as_uuid=as_uuid, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is not None and not isinstance(value, _uuid.UUID):
            value = _uuid.UUID(str(value))
        return value


# ── JSONB → JSON ─────────────────────────────────────────────────────────────
# SQL Server stores JSON as NVARCHAR(MAX); behaviour is equivalent for our use
JSONB = JSON


# ── ENUM: strip create_type (PostgreSQL-only kwarg) ──────────────────────────
def ENUM(*args, **kwargs):
    """
    Drop-in replacement for sqlalchemy.dialects.postgresql.ENUM.
    Removes PostgreSQL-specific 'create_type' kwarg and delegates to
    SQLAlchemy's generic Enum which renders VARCHAR+CHECK on SQL Server.
    """
    kwargs.pop("create_type", None)   # PG-only — not accepted by generic Enum
    kwargs.pop("schema", None)        # PG-only schema for type
    return _SAEnum(*args, **kwargs)


# ── ARRAY → JSON list ────────────────────────────────────────────────────────
# SQL Server has no native ARRAY type; store lists as JSON
class ARRAY(JSON):  # noqa: N801
    """
    Maps PostgreSQL ARRAY(item_type) to JSON on SQL Server.
    Usage:  ARRAY(String)  →  just stores as JSON list.
    The item_type arg is accepted but ignored.
    """
    def __init__(self, item_type=None, **kwargs):  # noqa: ANN001
        super().__init__(**kwargs)
