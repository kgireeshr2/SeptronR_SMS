from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_current_user, get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.models.staff import Department, Designation, EmploymentType
from app.repositories.staff_repository import StaffRepository
from app.repositories.user_repository import UserRepository
from app.services.staff_service import StaffService
from app.schemas.phase6 import (
    StaffCreate,
    StaffUpdate,
    StaffResponse,
    StaffDetailResponse,
    StaffTerminate,
    StaffStatistics,
    StaffDocumentCreate,
    StaffDocumentResponse,
)

router = APIRouter()


class StaffRolesAssign(BaseModel):
    role_ids: List[str]


# ===================== Staff CRUD Endpoints =====================
@router.get("", response_model=List[StaffResponse])
async def list_staff(
    department_id: Optional[str] = Query(None),
    designation_id: Optional[str] = Query(None),
    employment_type: Optional[EmploymentType] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "view")),
    db: AsyncSession = Depends(get_db),
):
    """List all staff with filters"""
    staff_list = await StaffRepository.get_staff_list(
        db,
        school_id,
        department_id=department_id,
        designation_id=designation_id,
        employment_type=employment_type,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit,
    )
    
    # Enrich with user data, department, designation names
    result = []
    for staff in staff_list:
        # Get user email/phone
        user_result = await db.execute(select(User).where(User.id == staff.user_id))
        user = user_result.scalar_one_or_none()
        
        # Get department name
        dept_name = None
        if staff.department_id:
            dept = await StaffRepository.get_department(db, staff.department_id, school_id)
            dept_name = dept.name if dept else None
        
        # Get designation name
        desig_name = None
        if staff.designation_id:
            desig = await StaffRepository.get_designation(db, staff.designation_id, school_id)
            desig_name = desig.name if desig else None
        
        result.append({
            **staff.__dict__,
            "email": user.email if user else None,
            "phone": user.phone if user else None,
            "department_name": dept_name,
            "designation_name": desig_name,
        })
    
    return result


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new staff member with user account"""
    # Check if email already exists within this school
    result = await db.execute(
        select(User).where(User.email == staff_data.email, User.school_id == school_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered in this school")
    
    # Check if phone already exists within this school
    if staff_data.phone:
        result = await db.execute(
            select(User).where(User.phone == staff_data.phone, User.school_id == school_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Phone number already registered in this school")
    
    # Create staff with user account
    staff_service = StaffService(db)
    staff_dict = staff_data.model_dump(exclude={"email", "phone", "role_ids"})
    staff, temp_password = await staff_service.create_staff(
        staff_dict,
        staff_data.email,
        staff_data.phone,
        staff_data.role_ids,
        school_id,
    )
    
    # TODO: Send welcome email/SMS with temp password
    # await send_staff_welcome_email.delay(staff.id, temp_password)
    
    # Get enriched response
    user_result = await db.execute(select(User).where(User.id == staff.user_id))
    user = user_result.scalar_one_or_none()
    
    return {
        **staff.__dict__,
        "email": user.email if user else None,
        "phone": user.phone if user else None,
        "temp_password": temp_password,  # Shown once for admin to communicate to staff
    }


@router.get("/{staff_id}", response_model=StaffDetailResponse)
async def get_staff(
    staff_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get staff member details with documents and leave balances"""
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Get user data
    user_result = await db.execute(select(User).where(User.id == staff.user_id))
    user = user_result.scalar_one_or_none()
    
    # Get department name
    dept_name = None
    if staff.department_id:
        dept = await StaffRepository.get_department(db, staff.department_id, school_id)
        dept_name = dept.name if dept else None
    
    # Get designation name
    desig_name = None
    if staff.designation_id:
        desig = await StaffRepository.get_designation(db, staff.designation_id, school_id)
        desig_name = desig.name if desig else None
    
    # Get documents
    documents = await StaffRepository.get_staff_documents(db, staff_id, school_id)
    
    # Get leave balances (handled by separate endpoint)
    # leave_balances = await LeaveRepository.get_leave_balances(db, school_id, staff_id=staff_id)
    
    return {
        **staff.__dict__,
        "email": user.email if user else None,
        "phone": user.phone if user else None,
        "department_name": dept_name,
        "designation_name": desig_name,
        "documents": [doc.__dict__ for doc in documents],
    }


@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: str,
    staff_data: StaffUpdate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Update staff member"""
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    update_dict = staff_data.model_dump(exclude_unset=True)
    updated_staff = await StaffRepository.update_staff(db, staff, update_dict)
    
    # Get user data
    user_result = await db.execute(select(User).where(User.id == updated_staff.user_id))
    user = user_result.scalar_one_or_none()
    
    return {
        **updated_staff.__dict__,
        "email": user.email if user else None,
        "phone": user.phone if user else None,
    }


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete staff member"""
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    await StaffRepository.soft_delete_staff(db, staff, str(current_user.id))


@router.post("/{staff_id}/terminate", response_model=StaffResponse)
async def terminate_staff(
    staff_id: str,
    termination_data: StaffTerminate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "terminate")),
    db: AsyncSession = Depends(get_db),
):
    """Terminate staff (deactivate user, cancel pending leaves)"""
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    staff_service = StaffService(db)
    terminated_staff = await staff_service.terminate_staff(
        staff, str(current_user.id), termination_data.reason
    )
    
    return terminated_staff


@router.post("/{staff_id}/photo", response_model=StaffResponse)
async def upload_staff_photo(
    staff_id: str,
    file: UploadFile = File(...),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Upload staff photo"""
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # TODO: Upload to storage service (S3, local storage, etc.)
    # For now, return placeholder
    photo_url = f"/uploads/staff/photos/{staff_id}_{file.filename}"
    
    updated_staff = await StaffRepository.update_staff(db, staff, {"photo_url": photo_url})
    return updated_staff


# ===================== Staff Document Endpoints =====================
@router.get("/{staff_id}/documents", response_model=List[StaffDocumentResponse])
async def list_staff_documents(
    staff_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "view")),
    db: AsyncSession = Depends(get_db),
):
    """List staff documents"""
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    documents = await StaffRepository.get_staff_documents(db, staff_id, school_id)
    return documents


@router.post("/{staff_id}/documents", response_model=StaffDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_staff_document(
    staff_id: str,
    doc_type: str = Query(...),
    file: UploadFile = File(...),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Upload staff document"""
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # TODO: Upload to storage service
    file_url = f"/uploads/staff/documents/{staff_id}_{file.filename}"
    
    document_data = {
        "staff_id": staff_id,
        "doc_type": doc_type,
        "file_url": file_url,
    }
    document = await StaffRepository.create_staff_document(db, document_data, school_id)
    return document


@router.delete("/{staff_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff_document(
    staff_id: str,
    document_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Delete staff document"""
    document = await StaffRepository.get_staff_document(db, document_id, school_id)
    if not document or document.staff_id != staff_id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    await StaffRepository.delete_staff_document(db, document)


# ===================== Staff Statistics Endpoints =====================
@router.get("/stats/summary", response_model=StaffStatistics)
async def get_staff_statistics(
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get staff statistics"""
    total_staff = await StaffRepository.count_staff(db, school_id)
    active_staff = await StaffRepository.count_staff(db, school_id, is_active=True)
    inactive_staff = await StaffRepository.count_staff(db, school_id, is_active=False)
    
    by_department = await StaffRepository.count_by_department(db, school_id)
    by_designation = await StaffRepository.count_by_designation(db, school_id)
    by_employment_type = await StaffRepository.count_by_employment_type(db, school_id)
    
    return {
        "total_staff": total_staff,
        "active_staff": active_staff,
        "inactive_staff": inactive_staff,
        "by_department": by_department,
        "by_designation": by_designation,
        "by_employment_type": by_employment_type,
    }


# ===================== Staff Role Endpoints =====================
@router.get("/{staff_id}/roles")
async def get_staff_roles(
    staff_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get current roles assigned to a staff member"""
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    from app.models.rbac import UserRole, Role
    result = await db.execute(
        select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == staff.user_id)
    )
    roles = result.scalars().all()
    return [{"id": str(r.id), "name": r.name, "slug": r.slug} for r in roles]


@router.put("/{staff_id}/roles")
async def assign_staff_roles(
    staff_id: str,
    body: StaffRolesAssign,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("staff", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Replace all roles for a staff member"""
    staff = await StaffRepository.get_staff_by_id(db, staff_id, school_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    user_repo = UserRepository(db)
    await user_repo.assign_roles(str(staff.user_id), body.role_ids, assigned_by=str(current_user.id))
    await db.commit()

    from app.models.rbac import UserRole, Role
    result = await db.execute(
        select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == staff.user_id)
    )
    roles = result.scalars().all()
    return [{"id": str(r.id), "name": r.name, "slug": r.slug} for r in roles]
