"""Repository — Phase 18: Audit Logs (append-only)."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def list_logs(
    db: AsyncSession,
    school_id: Optional[str],
    module: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    record_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[AuditLog]:
    q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if school_id:
        q = q.where(AuditLog.school_id == school_id)
    if module:
        q = q.where(AuditLog.module == module)
    if action:
        q = q.where(AuditLog.action == action)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    if record_type:
        q = q.where(AuditLog.record_type == record_type)
    if date_from:
        q = q.where(AuditLog.created_at >= date_from)
    if date_to:
        q = q.where(AuditLog.created_at <= date_to)
    q = q.limit(limit).offset(offset)
    r = await db.execute(q)
    return list(r.scalars().all())


async def write_log(
    db: AsyncSession,
    *,
    school_id: Optional[str],
    user_id: Optional[str],
    user_name: Optional[str],
    role_snapshot: Optional[str],
    module: str,
    action: str,
    record_type: Optional[str] = None,
    record_id: Optional[str] = None,
    record_description: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    obj = AuditLog(
        id=uuid.uuid4(),
        school_id=school_id,
        user_id=user_id,
        user_name=user_name,
        role_snapshot=role_snapshot,
        module=module,
        action=action,
        record_type=record_type,
        record_id=record_id,
        record_description=record_description,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(obj)
    await db.flush()
    return obj

