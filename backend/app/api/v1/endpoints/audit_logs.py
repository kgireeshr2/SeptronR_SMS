"""API Endpoints — Phase 18: Audit Logs."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, permission_required
from app.models.auth import User
from app.schemas.phase18 import AuditLogResponse, AuditLogFilter
import app.services.audit_service as svc

audit_router = APIRouter(prefix="/audit-logs", tags=["audit"])


def _resolve_school_id(request: Request, current_user: User) -> Optional[str]:
    """Return school_id from header, query param, or user's own school_id. None for super admin."""
    sid = (
        request.headers.get("X-School-Id")
        or request.query_params.get("school_id")
        or (str(current_user.school_id) if current_user.school_id else None)
    )
    return sid or None


@audit_router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    request: Request,
    module: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[UUID] = None,
    record_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("audit", "view")),
):
    school_id = _resolve_school_id(request, current_user)
    filters = AuditLogFilter(
        module=module,
        action=action,
        user_id=user_id,
        record_type=record_type,
        date_from=date_from,
        date_to=date_to,
    )
    return await svc.list_logs(db, school_id, filters, limit=limit, offset=offset)


@audit_router.get("/modules")
async def list_modules(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("audit", "view")),
):
    """Return distinct module names that have audit entries."""
    school_id = _resolve_school_id(request, current_user)
    from sqlalchemy import text
    if school_id:
        rows = await db.execute(
            text("SELECT DISTINCT module FROM audit_logs WHERE school_id = :sid ORDER BY module"),
            {"sid": school_id},
        )
    else:
        rows = await db.execute(text("SELECT DISTINCT module FROM audit_logs ORDER BY module"))
    return [r["module"] for r in rows.mappings().all()]


@audit_router.get("/export")
async def export_audit_logs(
    request: Request,
    module: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(default=1000, le=5000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("audit", "view")),
):
    """Export audit logs as CSV."""
    import csv
    import io
    from fastapi.responses import StreamingResponse as SR
    school_id = _resolve_school_id(request, current_user)
    filters = AuditLogFilter(module=module, action=action, date_from=date_from, date_to=date_to)
    logs = await svc.list_logs(db, school_id, filters, limit=limit, offset=0)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "module", "action", "user_name", "record_type", "record_id", "ip_address", "created_at"])
    for log in logs:
        w.writerow([log.id, log.module, log.action, log.user_name, log.record_type, log.record_id, log.ip_address, log.created_at])
    buf.seek(0)
    return SR(iter([buf.getvalue().encode()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit_logs.csv"})
