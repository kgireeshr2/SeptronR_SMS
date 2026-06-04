"""
Database-agnostic type aliases — replaces sqlalchemy.dialects.postgresql types.
Works transparently with SQL Server, PostgreSQL, SQLite.
"""
from sqlalchemy import Uuid, JSON
from sqlalchemy import Enum as _SAEnum


# ── UUID ──────────────────────────────────────────────────────────────────────
# Uuid(as_uuid=True) → UNIQUEIDENTIFIER on MSSQL, UUID on PG, CHAR(32) on SQLite
UUID = Uuid


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
