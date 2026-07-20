import secrets
import string
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.staff import Staff, EmploymentType, LeaveStatus, StaffLeave, StaffPayroll
from app.models.auth import User
from app.models.rbac import UserRole
from app.models.academic import AcademicYear
from app.repositories.staff_repository import StaffRepository
from app.repositories.leave_repository import LeaveRepository
from app.repositories.payroll_repository import PayrollRepository
from app.utils.employee_id import generate_employee_id
from app.core.security import get_password_hash


class StaffService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_staff(
        self,
        staff_data: dict,
        email: str,
        phone: str,
        role_ids: List[str],
        school_id: str,
    ) -> Tuple[Staff, str]:
        """
        Create a new staff member with user account.
        
        1. Generate employee_id
        2. Create user account with temp password
        3. Assign roles to user
        4. Create staff record linked to user
        5. Allocate leave for current academic year
        6. Return staff and temp password (for welcome email/SMS)
        """
        # Generate employee ID
        employee_id = await generate_employee_id(self.db, school_id)

        # Generate temporary password
        temp_password = self._generate_temp_password()
        hashed_password = get_password_hash(temp_password)

        # Create user account
        user = User(
            school_id=school_id,
            email=email,
            phone=phone,
            password_hash=hashed_password,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(user)
        await self.db.flush()  # Get user.id before creating staff

        # Assign roles to user
        for role_id in role_ids:
            user_role = UserRole(user_id=str(user.id), role_id=role_id)
            self.db.add(user_role)

        # Create staff record
        staff_dict = {**staff_data, "employee_id": employee_id, "user_id": str(user.id)}
        staff = await StaffRepository.create_staff(self.db, staff_dict, school_id)

        # Allocate leave for current academic year
        await self._allocate_leave_for_staff(staff.id, school_id)

        return staff, temp_password

    async def terminate_staff(
        self, staff: Staff, deleted_by: str, reason: Optional[str] = None
    ) -> Staff:
        """
        Terminate staff member.
        
        1. Soft delete staff (set is_active=False, deleted_at, deleted_by)
        2. Deactivate user account
        3. Cancel all pending leave applications
        """
        # Soft delete staff
        terminated_staff = await StaffRepository.soft_delete_staff(
            self.db, staff, deleted_by
        )

        # Deactivate user account
        result = await self.db.execute(select(User).where(User.id == staff.user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_active = False
            user.updated_at = datetime.utcnow()

        # Cancel pending leaves
        await LeaveRepository.cancel_pending_leaves(
            self.db, staff.id, staff.school_id
        )

        await self.db.commit()
        return terminated_staff

    async def process_leave_application(
        self,
        leave: StaffLeave,
        approved: bool,
        approved_by: str,
        remarks: Optional[str] = None,
    ) -> StaffLeave:
        """
        Process leave application (approve or reject).
        
        If approved:
        1. Update leave status to approved
        2. Deduct days from leave balance (used_days increases, remaining_days auto-recalculates)
        3. Send notification to staff
        
        If rejected:
        1. Update leave status to rejected
        2. Send notification to staff
        """
        if approved:
            # Get current academic year (simplified - assumes one active year)
            result = await self.db.execute(
                select(AcademicYear)
                .where(
                    AcademicYear.school_id == leave.school_id,
                    AcademicYear.is_current == True,
                )
            )
            academic_year = result.scalar_one_or_none()
            if not academic_year:
                raise ValueError("No active academic year found")

            # Check leave balance
            balance = await LeaveRepository.get_leave_balance(
                self.db,
                leave.staff_id,
                leave.leave_type_id,
                str(academic_year.id),
                leave.school_id,
            )
            if not balance:
                raise ValueError("Leave balance not found for staff")

            # Check if sufficient balance (remaining_days is generated column, use calculation)
            remaining = balance.entitled_days - balance.used_days
            if remaining < leave.total_days:
                raise ValueError(
                    f"Insufficient leave balance. Available: {remaining}, Requested: {leave.total_days}"
                )

            # Approve leave
            approved_leave = await LeaveRepository.approve_leave(
                self.db, leave, approved_by, remarks
            )

            # Deduct balance
            await LeaveRepository.deduct_leave_balance(
                self.db,
                leave.staff_id,
                leave.leave_type_id,
                str(academic_year.id),
                leave.school_id,
                leave.total_days,
            )

            # TODO: Send notification via Celery task
            # await send_leave_approved_notification.delay(staff_id, leave_id)

            return approved_leave
        else:
            # Reject leave
            rejected_leave = await LeaveRepository.reject_leave(
                self.db, leave, approved_by, remarks
            )

            # TODO: Send notification via Celery task
            # await send_leave_rejected_notification.delay(staff_id, leave_id, remarks)

            return rejected_leave

    async def generate_monthly_payroll(
        self,
        month: int,
        year: int,
        academic_year_id: str,
        school_id: str,
        staff_ids: Optional[List[str]] = None,
    ) -> List[StaffPayroll]:
        """
        Generate monthly payroll for staff.
        
        1. Load all active staff (or specified staff_ids)
        2. For each staff:
           - Calculate basic salary (from staff.monthly_salary)
           - Calculate allowances (can be customized per school, default from staff salary)
           - Calculate deductions (PF, ESI, TDS, etc.)
           - Calculate gross salary (basic + allowances)
           - Calculate net salary (gross - deductions)
        3. Bulk insert payroll records
        4. Return created payroll entries
        
        Note: Attendance-based salary calculation is simplified here.
        For production, integrate with attendance module.
        """
        # Get staff list
        if staff_ids:
            staff_list = []
            for staff_id in staff_ids:
                staff = await StaffRepository.get_staff_by_id(self.db, staff_id, school_id)
                if staff and staff.is_active:
                    staff_list.append(staff)
        else:
            staff_list = await StaffRepository.get_staff_list(
                self.db, school_id, is_active=True, limit=1000
            )

        # Generate payroll entries
        payroll_entries = []
        for staff in staff_list:
            # Check if payroll already exists for this month
            existing = await PayrollRepository.get_payroll_by_staff_month(
                self.db, str(staff.id), month, year, school_id
            )
            if existing:
                continue  # Skip if already generated

            # Calculate salary components (all in paise)
            basic_salary = staff.monthly_salary
            
            # Default allowances (can be customized)
            allowances = {
                "hra": int(basic_salary * 0.40),  # 40% HRA
                "da": int(basic_salary * 0.10),   # 10% DA
                "ta": int(basic_salary * 0.05),   # 5% TA
                "other": 0,
            }
            
            # Default deductions (can be customized)
            deductions = {
                "pf": int(basic_salary * 0.12),   # 12% PF
                "esi": int(basic_salary * 0.0075),  # 0.75% ESI (if applicable)
                "tds": 0,  # Calculate based on tax rules
                "loan": 0,
                "other": 0,
            }
            
            gross_salary = basic_salary + sum(allowances.values())
            net_salary = gross_salary - sum(deductions.values())

            payroll_entry = {
                "staff_id": str(staff.id),
                "academic_year_id": academic_year_id,
                "month": month,
                "year": year,
                "basic_salary": basic_salary,
                "allowances": allowances,
                "deductions": deductions,
                "gross_salary": gross_salary,
                "net_salary": net_salary,
                "is_paid": False,
            }
            payroll_entries.append(payroll_entry)

        # Bulk create payroll
        if payroll_entries:
            created_payroll = await PayrollRepository.bulk_create_payroll(
                self.db, payroll_entries, school_id
            )
            return created_payroll
        return []

    async def _allocate_leave_for_staff(self, staff_id: str, school_id: str) -> None:
        """Allocate leave balance for staff for current academic year"""
        # Get current academic year
        result = await self.db.execute(
            select(AcademicYear).where(
                AcademicYear.school_id == school_id,
                AcademicYear.is_current == True,
            )
        )
        academic_year = result.scalar_one_or_none()
        if not academic_year:
            return  # No current academic year, skip allocation

        # Get all active leave types
        leave_types = await LeaveRepository.get_leave_types(
            self.db, school_id, is_active=True, limit=100
        )

        # Allocate balance for each leave type
        for leave_type in leave_types:
            balance_data = {
                "staff_id": staff_id,
                "leave_type_id": str(leave_type.id),
                "academic_year_id": str(academic_year.id),
                "entitled_days": float(leave_type.max_days_per_year),
                "used_days": 0.0,
            }
            await LeaveRepository.upsert_leave_balance(self.db, balance_data, school_id)

    @staticmethod
    def _generate_temp_password(length: int = 8) -> str:
        """Generate a temporary password for new staff"""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

