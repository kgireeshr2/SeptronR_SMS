from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_school_id, permission_required
from app.db.session import get_db
from app.models.auth import User
from app.repositories.staff_repository import StaffRepository
from app.schemas.phase6 import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DesignationCreate,
    DesignationUpdate,
    DesignationResponse,
)

router = APIRouter()


# ===================== Department Endpoints =====================
@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("departments", "view")),
    db: AsyncSession = Depends(get_db),
):
    """List all departments for a school"""
    departments = await StaffRepository.get_departments(
        db, school_id, is_active=is_active, skip=skip, limit=limit
    )
    
    # Get staff count for each department
    result = []
    for dept in departments:
        staff_count = await StaffRepository.count_staff(
            db, school_id, department_id=str(dept.id), is_active=True
        )
        result.append({
            **dept.__dict__,
            "staff_count": staff_count,
        })
    
    return result


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("departments", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new department"""
    department = await StaffRepository.create_department(
        db, department_data.model_dump(), school_id
    )
    return department


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("departments", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get department by ID"""
    department = await StaffRepository.get_department(db, department_id, school_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Get staff count
    staff_count = await StaffRepository.count_staff(
        db, school_id, department_id=department_id, is_active=True
    )
    
    return {
        **department.__dict__,
        "staff_count": staff_count,
    }


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    department_data: DepartmentUpdate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("departments", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Update department"""
    department = await StaffRepository.get_department(db, department_id, school_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    update_dict = department_data.model_dump(exclude_unset=True)
    updated_department = await StaffRepository.update_department(db, department, update_dict)
    return updated_department


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("departments", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete (deactivate) department"""
    department = await StaffRepository.get_department(db, department_id, school_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if department has active staff
    staff_count = await StaffRepository.count_staff(
        db, school_id, department_id=department_id, is_active=True
    )
    if staff_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete department with {staff_count} active staff members"
        )
    
    await StaffRepository.update_department(db, department, {"is_active": False})


# ===================== Designation Endpoints =====================
@router.get("/designations", response_model=List[DesignationResponse])
async def list_designations(
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("designations", "view")),
    db: AsyncSession = Depends(get_db),
):
    """List all designations for a school"""
    designations = await StaffRepository.get_designations(
        db, school_id, is_active=is_active, skip=skip, limit=limit
    )
    
    # Get staff count for each designation
    result = []
    for desig in designations:
        staff_count = await StaffRepository.count_staff(
            db, school_id, designation_id=str(desig.id), is_active=True
        )
        result.append({
            **desig.__dict__,
            "staff_count": staff_count,
        })
    
    return result


@router.post("/designations", response_model=DesignationResponse, status_code=status.HTTP_201_CREATED)
async def create_designation(
    designation_data: DesignationCreate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("designations", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new designation"""
    designation = await StaffRepository.create_designation(
        db, designation_data.model_dump(), school_id
    )
    return designation


@router.get("/designations/{designation_id}", response_model=DesignationResponse)
async def get_designation(
    designation_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("designations", "view")),
    db: AsyncSession = Depends(get_db),
):
    """Get designation by ID"""
    designation = await StaffRepository.get_designation(db, designation_id, school_id)
    if not designation:
        raise HTTPException(status_code=404, detail="Designation not found")
    
    # Get staff count
    staff_count = await StaffRepository.count_staff(
        db, school_id, designation_id=designation_id, is_active=True
    )
    
    return {
        **designation.__dict__,
        "staff_count": staff_count,
    }


@router.put("/designations/{designation_id}", response_model=DesignationResponse)
async def update_designation(
    designation_id: str,
    designation_data: DesignationUpdate,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("designations", "edit")),
    db: AsyncSession = Depends(get_db),
):
    """Update designation"""
    designation = await StaffRepository.get_designation(db, designation_id, school_id)
    if not designation:
        raise HTTPException(status_code=404, detail="Designation not found")
    
    update_dict = designation_data.model_dump(exclude_unset=True)
    updated_designation = await StaffRepository.update_designation(db, designation, update_dict)
    return updated_designation


@router.delete("/designations/{designation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_designation(
    designation_id: str,
    school_id: str = Depends(get_school_id),
    current_user: User = Depends(permission_required("designations", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete (deactivate) designation"""
    designation = await StaffRepository.get_designation(db, designation_id, school_id)
    if not designation:
        raise HTTPException(status_code=404, detail="Designation not found")
    
    # Check if designation has active staff
    staff_count = await StaffRepository.count_staff(
        db, school_id, designation_id=designation_id, is_active=True
    )
    if staff_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete designation with {staff_count} active staff members"
        )
    
    await StaffRepository.update_designation(db, designation, {"is_active": False})

