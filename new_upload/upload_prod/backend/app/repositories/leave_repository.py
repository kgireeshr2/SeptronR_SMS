from datetime import date, datetime
from typing import Dict, List, Optional
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.staff import LeaveType, StaffLeave, StaffLeaveBalance, LeaveStatus


class LeaveRepository:
    @staticmethod
    async def get_leave_types(
        db: AsyncSession,
        school_id: str,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LeaveType]:
        query = select(LeaveType).where(LeaveType.school_id == school_id)
        if is_active is not None:
            query = query.where(LeaveType.is_active == is_active)
        query = query.order_by(LeaveType.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_leave_type(db: AsyncSession, leave_type_id: str, school_id: str) -> Optional[LeaveType]:
        result = await db.execute(
            select(LeaveType).where(
                LeaveType.id == leave_type_id, LeaveType.school_id == school_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_leave_type(db: AsyncSession, leave_type_data: dict, school_id: str) -> LeaveType:
        leave_type = LeaveType(**leave_type_data, school_id=school_id)
        db.add(leave_type)
        await db.commit()
        await db.refresh(leave_type)
        return leave_type

    @staticmethod
    async def update_leave_type(
        db: AsyncSession, leave_type: LeaveType, update_data: dict
    ) -> LeaveType:
        for field, value in update_data.items():
            setattr(leave_type, field, value)
        await db.commit()
        await db.refresh(leave_type)
        return leave_type

    @staticmethod
    async def get_leave_balances(
        db: AsyncSession,
        school_id: str,
        staff_id: Optional[str] = None,
        academic_year_id: Optional[str] = None,
    ) -> List[StaffLeaveBalance]:
        query = select(StaffLeaveBalance).where(StaffLeaveBalance.school_id == school_id)
        if staff_id:
            query = query.where(StaffLeaveBalance.staff_id == staff_id)
        if academic_year_id:
            query = query.where(StaffLeaveBalance.academic_year_id == academic_year_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_leave_balance(
        db: AsyncSession,
        staff_id: str,
        leave_type_id: str,
        academic_year_id: str,
        school_id: str,
    ) -> Optional[StaffLeaveBalance]:
        result = await db.execute(
            select(StaffLeaveBalance).where(
                StaffLeaveBalance.staff_id == staff_id,
                StaffLeaveBalance.leave_type_id == leave_type_id,
                StaffLeaveBalance.academic_year_id == academic_year_id,
                StaffLeaveBalance.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_leave_balance(
        db: AsyncSession, balance_data: dict, school_id: str
    ) -> StaffLeaveBalance:
        # Check if balance exists
        existing = await LeaveRepository.get_leave_balance(
            db,
            balance_data["staff_id"],
            balance_data["leave_type_id"],
            balance_data["academic_year_id"],
            school_id,
        )

        if existing:
            # Update existing
            for field, value in balance_data.items():
                setattr(existing, field, value)
            existing.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new
            balance = StaffLeaveBalance(**balance_data, school_id=school_id)
            db.add(balance)
            await db.commit()
            await db.refresh(balance)
            return balance

    @staticmethod
    async def update_leave_balance(
        db: AsyncSession, balance: StaffLeaveBalance, update_data: dict
    ) -> StaffLeaveBalance:
        for field, value in update_data.items():
            setattr(balance, field, value)
        balance.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(balance)
        return balance

    @staticmethod
    async def deduct_leave_balance(
        db: AsyncSession,
        staff_id: str,
        leave_type_id: str,
        academic_year_id: str,
        school_id: str,
        days: float,
    ) -> StaffLeaveBalance:
        """Deduct used days from leave balance (increases used_days, remaining_days auto-recalculates)"""
        balance = await LeaveRepository.get_leave_balance(
            db, staff_id, leave_type_id, academic_year_id, school_id
        )
        if not balance:
            raise ValueError("Leave balance not found")

        balance.used_days += days
        balance.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(balance)
        return balance

    @staticmethod
    async def get_staff_leaves(
        db: AsyncSession,
        school_id: str,
        staff_id: Optional[str] = None,
        status: Optional[LeaveStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StaffLeave]:
        query = select(StaffLeave).where(StaffLeave.school_id == school_id)

        if staff_id:
            query = query.where(StaffLeave.staff_id == staff_id)
        if status:
            query = query.where(StaffLeave.status == status)
        if from_date:
            query = query.where(StaffLeave.to_date >= from_date)
        if to_date:
            query = query.where(StaffLeave.from_date <= to_date)

        query = query.order_by(StaffLeave.from_date.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def count_staff_leaves(
        db: AsyncSession,
        school_id: str,
        staff_id: Optional[str] = None,
        status: Optional[LeaveStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> int:
        query = select(func.count(StaffLeave.id)).where(StaffLeave.school_id == school_id)

        if staff_id:
            query = query.where(StaffLeave.staff_id == staff_id)
        if status:
            query = query.where(StaffLeave.status == status)
        if from_date:
            query = query.where(StaffLeave.to_date >= from_date)
        if to_date:
            query = query.where(StaffLeave.from_date <= to_date)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_staff_leave(
        db: AsyncSession, leave_id: str, school_id: str
    ) -> Optional[StaffLeave]:
        result = await db.execute(
            select(StaffLeave).where(
                StaffLeave.id == leave_id, StaffLeave.school_id == school_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_staff_leave(
        db: AsyncSession, leave_data: dict, school_id: str
    ) -> StaffLeave:
        leave = StaffLeave(**leave_data, school_id=school_id)
        db.add(leave)
        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def update_staff_leave(
        db: AsyncSession, leave: StaffLeave, update_data: dict
    ) -> StaffLeave:
        for field, value in update_data.items():
            setattr(leave, field, value)
        leave.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def approve_leave(
        db: AsyncSession,
        leave: StaffLeave,
        approved_by: str,
        remarks: Optional[str] = None,
    ) -> StaffLeave:
        leave.status = LeaveStatus.approved
        leave.approved_by = approved_by
        leave.approved_at = datetime.utcnow()
        leave.remarks = remarks
        leave.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def reject_leave(
        db: AsyncSession,
        leave: StaffLeave,
        approved_by: str,
        remarks: Optional[str] = None,
    ) -> StaffLeave:
        leave.status = LeaveStatus.rejected
        leave.approved_by = approved_by
        leave.approved_at = datetime.utcnow()
        leave.remarks = remarks
        leave.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def cancel_leave(db: AsyncSession, leave: StaffLeave) -> StaffLeave:
        leave.status = LeaveStatus.cancelled
        leave.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def count_leaves_by_status(db: AsyncSession, school_id: str) -> Dict[str, int]:
        result = await db.execute(
            select(StaffLeave.status, func.count(StaffLeave.id))
            .where(StaffLeave.school_id == school_id)
            .group_by(StaffLeave.status)
        )
        return {status.value: count for status, count in result.all()}

    @staticmethod
    async def count_leaves_by_type(db: AsyncSession, school_id: str) -> Dict[str, int]:
        result = await db.execute(
            select(LeaveType.name, func.count(StaffLeave.id))
            .join(StaffLeave, StaffLeave.leave_type_id == LeaveType.id, isouter=True)
            .where(LeaveType.school_id == school_id)
            .group_by(LeaveType.id, LeaveType.name)
        )
        return {name: count for name, count in result.all()}

    @staticmethod
    async def cancel_pending_leaves(db: AsyncSession, staff_id: str, school_id: str) -> int:
        """Cancel all pending leaves for a staff member (used during termination)"""
        result = await db.execute(
            select(StaffLeave).where(
                StaffLeave.staff_id == staff_id,
                StaffLeave.school_id == school_id,
                StaffLeave.status == LeaveStatus.pending,
            )
        )
        leaves = result.scalars().all()
        
        count = 0
        for leave in leaves:
            leave.status = LeaveStatus.cancelled
            leave.updated_at = datetime.utcnow()
            count += 1
        
        await db.commit()
        return count

