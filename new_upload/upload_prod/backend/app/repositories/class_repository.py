from typing import Optional

from sqlalchemy import and_, delete as sa_delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import User
from app.models.classes import Class, Section


class ClassRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_school_year(self, school_id: str, year_id: str) -> list[Class]:
        result = await self.db.execute(
            select(Class)
            .where(
                Class.school_id == school_id,
                Class.academic_year_id == year_id,
                Class.is_active == True,
            )
            .order_by(Class.name.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(
        self, class_id: str, with_sections: bool = False, school_id: Optional[str] = None
    ) -> Optional[Class]:
        query = select(Class).where(Class.id == class_id)
        if school_id is not None:
            query = query.where(Class.school_id == school_id)
        if with_sections:
            query = query.options(selectinload(Class.sections))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, school_id: str, data: dict) -> Class:
        model = Class(school_id=school_id, **data)
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def update(self, class_id: str, data: dict) -> Optional[Class]:
        await self.db.execute(update(Class).where(Class.id == class_id).values(**data))
        await self.db.flush()
        return await self.get_by_id(class_id)

    async def soft_delete(self, class_id: str) -> None:
        await self.db.execute(update(Class).where(Class.id == class_id).values(is_active=False))
        await self.db.flush()

    async def hard_delete(self, class_id: str) -> None:
        await self.db.execute(sa_delete(Class).where(Class.id == class_id))
        await self.db.flush()

    async def count_students(self, class_id: str, year_id: str) -> int:
        return 0

    async def list_with_student_counts(self, school_id: str, year_id: str) -> list[dict]:
        classes = await self.list_by_school_year(school_id, year_id)
        response: list[dict] = []
        for class_item in classes:
            sections_raw = await self.db.execute(
                select(Section)
                .where(Section.class_id == class_item.id, Section.is_active == True)
                .order_by(Section.name.asc())
            )
            sections = [
                {
                    "id": str(s.id),
                    "class_id": str(s.class_id),
                    "name": s.name,
                    "capacity": s.capacity,
                    "room_number": s.room_number,
                    "is_active": s.is_active,
                }
                for s in sections_raw.scalars().all()
            ]
            response.append(
                {
                    "id": str(class_item.id),
                    "school_id": str(class_item.school_id),
                    "academic_year_id": str(class_item.academic_year_id),
                    "name": class_item.name,
                    "is_active": class_item.is_active,
                    "created_at": class_item.created_at,
                    "student_count": 0,
                    "sections": sections,
                }
            )
        return response


class SectionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_class(self, class_id: str) -> list[Section]:
        result = await self.db.execute(
            select(Section)
            .where(Section.class_id == class_id, Section.is_active == True)
            .order_by(Section.name.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, section_id: str, school_id: Optional[str] = None) -> Optional[Section]:
        query = select(Section).where(Section.id == section_id)
        if school_id is not None:
            # Section.school_id may be null on legacy rows — scope via the parent class.
            query = query.join(Class, Class.id == Section.class_id).where(Class.school_id == school_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, class_id: str, data: dict) -> Section:
        section = Section(class_id=class_id, **data)
        self.db.add(section)
        await self.db.flush()
        await self.db.refresh(section)
        return section

    async def update(self, section_id: str, data: dict) -> Optional[Section]:
        await self.db.execute(update(Section).where(Section.id == section_id).values(**data))
        await self.db.flush()
        return await self.get_by_id(section_id)

    async def soft_delete(self, section_id: str) -> None:
        await self.db.execute(update(Section).where(Section.id == section_id).values(is_active=False))
        await self.db.flush()

    async def get_class_teacher_sections(self, teacher_user_id: str, year_id: str) -> list[Section]:
        result = await self.db.execute(
            select(Section)
            .join(Class, Class.id == Section.class_id)
            .where(
                Section.class_teacher_id == teacher_user_id,
                Class.academic_year_id == year_id,
                Section.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def list_with_teacher_name(self, class_id: str) -> list[dict]:
        result = await self.db.execute(
            select(
                Section,
                User.first_name,
                User.last_name,
            )
            .select_from(Section)
            .outerjoin(User, User.id == Section.class_teacher_id)
            .where(Section.class_id == class_id, Section.is_active == True)
            .order_by(Section.name.asc())
        )
        payload: list[dict] = []
        for section, first_name, last_name in result.all():
            teacher_name = " ".join([part for part in [first_name, last_name] if part]) or None
            payload.append(
                {
                    "id": str(section.id),
                    "class_id": str(section.class_id),
                    "name": section.name,
                    "capacity": section.capacity,
                    "class_teacher_id": str(section.class_teacher_id) if section.class_teacher_id else None,
                    "class_teacher_name": teacher_name,
                    "room_number": section.room_number,
                    "is_active": section.is_active,
                    "student_count": 0,
                }
            )
        return payload

    async def get_room_for_section(self, section_id: str) -> Optional[str]:
        result = await self.db.execute(select(Section.room_number).where(Section.id == section_id, Section.is_active == True))
        return result.scalar_one_or_none()

    async def duplicate_sections(self, from_class_id: str, to_class_id: str) -> int:
        source_sections = await self.list_by_class(from_class_id)
        created = 0
        for source in source_sections:
            existing = await self.db.execute(
                select(Section.id).where(Section.class_id == to_class_id, Section.name == source.name)
            )
            if existing.scalar_one_or_none():
                continue
            self.db.add(
                Section(
                    class_id=to_class_id,
                    name=source.name,
                    capacity=source.capacity,
                    class_teacher_id=source.class_teacher_id,
                    room_number=source.room_number,
                    is_active=True,
                )
            )
            created += 1
        await self.db.flush()
        return created

