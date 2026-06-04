"""
Repository layer — Phase 9: Exam Management
All DB queries for exam_types, exams, student_marks, grading_scales.
"""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exams import (
    AdmitCardConfig,
    Exam,
    ExamType,
    GradingScale,
    ReportCardTemplate,
    StudentMark,
)
from app.models.students import Student, StudentEnrollment
from app.models.classes import Subject


class ExamRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Exam Types ────────────────────────────────────────────────────────

    async def list_exam_types(self, school_id: str) -> list[ExamType]:
        result = await self.db.execute(
            select(ExamType)
            .where(ExamType.school_id == school_id)
            .order_by(ExamType.name)
        )
        return list(result.scalars().all())

    async def get_exam_type(self, school_id: str, exam_type_id: str) -> Optional[ExamType]:
        result = await self.db.execute(
            select(ExamType).where(
                ExamType.school_id == school_id,
                ExamType.id == exam_type_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_exam_type(self, school_id: str, data: dict) -> ExamType:
        obj = ExamType(school_id=school_id, **data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update_exam_type(self, obj: ExamType, data: dict) -> ExamType:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete_exam_type(self, obj: ExamType) -> None:
        await self.db.delete(obj)
        await self.db.commit()

    # ── Grading Scale ─────────────────────────────────────────────────────

    async def get_grading_scale(self, school_id: str) -> Optional[GradingScale]:
        result = await self.db.execute(
            select(GradingScale).where(GradingScale.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def upsert_grading_scale(self, school_id: str, data: dict) -> GradingScale:
        obj = await self.get_grading_scale(school_id)
        if obj:
            for k, v in data.items():
                setattr(obj, k, v)
        else:
            obj = GradingScale(school_id=school_id, **data)
            self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    def calculate_grade(self, grading_scale: GradingScale, percentage: float) -> dict[str, Any]:
        """Return grade dict matching the percentage from the JSONB ranges."""
        for r in grading_scale.ranges:
            min_pct = float(r.get("min_pct", 0))
            max_pct = float(r.get("max_pct", 100))
            if min_pct <= percentage <= max_pct:
                return {
                    "grade": r.get("grade"),
                    "grade_point": float(r.get("grade_point", 0)),
                    "description": r.get("description"),
                }
        return {"grade": None, "grade_point": 0.0, "description": None}

    # ── Exams ─────────────────────────────────────────────────────────────

    async def create_exam(self, school_id: str, data: dict) -> Exam:
        obj = Exam(school_id=school_id, **data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def bulk_create_exams(self, school_id: str, exams_data: list[dict]) -> list[Exam]:
        objs = [Exam(school_id=school_id, **d) for d in exams_data]
        self.db.add_all(objs)
        await self.db.commit()
        for o in objs:
            await self.db.refresh(o)
        return objs

    async def get_exam(self, school_id: str, exam_id: str) -> Optional[Exam]:
        result = await self.db.execute(
            select(Exam).where(Exam.school_id == school_id, Exam.id == exam_id)
        )
        return result.scalar_one_or_none()

    async def list_exams(
        self,
        school_id: str,
        year_id: Optional[str] = None,
        class_id: Optional[str] = None,
        exam_type_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[Exam]:
        q = select(Exam).where(Exam.school_id == school_id)
        if year_id:
            q = q.where(Exam.academic_year_id == year_id)
        if class_id:
            q = q.where(Exam.class_id == class_id)
        if exam_type_id:
            q = q.where(Exam.exam_type_id == exam_type_id)
        if status:
            q = q.where(Exam.status == status)
        q = q.order_by(Exam.exam_date, Exam.name)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def update_exam(self, obj: Exam, data: dict) -> Exam:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete_exam(self, obj: Exam) -> None:
        await self.db.delete(obj)
        await self.db.commit()

    # ── Marks ─────────────────────────────────────────────────────────────

    async def get_marks_for_exam(self, exam_id: str) -> list[StudentMark]:
        result = await self.db.execute(
            select(StudentMark).where(StudentMark.exam_id == exam_id)
        )
        return list(result.scalars().all())

    async def bulk_upsert_marks(
        self, school_id: str, exam_id: str, entries: list[dict], entered_by: str
    ) -> int:
        """Insert or update marks for students. Returns count of rows affected."""
        count = 0
        for entry in entries:
            student_id = str(entry["student_id"])
            # Try to load existing
            result = await self.db.execute(
                select(StudentMark).where(
                    StudentMark.exam_id == exam_id,
                    StudentMark.student_id == student_id,
                )
            )
            obj = result.scalar_one_or_none()
            if obj:
                obj.marks_obtained = entry.get("marks_obtained")
                obj.is_absent = entry.get("is_absent", False)
                obj.is_exempted = entry.get("is_exempted", False)
                obj.grade = entry.get("grade")
                obj.remarks = entry.get("remarks")
                obj.updated_by = entered_by
            else:
                obj = StudentMark(
                    school_id=school_id,
                    exam_id=exam_id,
                    student_id=student_id,
                    marks_obtained=entry.get("marks_obtained"),
                    is_absent=entry.get("is_absent", False),
                    is_exempted=entry.get("is_exempted", False),
                    grade=entry.get("grade"),
                    remarks=entry.get("remarks"),
                    entered_by=entered_by,
                )
                self.db.add(obj)
            count += 1
        await self.db.commit()
        return count

    async def get_students_for_exam(self, exam: Exam) -> list[Student]:
        """Return students enrolled in exam's class (optionally section)."""
        q = (
            select(Student)
            .join(StudentEnrollment, StudentEnrollment.student_id == Student.id)
            .where(
                StudentEnrollment.academic_year_id == exam.academic_year_id,
                StudentEnrollment.class_id == exam.class_id,
                Student.is_active == True,
            )
        )
        if exam.section_id:
            q = q.where(StudentEnrollment.section_id == exam.section_id)
        q = q.order_by(Student.first_name, Student.last_name)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def publish_exams(
        self, school_id: str, exam_type_id: str, class_id: str, year_id: str
    ) -> int:
        """Set status = results_published for matching exams."""
        result = await self.db.execute(
            update(Exam)
            .where(
                Exam.school_id == school_id,
                Exam.exam_type_id == exam_type_id,
                Exam.class_id == class_id,
                Exam.academic_year_id == year_id,
            )
            .values(status="results_published")
        )
        await self.db.commit()
        return result.rowcount  # type: ignore[return-value]

    # ── Report Card Templates ─────────────────────────────────────────────

    async def list_report_card_templates(self, school_id: str) -> list[ReportCardTemplate]:
        result = await self.db.execute(
            select(ReportCardTemplate)
            .where(ReportCardTemplate.school_id == school_id)
            .order_by(ReportCardTemplate.template_name)
        )
        return list(result.scalars().all())

    async def create_report_card_template(self, school_id: str, data: dict) -> ReportCardTemplate:
        obj = ReportCardTemplate(school_id=school_id, **data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_report_card_template(
        self, school_id: str, template_id: str
    ) -> Optional[ReportCardTemplate]:
        result = await self.db.execute(
            select(ReportCardTemplate).where(
                ReportCardTemplate.school_id == school_id,
                ReportCardTemplate.id == template_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_report_card_template(
        self, obj: ReportCardTemplate, data: dict
    ) -> ReportCardTemplate:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    # ── Admit Card Configs ────────────────────────────────────────────────

    async def list_admit_card_configs(self, school_id: str) -> list[AdmitCardConfig]:
        result = await self.db.execute(
            select(AdmitCardConfig)
            .where(AdmitCardConfig.school_id == school_id)
            .order_by(AdmitCardConfig.template_name)
        )
        return list(result.scalars().all())

    async def create_admit_card_config(self, school_id: str, data: dict) -> AdmitCardConfig:
        obj = AdmitCardConfig(school_id=school_id, **data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_admit_card_config(
        self, school_id: str, config_id: str
    ) -> Optional[AdmitCardConfig]:
        result = await self.db.execute(
            select(AdmitCardConfig).where(
                AdmitCardConfig.school_id == school_id,
                AdmitCardConfig.id == config_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_admit_card_config(
        self, obj: AdmitCardConfig, data: dict
    ) -> AdmitCardConfig:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

