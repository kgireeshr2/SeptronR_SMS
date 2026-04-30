"""Audit log utility — Phase 18.

Usage:
    from app.utils.audit import audit_log

    async with audit_log(db, request, school_id=school_id) as ctx:
        ctx.module = "fees"
        ctx.action = "create"
        ctx.record_type = "FeeRecord"
        ctx.record_id = str(new_record.id)
        ctx.new_values = {"amount": 1000}

The context manager writes the log entry after the `async with` block completes
successfully (no exception). If an exception occurs, no log is written (the
caller should handle rollback).
"""
from __future__ import annotations
import contextlib
from typing import Optional, Any
from uuid import UUID
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.audit_repository as audit_repo


class _AuditContext:
    def __init__(self) -> None:
        self.module: str = ""
        self.action: str = ""
        self.record_type: Optional[str] = None
        self.record_id: Optional[str] = None
        self.record_description: Optional[str] = None
        self.old_values: Optional[dict] = None
        self.new_values: Optional[dict] = None


@contextlib.asynccontextmanager
async def audit_log(
    db: AsyncSession,
    request: Optional[Request],
    *,
    school_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    role_snapshot: Optional[str] = None,
):
    """Async context manager that writes an audit log entry on success."""
    ctx = _AuditContext()
    yield ctx
    if not ctx.module or not ctx.action:
        return
    ip = None
    ua = None
    if request:
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
    await audit_repo.write_log(
        db,
        school_id=school_id,
        user_id=user_id,
        user_name=user_name,
        role_snapshot=role_snapshot,
        module=ctx.module,
        action=ctx.action,
        record_type=ctx.record_type,
        record_id=ctx.record_id,
        record_description=ctx.record_description,
        old_values=ctx.old_values,
        new_values=ctx.new_values,
        ip_address=ip,
        user_agent=ua,
    )
