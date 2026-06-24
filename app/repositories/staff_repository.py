from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.staff import (
    Department,
    Designation,
    Staff,
    StaffDocument,
    LeaveType,
    StaffLeave,
    StaffLeaveBalance,
    StaffPayroll,
    EmploymentType,
    LeaveStatus,
)
from app.models.auth import User
from app.models.academic import AcademicYear


class StaffRepository:
    @staticmethod
    async def get_departments(
        db: AsyncSession,
        school_id: str,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Department]:
        query = select(Department).where(Department.school_id == school_id)
        if is_active is not None:
            query = query.where(Department.is_active == is_active)
        query = query.order_by(Department.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_department(db: AsyncSession, department_id: str, school_id: str) -> Optional[Department]:
        result = await db.execute(
            select(Department).where(
                Department.id == department_id, Department.school_id == school_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_department(db: AsyncSession, department_data: dict, school_id: str) -> Department:
        department = Department(**department_data, school_id=school_id)
        db.add(department)
        await db.commit()
        await db.refresh(department)
        return department

    @staticmethod
    async def update_department(
        db: AsyncSession, department: Department, update_data: dict
    ) -> Department:
        for field, value in update_data.items():
            setattr(department, field, value)
        department.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(department)
        return department

    @staticmethod
    async def get_designations(
        db: AsyncSession,
        school_id: str,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Designation]:
        query = select(Designation).where(Designation.school_id == school_id)
        if is_active is not None:
            query = query.where(Designation.is_active == is_active)
        query = query.order_by(Designation.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_designation(db: AsyncSession, designation_id: str, school_id: str) -> Optional[Designation]:
        result = await db.execute(
            select(Designation).where(
                Designation.id == designation_id, Designation.school_id == school_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_designation(db: AsyncSession, designation_data: dict, school_id: str) -> Designation:
        designation = Designation(**designation_data, school_id=school_id)
        db.add(designation)
        await db.commit()
        await db.refresh(designation)
        return designation

    @staticmethod
    async def update_designation(
        db: AsyncSession, designation: Designation, update_data: dict
    ) -> Designation:
        for field, value in update_data.items():
            setattr(designation, field, value)
        designation.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(designation)
        return designation

    @staticmethod
    async def get_staff_list(
        db: AsyncSession,
        school_id: str,
        department_id: Optional[str] = None,
        designation_id: Optional[str] = None,
        employment_type: Optional[EmploymentType] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Staff]:
        query = select(Staff).where(
            Staff.school_id == school_id, Staff.deleted_at.is_(None)
        )

        if department_id:
            query = query.where(Staff.department_id == department_id)
        if designation_id:
            query = query.where(Staff.designation_id == designation_id)
        if employment_type:
            query = query.where(Staff.employment_type == employment_type)
        if is_active is not None:
            query = query.where(Staff.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Staff.first_name.ilike(search_term),
                    Staff.last_name.ilike(search_term),
                    Staff.employee_id.ilike(search_term),
                )
            )

        query = query.order_by(Staff.employee_id).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def count_staff(
        db: AsyncSession,
        school_id: str,
        department_id: Optional[str] = None,
        designation_id: Optional[str] = None,
        employment_type: Optional[EmploymentType] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> int:
        query = select(func.count(Staff.id)).where(
            Staff.school_id == school_id, Staff.deleted_at.is_(None)
        )

        if department_id:
            query = query.where(Staff.department_id == department_id)
        if designation_id:
            query = query.where(Staff.designation_id == designation_id)
        if employment_type:
            query = query.where(Staff.employment_type == employment_type)
        if is_active is not None:
            query = query.where(Staff.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Staff.first_name.ilike(search_term),
                    Staff.last_name.ilike(search_term),
                    Staff.employee_id.ilike(search_term),
                )
            )

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_staff_by_id(db: AsyncSession, staff_id: str, school_id: str) -> Optional[Staff]:
        result = await db.execute(
            select(Staff).where(
                Staff.id == staff_id,
                Staff.school_id == school_id,
                Staff.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_staff_by_user_id(db: AsyncSession, user_id: str, school_id: str) -> Optional[Staff]:
        result = await db.execute(
            select(Staff).where(
                Staff.user_id == user_id,
                Staff.school_id == school_id,
                Staff.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_staff_by_employee_id(
        db: AsyncSession, employee_id: str, school_id: str
    ) -> Optional[Staff]:
        result = await db.execute(
            select(Staff).where(
                Staff.employee_id == employee_id,
                Staff.school_id == school_id,
                Staff.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_staff(db: AsyncSession, staff_data: dict, school_id: str) -> Staff:
        staff = Staff(**staff_data, school_id=school_id)
        db.add(staff)
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def update_staff(db: AsyncSession, staff: Staff, update_data: dict) -> Staff:
        for field, value in update_data.items():
            if value is not None or field in ["department_id", "designation_id"]:
                setattr(staff, field, value)
        staff.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def soft_delete_staff(db: AsyncSession, staff: Staff, deleted_by: str) -> Staff:
        staff.deleted_at = datetime.utcnow()
        staff.deleted_by = deleted_by
        staff.is_active = False
        await db.commit()
        await db.refresh(staff)
        return staff

    @staticmethod
    async def get_staff_documents(
        db: AsyncSession, staff_id: str, school_id: str
    ) -> List[StaffDocument]:
        result = await db.execute(
            select(StaffDocument)
            .where(
                StaffDocument.staff_id == staff_id,
                StaffDocument.school_id == school_id,
            )
            .order_by(StaffDocument.uploaded_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_staff_document(
        db: AsyncSession, document_id: str, school_id: str
    ) -> Optional[StaffDocument]:
        result = await db.execute(
            select(StaffDocument).where(
                StaffDocument.id == document_id,
                StaffDocument.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_staff_document(
        db: AsyncSession, document_data: dict, school_id: str
    ) -> StaffDocument:
        document = StaffDocument(**document_data, school_id=school_id)
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    @staticmethod
    async def delete_staff_document(db: AsyncSession, document: StaffDocument) -> None:
        await db.delete(document)
        await db.commit()

    @staticmethod
    async def count_by_department(db: AsyncSession, school_id: str) -> Dict[str, int]:
        result = await db.execute(
            select(Department.name, func.count(Staff.id))
            .join(Staff, Staff.department_id == Department.id, isouter=True)
            .where(Department.school_id == school_id, Staff.deleted_at.is_(None))
            .group_by(Department.id, Department.name)
        )
        return {name: count for name, count in result.all()}

    @staticmethod
    async def count_by_designation(db: AsyncSession, school_id: str) -> Dict[str, int]:
        result = await db.execute(
            select(Designation.name, func.count(Staff.id))
            .join(Staff, Staff.designation_id == Designation.id, isouter=True)
            .where(Designation.school_id == school_id, Staff.deleted_at.is_(None))
            .group_by(Designation.id, Designation.name)
        )
        return {name: count for name, count in result.all()}

    @staticmethod
    async def count_by_employment_type(db: AsyncSession, school_id: str) -> Dict[str, int]:
        result = await db.execute(
            select(Staff.employment_type, func.count(Staff.id))
            .where(Staff.school_id == school_id, Staff.deleted_at.is_(None))
            .group_by(Staff.employment_type)
        )
        return {emp_type.value: count for emp_type, count in result.all()}

