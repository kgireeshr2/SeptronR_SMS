from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.staff import StaffPayroll, PaymentMethod


class PayrollRepository:
    @staticmethod
    async def get_payroll_list(
        db: AsyncSession,
        school_id: str,
        academic_year_id: Optional[str] = None,
        staff_id: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        is_paid: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StaffPayroll]:
        query = select(StaffPayroll).where(StaffPayroll.school_id == school_id)

        if academic_year_id:
            query = query.where(StaffPayroll.academic_year_id == academic_year_id)
        if staff_id:
            query = query.where(StaffPayroll.staff_id == staff_id)
        if month:
            query = query.where(StaffPayroll.month == month)
        if year:
            query = query.where(StaffPayroll.year == year)
        if is_paid is not None:
            query = query.where(StaffPayroll.is_paid == is_paid)

        query = query.order_by(StaffPayroll.year.desc(), StaffPayroll.month.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def count_payroll(
        db: AsyncSession,
        school_id: str,
        academic_year_id: Optional[str] = None,
        staff_id: Optional[str] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        is_paid: Optional[bool] = None,
    ) -> int:
        query = select(func.count(StaffPayroll.id)).where(StaffPayroll.school_id == school_id)

        if academic_year_id:
            query = query.where(StaffPayroll.academic_year_id == academic_year_id)
        if staff_id:
            query = query.where(StaffPayroll.staff_id == staff_id)
        if month:
            query = query.where(StaffPayroll.month == month)
        if year:
            query = query.where(StaffPayroll.year == year)
        if is_paid is not None:
            query = query.where(StaffPayroll.is_paid == is_paid)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_payroll(db: AsyncSession, payroll_id: str, school_id: str) -> Optional[StaffPayroll]:
        result = await db.execute(
            select(StaffPayroll).where(
                StaffPayroll.id == payroll_id, StaffPayroll.school_id == school_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_payroll_by_staff_month(
        db: AsyncSession,
        staff_id: str,
        month: int,
        year: int,
        school_id: str,
    ) -> Optional[StaffPayroll]:
        result = await db.execute(
            select(StaffPayroll).where(
                StaffPayroll.staff_id == staff_id,
                StaffPayroll.month == month,
                StaffPayroll.year == year,
                StaffPayroll.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_payroll(db: AsyncSession, payroll_data: dict, school_id: str) -> StaffPayroll:
        payroll = StaffPayroll(**payroll_data, school_id=school_id)
        db.add(payroll)
        await db.commit()
        await db.refresh(payroll)
        return payroll

    @staticmethod
    async def bulk_create_payroll(
        db: AsyncSession, payroll_entries: List[dict], school_id: str
    ) -> List[StaffPayroll]:
        payroll_objects = [StaffPayroll(**entry, school_id=school_id) for entry in payroll_entries]
        db.add_all(payroll_objects)
        await db.commit()
        for payroll in payroll_objects:
            await db.refresh(payroll)
        return payroll_objects

    @staticmethod
    async def update_payroll(
        db: AsyncSession, payroll: StaffPayroll, update_data: dict
    ) -> StaffPayroll:
        for field, value in update_data.items():
            if value is not None:
                setattr(payroll, field, value)
        payroll.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(payroll)
        return payroll

    @staticmethod
    async def mark_paid(
        db: AsyncSession,
        payroll: StaffPayroll,
        payment_date: date,
        payment_method: PaymentMethod,
    ) -> StaffPayroll:
        payroll.is_paid = True
        payroll.payment_date = payment_date
        payroll.payment_method = payment_method
        payroll.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(payroll)
        return payroll

    @staticmethod
    async def bulk_mark_paid(
        db: AsyncSession,
        payroll_ids: List[str],
        school_id: str,
        payment_date: date,
        payment_method: PaymentMethod,
    ) -> int:
        result = await db.execute(
            select(StaffPayroll).where(
                StaffPayroll.id.in_(payroll_ids),
                StaffPayroll.school_id == school_id,
            )
        )
        payroll_entries = result.scalars().all()

        count = 0
        for payroll in payroll_entries:
            payroll.is_paid = True
            payroll.payment_date = payment_date
            payroll.payment_method = payment_method
            payroll.updated_at = datetime.utcnow()
            count += 1

        await db.commit()
        return count

    @staticmethod
    async def delete_payroll(db: AsyncSession, payroll: StaffPayroll) -> None:
        """Delete draft payroll (only if not paid)"""
        if payroll.is_paid:
            raise ValueError("Cannot delete paid payroll")
        await db.delete(payroll)
        await db.commit()

    @staticmethod
    async def get_staff_payroll_history(
        db: AsyncSession,
        staff_id: str,
        school_id: str,
        skip: int = 0,
        limit: int = 12,
    ) -> List[StaffPayroll]:
        result = await db.execute(
            select(StaffPayroll)
            .where(
                StaffPayroll.staff_id == staff_id,
                StaffPayroll.school_id == school_id,
            )
            .order_by(StaffPayroll.year.desc(), StaffPayroll.month.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

