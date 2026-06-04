from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.models.staff import LeaveStatus
from app.repositories.staff_repository import StaffRepository
from app.repositories.leave_repository import LeaveRepository
from app.services.staff_service import StaffService
from app.schemas.phase6 import (
    LeaveTypeCreate,
    LeaveTypeUpdate,
    LeaveTypeResponse,
    LeaveApplicationCreate,
    LeaveApplicationUpdate,
    LeaveApplicationReview,
    LeaveApplicationResponse,
    LeaveBalanceResponse,
    LeaveAllocationRequest,
    LeaveBalanceUpdateRequest,
    LeaveStatistics,
)

router = APIRouter()


# ===================== Leave Type Endpoints =====================
@router.get("/types", response_model=List[LeaveTypeResponse])
async def list_leave_types(
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "view_types")),
    db: AsyncSession = Depends(get_db),
):
    """List all leave types"""
    leave_types = await LeaveRepository.get_leave_types(
        db, school_id, is_active=is_active, skip=skip, limit=limit
    )
    return leave_types


@router.post("/types", response_model=LeaveTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_type(
    leave_type_data: LeaveTypeCreate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "create_types")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new leave type"""
    leave_type = await LeaveRepository.create_leave_type(
        db, leave_type_data.model_dump(), school_id
    )
    return leave_type


@router.get("/types/{leave_type_id}", response_model=LeaveTypeResponse)
async def get_leave_type(
    leave_type_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "view_types")),
    db: AsyncSession = Depends(get_db),
):
    """Get leave type by ID"""
    leave_type = await LeaveRepository.get_leave_type(db, leave_type_id, school_id)
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    return leave_type


@router.put("/types/{leave_type_id}", response_model=LeaveTypeResponse)
async def update_leave_type(
    leave_type_id: str,
    leave_type_data: LeaveTypeUpdate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "edit_types")),
    db: AsyncSession = Depends(get_db),
):
    """Update leave type"""
    leave_type = await LeaveRepository.get_leave_type(db, leave_type_id, school_id)
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    
    update_dict = leave_type_data.model_dump(exclude_unset=True)
    updated_leave_type = await LeaveRepository.update_leave_type(db, leave_type, update_dict)
    return updated_leave_type


@router.delete("/types/{leave_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_leave_type(
    leave_type_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "delete_types")),
    db: AsyncSession = Depends(get_db),
):
    """Delete (deactivate) leave type"""
    leave_type = await LeaveRepository.get_leave_type(db, leave_type_id, school_id)
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    
    await LeaveRepository.update_leave_type(db, leave_type, {"is_active": False})


# ===================== Leave Application Endpoints =====================
@router.get("/applications", response_model=List[LeaveApplicationResponse])
async def list_leave_applications(
    staff_id: Optional[str] = Query(None),
    status: Optional[LeaveStatus] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "view")),
    db: AsyncSession = Depends(get_db),
):
    """List all leave applications (admin view)"""
    leaves = await LeaveRepository.get_staff_leaves(
        db,
        school_id,
        staff_id=staff_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )
    
    # Enrich with staff name, leave type name
    result = []
    for leave in leaves:
        staff = await StaffRepository.get_staff_by_id(db, leave.staff_id, school_id)
        leave_type = await LeaveRepository.get_leave_type(db, leave.leave_type_id, school_id)
        
        result.append({
            **leave.__dict__,
            "staff_name": f"{staff.first_name} {staff.last_name}" if staff else None,
            "leave_type_name": leave_type.name if leave_type else None,
        })
    
    return result


@router.get("/applications/my", response_model=List[LeaveApplicationResponse])
async def list_my_leave_applications(
    status: Optional[LeaveStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's leave applications (staff self-view)"""
    # Get staff record for current user
    staff = await StaffRepository.get_staff_by_user_id(db, str(current_user.id), school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff record not found for user")
    
    leaves = await LeaveRepository.get_staff_leaves(
        db,
        school_id,
        staff_id=str(staff.id),
        status=status,
        skip=skip,
        limit=limit,
    )
    
    # Enrich with leave type name
    result = []
    for leave in leaves:
        leave_type = await LeaveRepository.get_leave_type(db, leave.leave_type_id, school_id)
        
        result.append({
            **leave.__dict__,
            "staff_name": f"{staff.first_name} {staff.last_name}",
            "leave_type_name": leave_type.name if leave_type else None,
        })
    
    return result


@router.post("/applications", response_model=LeaveApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_leave(
    leave_data: LeaveApplicationCreate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply for leave (staff self-service)"""
    # Get staff record for current user
    staff = await StaffRepository.get_staff_by_user_id(db, str(current_user.id), school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff record not found for user")
    
    # Validate leave type
    leave_type = await LeaveRepository.get_leave_type(db, leave_data.leave_type_id, school_id)
    if not leave_type or not leave_type.is_active:
        raise HTTPException(status_code=400, detail="Invalid leave type")
    
    # Create leave application
    leave_dict = leave_data.model_dump()
    leave_dict["staff_id"] = str(staff.id)
    leave_dict["status"] = LeaveStatus.pending
    
    leave = await LeaveRepository.create_staff_leave(db, leave_dict, school_id)
    
    return {
        **leave.__dict__,
        "staff_name": f"{staff.first_name} {staff.last_name}",
        "leave_type_name": leave_type.name,
    }


@router.get("/applications/{leave_id}", response_model=LeaveApplicationResponse)
async def get_leave_application(
    leave_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get leave application by ID"""
    leave = await LeaveRepository.get_staff_leave(db, leave_id, school_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave application not found")
    
    # Check permission (admin or self)
    staff = await StaffRepository.get_staff_by_user_id(db, str(current_user.id), school_id)
    # TODO: Check if user has permission to view all leaves or only own
    
    # Enrich with staff name, leave type name
    staff_record = await StaffRepository.get_staff_by_id(db, leave.staff_id, school_id)
    leave_type = await LeaveRepository.get_leave_type(db, leave.leave_type_id, school_id)
    
    return {
        **leave.__dict__,
        "staff_name": f"{staff_record.first_name} {staff_record.last_name}" if staff_record else None,
        "leave_type_name": leave_type.name if leave_type else None,
    }


@router.patch("/applications/{leave_id}/review", response_model=LeaveApplicationResponse)
async def review_leave_application(
    leave_id: str,
    review_data: LeaveApplicationReview,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "review")),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject leave application"""
    leave = await LeaveRepository.get_staff_leave(db, leave_id, school_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave application not found")
    
    if leave.status != LeaveStatus.pending:
        raise HTTPException(status_code=400, detail="Leave application already processed")
    
    # Process leave
    staff_service = StaffService(db)
    approved = review_data.status == LeaveStatus.approved
    
    try:
        processed_leave = await staff_service.process_leave_application(
            leave, approved, str(current_user.id), review_data.remarks
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # TODO: Send notification via Celery
    # await send_leave_decision_notification.delay(leave.staff_id, leave_id, approved)
    
    return processed_leave


@router.patch("/applications/{leave_id}/cancel", response_model=LeaveApplicationResponse)
async def cancel_leave_application(
    leave_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel own leave application (staff self-service)"""
    leave = await LeaveRepository.get_staff_leave(db, leave_id, school_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave application not found")
    
    # Check ownership
    staff = await StaffRepository.get_staff_by_user_id(db, str(current_user.id), school_id)
    if not staff or leave.staff_id != str(staff.id):
        raise HTTPException(status_code=403, detail="Cannot cancel others' leave applications")
    
    if leave.status != LeaveStatus.pending:
        raise HTTPException(status_code=400, detail="Can only cancel pending leave applications")
    
    cancelled_leave = await LeaveRepository.cancel_leave(db, leave)
    return cancelled_leave


# ===================== Leave Balance Endpoints =====================
@router.get("/balances", response_model=List[LeaveBalanceResponse])
async def list_leave_balances(
    staff_id: Optional[str] = Query(None),
    academic_year_id: Optional[str] = Query(None),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "view_balances")),
    db: AsyncSession = Depends(get_db),
):
    """List leave balances (admin view)"""
    balances = await LeaveRepository.get_leave_balances(
        db, school_id, staff_id=staff_id, academic_year_id=academic_year_id
    )
    
    # Enrich with leave type name
    result = []
    for balance in balances:
        leave_type = await LeaveRepository.get_leave_type(db, balance.leave_type_id, school_id)
        
        # Calculate remaining (in case DB doesn't have generated column)
        remaining = balance.entitled_days - balance.used_days
        
        result.append({
            **balance.__dict__,
            "leave_type_name": leave_type.name if leave_type else None,
            "remaining_days": remaining,
        })
    
    return result


@router.get("/balances/my", response_model=List[LeaveBalanceResponse])
async def get_my_leave_balances(
    academic_year_id: Optional[str] = Query(None),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's leave balances (staff self-view)"""
    # Get staff record for current user
    staff = await StaffRepository.get_staff_by_user_id(db, str(current_user.id), school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff record not found for user")
    
    balances = await LeaveRepository.get_leave_balances(
        db, school_id, staff_id=str(staff.id), academic_year_id=academic_year_id
    )
    
    # Enrich with leave type name
    result = []
    for balance in balances:
        leave_type = await LeaveRepository.get_leave_type(db, balance.leave_type_id, school_id)
        remaining = balance.entitled_days - balance.used_days
        
        result.append({
            **balance.__dict__,
            "leave_type_name": leave_type.name if leave_type else None,
            "remaining_days": remaining,
        })
    
    return result


@router.post("/balances/allocate", response_model=LeaveBalanceResponse, status_code=status.HTTP_201_CREATED)
async def allocate_leave_balance(
    balance_data: LeaveAllocationRequest,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "allocate")),
    db: AsyncSession = Depends(get_db),
):
    """Manually allocate leave balance for a staff member"""
    balance_dict = balance_data.model_dump()
    balance_dict["used_days"] = 0.0
    
    balance = await LeaveRepository.upsert_leave_balance(db, balance_dict, school_id)
    
    # Calculate remaining
    remaining = balance.entitled_days - balance.used_days
    
    return {
        **balance.__dict__,
        "remaining_days": remaining,
    }


@router.put("/balances/{balance_id}", response_model=LeaveBalanceResponse)
async def update_leave_balance(
    balance_id: str,
    balance_data: LeaveBalanceUpdateRequest,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "edit_balances")),
    db: AsyncSession = Depends(get_db),
):
    """Update leave balance entitled days (admin only)"""
    # Get balance
    from sqlalchemy import select
    from app.models.staff import StaffLeaveBalance
    
    result = await db.execute(
        select(StaffLeaveBalance).where(
            StaffLeaveBalance.id == balance_id,
            StaffLeaveBalance.school_id == school_id,
        )
    )
    balance = result.scalar_one_or_none()
    if not balance:
        raise HTTPException(status_code=404, detail="Leave balance not found")
    
    update_dict = balance_data.model_dump(exclude_unset=True)
    updated_balance = await LeaveRepository.update_leave_balance(db, balance, update_dict)
    
    remaining = updated_balance.entitled_days - updated_balance.used_days
    
    return {
        **updated_balance.__dict__,
        "remaining_days": remaining,
    }


# ===================== Leave Statistics Endpoints =====================
@router.get("/stats/summary", response_model=LeaveStatistics)
async def get_leave_statistics(
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("leaves", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get leave statistics"""
    total_leaves = await LeaveRepository.count_staff_leaves(db, school_id)
    pending_leaves = await LeaveRepository.count_staff_leaves(db, school_id, status=LeaveStatus.pending)
    approved_leaves = await LeaveRepository.count_staff_leaves(db, school_id, status=LeaveStatus.approved)
    rejected_leaves = await LeaveRepository.count_staff_leaves(db, school_id, status=LeaveStatus.rejected)
    
    by_leave_type = await LeaveRepository.count_leaves_by_type(db, school_id)
    
    return {
        "total_leaves": total_leaves,
        "pending_leaves": pending_leaves,
        "approved_leaves": approved_leaves,
        "rejected_leaves": rejected_leaves,
        "by_leave_type": by_leave_type,
    }

