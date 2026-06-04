from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user, get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.models.staff import Staff
from app.repositories.staff_repository import StaffRepository
from app.repositories.payroll_repository import PayrollRepository
from app.services.staff_service import StaffService
from app.schemas.phase6 import (
    PayrollGenerateRequest,
    PayrollEntryCreate,
    PayrollUpdate,
    PayrollMarkPaidRequest,
    PayrollResponse,
)

router = APIRouter()


# ===================== Payroll Endpoints =====================
@router.get("", response_model=List[PayrollResponse])
async def list_payroll(
    academic_year_id: Optional[str] = Query(None),
    staff_id: Optional[str] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    is_paid: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("payroll", "view")),
    db: AsyncSession = Depends(get_db),
):
    """List payroll entries with filters"""
    payroll_list = await PayrollRepository.get_payroll_list(
        db,
        school_id,
        academic_year_id=academic_year_id,
        staff_id=staff_id,
        month=month,
        year=year,
        is_paid=is_paid,
        skip=skip,
        limit=limit,
    )
    
    # Enrich with staff name and employee_id
    result = []
    for payroll in payroll_list:
        staff = await StaffRepository.get_staff_by_id(db, payroll.staff_id, school_id)
        
        result.append({
            **payroll.__dict__,
            "staff_name": f"{staff.first_name} {staff.last_name}" if staff else None,
            "employee_id": staff.employee_id if staff else None,
        })
    
    return result


@router.post("/generate", response_model=List[PayrollResponse], status_code=status.HTTP_201_CREATED)
async def generate_payroll(
    generate_data: PayrollGenerateRequest,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("payroll", "generate")),
    db: AsyncSession = Depends(get_db),
):
    """Generate payroll for a month"""
    staff_service = StaffService(db)
    
    try:
        payroll_entries = await staff_service.generate_monthly_payroll(
            generate_data.month,
            generate_data.year,
            generate_data.academic_year_id,
            school_id,
            generate_data.staff_ids,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Enrich with staff details
    result = []
    for payroll in payroll_entries:
        staff = await StaffRepository.get_staff_by_id(db, payroll.staff_id, school_id)
        
        result.append({
            **payroll.__dict__,
            "staff_name": f"{staff.first_name} {staff.last_name}" if staff else None,
            "employee_id": staff.employee_id if staff else None,
        })
    
    return result


@router.get("/{payroll_id}", response_model=PayrollResponse)
async def get_payroll(
    payroll_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("payroll", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get payroll entry by ID"""
    payroll = await PayrollRepository.get_payroll(db, payroll_id, school_id)
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll entry not found")
    
    # Enrich with staff details
    staff = await StaffRepository.get_staff_by_id(db, payroll.staff_id, school_id)
    
    return {
        **payroll.__dict__,
        "staff_name": f"{staff.first_name} {staff.last_name}" if staff else None,
        "employee_id": staff.employee_id if staff else None,
    }


@router.put("/{payroll_id}", response_model=PayrollResponse)
async def update_payroll(
    payroll_id: str,
    payroll_data: PayrollUpdate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("payroll", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Update payroll entry (draft only)"""
    payroll = await PayrollRepository.get_payroll(db, payroll_id, school_id)
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll entry not found")
    
    if payroll.is_paid:
        raise HTTPException(status_code=400, detail="Cannot edit paid payroll")
    
    update_dict = payroll_data.model_dump(exclude_unset=True)
    updated_payroll = await PayrollRepository.update_payroll(db, payroll, update_dict)
    
    # Enrich with staff details
    staff = await StaffRepository.get_staff_by_id(db, updated_payroll.staff_id, school_id)
    
    return {
        **updated_payroll.__dict__,
        "staff_name": f"{staff.first_name} {staff.last_name}" if staff else None,
        "employee_id": staff.employee_id if staff else None,
    }


@router.delete("/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payroll(
    payroll_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("payroll", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete draft payroll entry"""
    payroll = await PayrollRepository.get_payroll(db, payroll_id, school_id)
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll entry not found")
    
    try:
        await PayrollRepository.delete_payroll(db, payroll)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/mark-paid", response_model=dict)
async def mark_payroll_as_paid(
    mark_paid_data: PayrollMarkPaidRequest,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("payroll", "mark_paid")),
    db: AsyncSession = Depends(get_db),
):
    """Mark multiple payroll entries as paid"""
    count = await PayrollRepository.bulk_mark_paid(
        db,
        mark_paid_data.payroll_ids,
        school_id,
        mark_paid_data.payment_date,
        mark_paid_data.payment_method,
    )
    
    # TODO: Send payslip emails via Celery
    # for payroll_id in mark_paid_data.payroll_ids:
    #     await send_payslip_email.delay(payroll_id)
    
    return {
        "message": f"{count} payroll entries marked as paid",
        "count": count,
    }


@router.get("/{payroll_id}/slip")
async def download_payslip(
    payroll_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download payslip PDF (staff can download own payslip)"""
    payroll = await PayrollRepository.get_payroll(db, payroll_id, school_id)
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll entry not found")
    
    # Check permission (admin or self)
    staff = await StaffRepository.get_staff_by_user_id(db, str(current_user.id), school_id)
    # TODO: Check if user has permission to view all payroll or only own
    # For now, allow staff to view only their own payslip
    if staff and payroll.staff_id != str(staff.id):
        # Check if user has admin permission
        # If not, raise 403
        pass
    
    # TODO: Generate PDF using Jinja2 template and WeasyPrint
    # For now, return placeholder
    
    raise HTTPException(
        status_code=501,
        detail="PDF generation not implemented yet. Use GET /payroll/{id} to view payroll details.",
    )


@router.get("/staff/{staff_id}", response_model=List[PayrollResponse])
async def get_staff_payroll_history(
    staff_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=100),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payroll history for a staff member (staff can view own history)"""
    # Check permission (admin or self)
    requesting_staff = await StaffRepository.get_staff_by_user_id(db, str(current_user.id), school_id)
    if requesting_staff and str(requesting_staff.id) != staff_id:
        # Check if user has admin permission
        # TODO: Implement proper permission check
        pass
    
    # Get staff to verify existence
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    payroll_history = await PayrollRepository.get_staff_payroll_history(
        db, staff_id, school_id, skip=skip, limit=limit
    )
    
    # Enrich with staff details
    result = []
    for payroll in payroll_history:
        result.append({
            **payroll.__dict__,
            "staff_name": f"{staff.first_name} {staff.last_name}",
            "employee_id": staff.employee_id,
        })
    
    return result


# ===================== Staff Self-Service Endpoints =====================
@router.get("/my/history", response_model=List[PayrollResponse])
async def get_my_payroll_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(12, ge=1, le=100),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's payroll history (staff self-service)"""
    # Get staff record for current user
    staff = await StaffRepository.get_staff_by_user_id(db, str(current_user.id), school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff record not found for user")
    
    payroll_history = await PayrollRepository.get_staff_payroll_history(
        db, str(staff.id), school_id, skip=skip, limit=limit
    )
    
    # Enrich with staff details
    result = []
    for payroll in payroll_history:
        result.append({
            **payroll.__dict__,
            "staff_name": f"{staff.first_name} {staff.last_name}",
            "employee_id": staff.employee_id,
        })
    
    return result


# ===================== Payslip PDF Download =====================
@router.get("/{payroll_id}/payslip/pdf")
async def download_payslip_pdf(
    payroll_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("payroll", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Download payslip as PDF for a payroll entry."""
    import io
    from app.services.pdf_service import generate_payslip_pdf
    from app.repositories.school_repository import SchoolRepository

    payroll_entry = await PayrollRepository.get_payroll(db, payroll_id, school_id)
    if not payroll_entry:
        raise HTTPException(status_code=404, detail="Payroll entry not found")

    staff = await StaffRepository.get_staff_by_id(db, str(payroll_entry.staff_id), school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)
    school_name = school.name if school else "School"

    # Build allowances and deductions from JSON fields
    allowances = []
    deductions = []
    if payroll_entry.allowances:
        raw = payroll_entry.allowances
        if isinstance(raw, dict):
            for k, v in raw.items():
                allowances.append({"name": k, "amount": int(v * 100)})
        elif isinstance(raw, list):
            allowances = [{"name": a.get("name", "Allowance"), "amount": int((a.get("amount", 0)) * 100)} for a in raw]
    if payroll_entry.deductions:
        raw = payroll_entry.deductions
        if isinstance(raw, dict):
            for k, v in raw.items():
                deductions.append({"name": k, "amount": int(v * 100)})
        elif isinstance(raw, list):
            deductions = [{"name": d.get("name", "Deduction"), "amount": int((d.get("amount", 0)) * 100)} for d in raw]

    pdf_data = {
        "school_name": school_name,
        "school_address": getattr(school, "address", None),
        "employee_name": f"{staff.first_name} {staff.last_name}",
        "employee_id": staff.employee_id,
        "designation": getattr(staff, "designation", "—") or "—",
        "department": getattr(staff, "department", None),
        "month": payroll_entry.month,
        "year": payroll_entry.year,
        "payment_date": getattr(payroll_entry, "payment_date", None),
        "basic_salary": int(payroll_entry.basic_salary * 100) if payroll_entry.basic_salary else 0,
        "allowances": allowances,
        "deductions": deductions,
        "net_salary": int(payroll_entry.net_salary * 100) if payroll_entry.net_salary else 0,
        "bank_name": getattr(staff, "bank_name", None),
        "bank_account_no": getattr(staff, "bank_account_no", None),
    }

    pdf_bytes = generate_payslip_pdf(pdf_data)
    filename = f"payslip_{staff.employee_id}_{payroll_entry.month}_{payroll_entry.year}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

