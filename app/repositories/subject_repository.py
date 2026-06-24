from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.classes import ClassSubject, Subject


class SubjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_school(self, school_id: str, active_only: bool = True) -> list[Subject]:
        query = select(Subject).where(Subject.school_id == school_id)
        if active_only:
            query = query.where(Subject.is_active == True)
        query = query.order_by(Subject.name.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, subject_id: str, school_id: Optional[str] = None) -> Optional[Subject]:
        query = select(Subject).where(Subject.id == subject_id)
        if school_id is not None:
            query = query.where(Subject.school_id == school_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, school_id: str, data: dict) -> Subject:
        model = Subject(school_id=school_id, **data)
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def update(self, subject_id: str, data: dict) -> Optional[Subject]:
        await self.db.execute(update(Subject).where(Subject.id == subject_id).values(**data))
        await self.db.flush()
        return await self.get_by_id(subject_id)

    async def soft_delete(self, subject_id: str) -> None:
        await self.db.execute(update(Subject).where(Subject.id == subject_id).values(is_active=False))
        await self.db.flush()

    async def get_subjects_for_class(self, class_id: str) -> list[dict]:
        result = await self.db.execute(
            select(
                ClassSubject.subject_id,
                Subject.name,
                Subject.code,
                ClassSubject.teacher_id,
                User.first_name,
                User.last_name,
            )
            .select_from(ClassSubject)
            .join(Subject, Subject.id == ClassSubject.subject_id)
            .outerjoin(User, User.id == ClassSubject.teacher_id)
            .where(ClassSubject.class_id == class_id)
            .order_by(Subject.name.asc())
        )
        payload: list[dict] = []
        for subject_id, subject_name, subject_code, teacher_id, first_name, last_name in result.all():
            teacher_name = " ".join([part for part in [first_name, last_name] if part]) or None
            payload.append(
                {
                    "subject_id": str(subject_id),
                    "subject_name": subject_name,
                    "subject_code": subject_code,
                    "teacher_id": str(teacher_id) if teacher_id else None,
                    "teacher_name": teacher_name,
                }
            )
        return payload

    async def assign_to_class(self, class_id: str, subject_id: str, teacher_id: Optional[str]) -> ClassSubject:
        existing = await self.db.execute(
            select(ClassSubject).where(ClassSubject.class_id == class_id, ClassSubject.subject_id == subject_id)
        )
        record = existing.scalar_one_or_none()
        if record:
            record.teacher_id = teacher_id
            await self.db.flush()
            await self.db.refresh(record)
            return record
        model = ClassSubject(class_id=class_id, subject_id=subject_id, teacher_id=teacher_id)
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def remove_from_class(self, class_id: str, subject_id: str) -> None:
        await self.db.execute(
            delete(ClassSubject).where(ClassSubject.class_id == class_id, ClassSubject.subject_id == subject_id)
        )
        await self.db.flush()

