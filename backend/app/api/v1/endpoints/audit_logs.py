"""API Endpoints — Phase 18: Audit Logs."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_school_id, permission_required
from app.schemas.phase18 import AuditLogResponse, AuditLogFilter
import app.services.audit_service as svc

audit_router = APIRouter(prefix="/audit-logs", tags=["audit"])


@audit_router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    module: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[UUID] = None,
    record_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("audit", "view")),
):
    filters = AuditLogFilter(
        module=module,
        action=action,
        user_id=user_id,
        record_type=record_type,
        date_from=date_from,
        date_to=date_to,
    )
    return await svc.list_logs(db, school_id, filters, limit=limit, offset=offset)

