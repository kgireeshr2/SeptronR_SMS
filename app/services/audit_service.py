"""Service — Phase 18: Audit Logs."""
from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.audit_repository as repo
from app.schemas.phase18 import AuditLogFilter


async def list_logs(
    db: AsyncSession,
    school_id: Optional[str],
    filters: AuditLogFilter,
    limit: int = 100,
    offset: int = 0,
):
    return await repo.list_logs(
        db,
        school_id=school_id,
        module=filters.module,
        action=filters.action,
        user_id=str(filters.user_id) if filters.user_id else None,
        record_type=filters.record_type,
        date_from=filters.date_from,
        date_to=filters.date_to,
        limit=limit,
        offset=offset,
    )

