"""
Service layer — Phase 9: Exam Management
Business logic: grade calculation, report cards, class rankings, publishing.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.exam_repository import ExamRepository
from app.models.exams import Exam, GradingScale
from app.schemas.phase9 import (
    ClassResultResponse,
    ClassResultRow,
    ExamMarkResponse,
    MarkEntryItem,
    ResultPublishRequest,
    ResultPublishResponse,
    StudentReportCard,
    SubjectResult,
)


class ExamService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ExamRepository(db)

    # ── Grade helper ──────────────────────────────────────────────────────

    def _compute_result(
        self,
        marks_obtained: Optional[float],
        pass_marks: int,
        full_marks: int,
        is_absent: bool,
        is_exempted: bool,
        grading_scale: Optional[GradingScale],
    ) -> dict[str, Any]:
        if is_absent:
            return {"grade": None, "grade_point": None, "percentage": None, "result": "Absent"}
        if is_exempted:
            return {"grade": "EX", "grade_point": None, "percentage": None, "result": "Exempted"}
        if marks_obtained is None:
            return {"grade": None, "grade_point": None, "percentage": None, "result": "Pending"}

        pct = round((float(marks_obtained) / full_marks) * 100, 2)
        result_str = "Pass" if float(marks_obtained) >= pass_marks else "Fail"

        grade_info = {"grade": None, "grade_point": 0.0}
        if grading_scale:
            grade_info = self.repo.calculate_grade(grading_scale, pct)

        return {
            "percentage": pct,
            "grade": grade_info.get("grade"),
            "grade_point": grade_info.get("grade_point"),
            "result": result_str,
        }

    # ── Mark entry ────────────────────────────────────────────────────────

    async def enter_marks(
        self,
        school_id: str,
        exam_id: str,
        entries: list[MarkEntryItem],
        entered_by: str,
    ) -> list[ExamMarkResponse]:
        """Upsert marks and return computed responses with grades."""
        exam = await self.repo.get_exam(school_id, exam_id)
        if not exam:
            raise ValueError("Exam not found")

        grading_scale = await self.repo.get_grading_scale(school_id)
        students = {str(s.id): s for s in await self.repo.get_students_for_exam(exam)}

        entries_data: list[dict] = []
        responses: list[ExamMarkResponse] = []

        for entry in entries:
            computed = self._compute_result(
                entry.marks_obtained,
                exam.pass_marks,
                exam.full_marks,
                entry.is_absent,
                entry.is_exempted,
                grading_scale,
            )
            entries_data.append(
                {
                    "student_id": entry.student_id,
                    "marks_obtained": entry.marks_obtained,
                    "is_absent": entry.is_absent,
                    "is_exempted": entry.is_exempted,
                    "grade": computed.get("grade"),
                    "remarks": entry.remarks,
                }
            )

            student = students.get(str(entry.student_id))
            responses.append(
                ExamMarkResponse(
                    student_id=entry.student_id,
                    student_name=f"{student.first_name} {student.last_name}" if student else "Unknown",
                    admission_number=student.admission_number if student else "",
                    roll_number=None,
                    marks_obtained=entry.marks_obtained,
                    full_marks=exam.full_marks,
                    pass_marks=exam.pass_marks,
                    grade=computed.get("grade"),
                    grade_point=computed.get("grade_point"),
                    percentage=computed.get("percentage"),
                    is_absent=entry.is_absent,
                    is_exempted=entry.is_exempted,
                    result=computed["result"],
                )
            )

        await self.repo.bulk_upsert_marks(school_id, exam_id, entries_data, entered_by)
        return responses

    # ── Class results ─────────────────────────────────────────────────────

    async def get_class_results(
        self,
        school_id: str,
        exam_type_id: str,
        class_id: str,
        year_id: str,
    ) -> ClassResultResponse:
        """Aggregate marks across all subjects for a class and compute ranks."""
        exams = await self.repo.list_exams(
            school_id,
            year_id=year_id,
            class_id=class_id,
            exam_type_id=exam_type_id,
        )
        if not exams:
            return ClassResultResponse(
                exam_type_name="",
                class_name="",
                academic_year_name="",
                results=[],
                total_students=0,
                passed_students=0,
                failed_students=0,
                class_average=0.0,
            )

        grading_scale = await self.repo.get_grading_scale(school_id)

        # Collect all marks — keyed by student_id → {exam_id: mark}
        student_marks: dict[str, dict[str, Any]] = {}
        subject_map: dict[str, Any] = {}

        for exam in exams:
            subject_map[str(exam.id)] = {
                "name": exam.name,
                "full_marks": exam.full_marks,
                "pass_marks": exam.pass_marks,
            }
            marks = await self.repo.get_marks_for_exam(str(exam.id))
            for m in marks:
                sid = str(m.student_id)
                if sid not in student_marks:
                    student_marks[sid] = {}
                student_marks[sid][str(exam.id)] = m

        # Load students
        students = {str(s.id): s for s in await self.repo.get_students_for_exam(exams[0])}

        rows: list[ClassResultRow] = []
        for sid, student in students.items():
            subj_results: list[dict] = []
            total = 0.0
            total_full = 0
            all_pass = True
            has_marks = False

            for exam in exams:
                eid = str(exam.id)
                mark = student_marks.get(sid, {}).get(eid)
                if mark:
                    has_marks = True
                    computed = self._compute_result(
                        float(mark.marks_obtained) if mark.marks_obtained else None,
                        exam.pass_marks,
                        exam.full_marks,
                        mark.is_absent,
                        mark.is_exempted,
                        grading_scale,
                    )
                    if computed["result"] == "Fail":
                        all_pass = False
                    if computed.get("percentage") is not None:
                        total += float(mark.marks_obtained or 0)
                        total_full += exam.full_marks
                    subj_results.append(
                        {
                            "subject_name": exam.name,
                            "marks": float(mark.marks_obtained) if mark.marks_obtained else None,
                            "full_marks": exam.full_marks,
                            "grade": computed.get("grade"),
                            "result": computed["result"],
                        }
                    )
                else:
                    subj_results.append(
                        {
                            "subject_name": exam.name,
                            "marks": None,
                            "full_marks": exam.full_marks,
                            "grade": None,
                            "result": "Pending",
                        }
                    )
                    total_full += exam.full_marks

            pct = round((total / total_full) * 100, 2) if total_full else 0.0
            grade_info = self.repo.calculate_grade(grading_scale, pct) if grading_scale else {}

            rows.append(
                ClassResultRow(
                    rank=0,  # computed after sorting
                    student_id=student.id,
                    student_name=f"{student.first_name} {student.last_name}",
                    admission_number=student.admission_number,
                    roll_number=None,
                    subject_marks=subj_results,
                    total_marks=total,
                    total_full_marks=total_full,
                    percentage=pct,
                    overall_grade=grade_info.get("grade"),
                    is_pass=all_pass and has_marks,
                )
            )

        # Sort and assign ranks
        rows.sort(key=lambda r: r.percentage, reverse=True)
        for i, row in enumerate(rows):
            row.rank = i + 1

        passed = sum(1 for r in rows if r.is_pass)
        avg = round(sum(r.percentage for r in rows) / len(rows), 2) if rows else 0.0

        return ClassResultResponse(
            exam_type_name=exams[0].name.split(" - ")[0] if exams else "",
            class_name="",
            academic_year_name="",
            results=rows,
            total_students=len(rows),
            passed_students=passed,
            failed_students=len(rows) - passed,
            class_average=avg,
        )

    # ── Publish results ───────────────────────────────────────────────────

    async def publish_results(
        self,
        school_id: str,
        data: ResultPublishRequest,
    ) -> ResultPublishResponse:
        updated = await self.repo.publish_exams(
            school_id,
            str(data.exam_type_id),
            str(data.class_id),
            str(data.year_id),
        )
        notified = 0
        if data.notify_parents and updated:
            # Enqueue Celery task (optional — graceful if Celery not configured)
            try:
                from app.tasks.exam_tasks import send_result_notification_bulk
                send_result_notification_bulk.delay(
                    str(data.exam_type_id), str(data.class_id), str(data.year_id), school_id
                )
                notified = updated  # approximate
            except Exception:
                pass

        return ResultPublishResponse(
            published=True, exams_updated=updated, students_notified=notified
        )

