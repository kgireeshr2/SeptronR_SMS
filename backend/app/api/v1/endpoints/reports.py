from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.services.report_service import REPORT_REGISTRY, run_report

reports_router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportRequest(BaseModel):
    report_id: str
    year_id: Optional[str] = None
    filters: Dict[str, Any] = {}


@reports_router.get("/available")
async def list_available_reports(
    _: User = Depends(permission_required("reports", "view")),
):
    """Return all registered report IDs with their module group."""
    groups: Dict[str, List[str]] = {
        "student": [],
        "staff": [],
        "finance": [],
        "attendance": [],
        "other": [],
    }
    mappings = {
        "student_list": "student",
        "student_attendance": "attendance",
        "low_attendance": "attendance",
        "fee_defaulters": "finance",
        "fee_collection": "finance",
        "income_expense": "finance",
        "monthly_pl": "finance",
        "staff_list": "staff",
        "staff_attendance": "staff",
    }
    for report_id in REPORT_REGISTRY:
        group = mappings.get(report_id, "other")
        groups[group].append(report_id)
    return groups


@reports_router.post("/generate")
async def generate_report(
    req: ReportRequest,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(permission_required("reports", "view")),
):
    if req.report_id not in REPORT_REGISTRY:
        raise HTTPException(400, f"Unknown report: {req.report_id}. Available: {list(REPORT_REGISTRY.keys())}")
    rows = await run_report(req.report_id, school_id, req.year_id, req.filters, db)
    return {"report_id": req.report_id, "total_rows": len(rows), "data": rows}


@reports_router.get("/{report_id}")
async def get_report(
    report_id: str,
    year_id: Optional[str] = Query(None),
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(permission_required("reports", "view")),
    # Common filter query params
    class_id: Optional[str] = Query(None),
    section_id: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    threshold_pct: Optional[int] = Query(None),
    department_id: Optional[str] = Query(None),
):
    filters = {k: v for k, v in {
        "class_id": class_id,
        "section_id": section_id,
        "gender": gender,
        "status": status,
        "month": month,
        "year": year,
        "date_from": date_from,
        "date_to": date_to,
        "threshold_pct": threshold_pct,
        "department_id": department_id,
    }.items() if v is not None}

    if report_id not in REPORT_REGISTRY:
        raise HTTPException(400, f"Unknown report: {report_id}")
    rows = await run_report(report_id, school_id, year_id, filters, db)
    return {"report_id": report_id, "total_rows": len(rows), "data": rows}

