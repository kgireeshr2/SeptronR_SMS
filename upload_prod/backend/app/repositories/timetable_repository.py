from typing import Optional

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.classes import Class, Section, Subject, Timetable


class TimetableRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_grid_for_section(self, section_id: str, year_id: str) -> dict:
        section_result = await self.db.execute(
            select(Section.name, Class.name)
            .select_from(Section)
            .join(Class, Class.id == Section.class_id)
            .where(Section.id == section_id)
        )
        section_row = section_result.first()
        if not section_row:
            return {
                "section_id": section_id,
                "section_name": "",
                "class_name": "",
                "academic_year_id": year_id,
                "grid": {},
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "periods": [],
            }

        result = await self.db.execute(
            select(
                Timetable,
                Subject.name,
                User.first_name,
                User.last_name,
            )
            .select_from(Timetable)
            .join(Subject, Subject.id == Timetable.subject_id)
            .outerjoin(User, User.id == Timetable.teacher_id)
            .where(Timetable.section_id == section_id, Timetable.academic_year_id == year_id)
            .order_by(Timetable.day_of_week.asc(), Timetable.period_number.asc())
        )

        grid: dict[int, dict[int, Optional[dict]]] = {}
        periods: set[int] = set()
        for entry, subject_name, first_name, last_name in result.all():
            teacher_name = " ".join([part for part in [first_name, last_name] if part]) or None
            periods.add(entry.period_number)
            if entry.day_of_week not in grid:
                grid[entry.day_of_week] = {}
            grid[entry.day_of_week][entry.period_number] = {
                "id": str(entry.id),
                "section_id": str(entry.section_id),
                "subject_id": str(entry.subject_id),
                "teacher_id": str(entry.teacher_id) if entry.teacher_id else None,
                "day_of_week": entry.day_of_week,
                "period_number": entry.period_number,
                "start_time": entry.start_time,
                "end_time": entry.end_time,
                "subject_name": subject_name,
                "teacher_name": teacher_name,
            }

        return {
            "section_id": section_id,
            "section_name": section_row[0],
            "class_name": section_row[1],
            "academic_year_id": year_id,
            "grid": grid,
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "periods": sorted(periods),
        }

    async def get_teacher_schedule(self, teacher_id: str, year_id: str) -> list[dict]:
        result = await self.db.execute(
            select(
                Timetable,
                Subject.name,
                Section.name,
                Class.name,
            )
            .select_from(Timetable)
            .join(Subject, Subject.id == Timetable.subject_id)
            .join(Section, Section.id == Timetable.section_id)
            .join(Class, Class.id == Section.class_id)
            .where(Timetable.teacher_id == teacher_id, Timetable.academic_year_id == year_id)
            .order_by(Timetable.day_of_week.asc(), Timetable.period_number.asc())
        )
        payload: list[dict] = []
        for entry, subject_name, section_name, class_name in result.all():
            payload.append(
                {
                    "id": str(entry.id),
                    "section_id": str(entry.section_id),
                    "subject_id": str(entry.subject_id),
                    "teacher_id": str(entry.teacher_id) if entry.teacher_id else None,
                    "day_of_week": entry.day_of_week,
                    "period_number": entry.period_number,
                    "start_time": entry.start_time,
                    "end_time": entry.end_time,
                    "subject_name": subject_name,
                    "teacher_name": None,
                    "section_name": section_name,
                    "class_name": class_name,
                }
            )
        return payload

    async def upsert_entry(self, section_id: str, year_id: str, school_id: str, data: dict) -> Timetable:
        existing_result = await self.db.execute(
            select(Timetable).where(
                Timetable.section_id == section_id,
                Timetable.academic_year_id == year_id,
                Timetable.day_of_week == data["day_of_week"],
                Timetable.period_number == data["period_number"],
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        model = Timetable(section_id=section_id, academic_year_id=year_id, school_id=school_id, **data)
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def delete_entry(self, timetable_id: str) -> None:
        await self.db.execute(delete(Timetable).where(Timetable.id == timetable_id))
        await self.db.flush()

    async def check_teacher_conflict(
        self,
        teacher_id: str,
        year_id: str,
        day: int,
        period: int,
        exclude_id: Optional[str] = None,
    ) -> bool:
        query = select(Timetable.id).where(
            Timetable.teacher_id == teacher_id,
            Timetable.academic_year_id == year_id,
            Timetable.day_of_week == day,
            Timetable.period_number == period,
        )
        if exclude_id:
            query = query.where(Timetable.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_teacher_conflict_details(self, teacher_id: str, year_id: str, day: int, period: int) -> Optional[dict]:
        result = await self.db.execute(
            select(Subject.name, Section.name, Class.name)
            .select_from(Timetable)
            .join(Subject, Subject.id == Timetable.subject_id)
            .join(Section, Section.id == Timetable.section_id)
            .join(Class, Class.id == Section.class_id)
            .where(
                Timetable.teacher_id == teacher_id,
                Timetable.academic_year_id == year_id,
                Timetable.day_of_week == day,
                Timetable.period_number == period,
            )
            .limit(1)
        )
        row = result.first()
        if not row:
            return None
        return {"subject_name": row[0], "section_name": row[1], "class_name": row[2]}

    async def check_room_conflict(
        self,
        room_number: str,
        year_id: str,
        day: int,
        period: int,
        exclude_id: Optional[str] = None,
    ) -> bool:
        query = (
            select(Timetable.id)
            .select_from(Timetable)
            .join(Section, Section.id == Timetable.section_id)
            .where(
                Section.room_number == room_number,
                Timetable.academic_year_id == year_id,
                Timetable.day_of_week == day,
                Timetable.period_number == period,
            )
        )
        if exclude_id:
            query = query.where(Timetable.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_room_conflict_details(self, room_number: str, year_id: str, day: int, period: int) -> Optional[dict]:
        result = await self.db.execute(
            select(Section.name, Class.name)
            .select_from(Timetable)
            .join(Section, Section.id == Timetable.section_id)
            .join(Class, Class.id == Section.class_id)
            .where(
                Section.room_number == room_number,
                Timetable.academic_year_id == year_id,
                Timetable.day_of_week == day,
                Timetable.period_number == period,
            )
            .limit(1)
        )
        row = result.first()
        if not row:
            return None
        return {"section_name": row[0], "class_name": row[1]}

    async def bulk_upsert(self, section_id: str, year_id: str, school_id: str, entries: list[dict]) -> int:
        count = 0
        for entry in entries:
            await self.upsert_entry(section_id, year_id, school_id, entry)
            count += 1
        return count

