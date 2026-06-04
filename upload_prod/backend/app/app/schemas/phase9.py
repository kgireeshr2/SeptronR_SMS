"""
Pydantic v2 schemas — Phase 9: Exam Management
"""
from __future__ import annotations

from datetime import date, time
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ──────────────────────────────────────────────────────────────────────────
# Exam Types
# ──────────────────────────────────────────────────────────────────────────

class ExamTypeCreate(BaseModel):
    name: str = Field(..., max_length=100)
    weightage: float = Field(100.0, ge=0, le=100)
    is_active: bool = True


class ExamTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    weightage: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class ExamTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    weightage: float
    is_active: bool


# ──────────────────────────────────────────────────────────────────────────
# Grading Scales
# ──────────────────────────────────────────────────────────────────────────

class GradeRange(BaseModel):
    grade: str
    min_pct: float
    max_pct: float
    grade_point: float = 0.0
    description: Optional[str] = None


class GradingScaleUpsert(BaseModel):
    name: str = "Default"
    ranges: list[GradeRange]


class GradingScaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    ranges: list[dict[str, Any]]
    is_active: bool


# ──────────────────────────────────────────────────────────────────────────
# Exams
# ──────────────────────────────────────────────────────────────────────────

class ExamCreate(BaseModel):
    name: str = Field(..., max_length=200)
    academic_year_id: UUID
    term_id: Optional[UUID] = None
    exam_type_id: UUID
    class_id: UUID
    subject_id: UUID
    section_id: Optional[UUID] = None
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room_number: Optional[str] = Field(None, max_length=20)
    invigilator_id: Optional[UUID] = None
    full_marks: int = Field(100, ge=1, le=999)
    pass_marks: int = Field(35, ge=0, le=999)
    description: Optional[str] = None


class ExamSubjectEntry(BaseModel):
    subject_id: UUID
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    full_marks: int = Field(100, ge=1, le=999)
    pass_marks: int = Field(35, ge=0, le=999)


class ExamBulkCreate(BaseModel):
    """Create one exam row per subject for a class/exam_type combo."""
    academic_year_id: UUID
    term_id: Optional[UUID] = None
    exam_type_id: UUID
    class_id: UUID
    exam_name_prefix: str
    subjects: list[ExamSubjectEntry]


class ExamUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room_number: Optional[str] = None
    invigilator_id: Optional[UUID] = None
    full_marks: Optional[int] = None
    pass_marks: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ExamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    term_id: Optional[UUID]
    exam_type_id: UUID
    name: str
    class_id: UUID
    subject_id: UUID
    section_id: Optional[UUID]
    exam_date: Optional[date]
    start_time: Optional[time]
    end_time: Optional[time]
    room_number: Optional[str]
    invigilator_id: Optional[UUID]
    full_marks: int
    pass_marks: int
    status: str
    description: Optional[str]


# ──────────────────────────────────────────────────────────────────────────
# Marks Entry
# ──────────────────────────────────────────────────────────────────────────

class MarkEntryItem(BaseModel):
    student_id: UUID
    marks_obtained: Optional[float] = None
    is_absent: bool = False
    is_exempted: bool = False
    remarks: Optional[str] = None


class MarkEntryRequest(BaseModel):
    entries: list[MarkEntryItem]


class SubjectResult(BaseModel):
    subject_name: str
    subject_code: Optional[str] = None
    full_marks: int
    pass_marks: int
    marks_obtained: Optional[float]
    percentage: Optional[float]
    grade: Optional[str]
    grade_point: Optional[float]
    result: str  # Pass | Fail | Absent | Exempted


class ExamMarkResponse(BaseModel):
    student_id: UUID
    student_name: str
    admission_number: str
    roll_number: Optional[str]
    marks_obtained: Optional[float]
    full_marks: int
    pass_marks: int
    grade: Optional[str]
    grade_point: Optional[float]
    percentage: Optional[float]
    is_absent: bool
    is_exempted: bool
    result: str  # Pass | Fail | Absent | Exempted


# ──────────────────────────────────────────────────────────────────────────
# Report Card / Results
# ──────────────────────────────────────────────────────────────────────────

class StudentReportCard(BaseModel):
    student_id: UUID
    student_name: str
    admission_number: str
    class_name: str
    section_name: Optional[str]
    academic_year_name: str
    exam_type_name: str
    subjects: list[SubjectResult]
    total_marks: float
    total_full_marks: int
    overall_percentage: float
    overall_grade: Optional[str]
    overall_grade_point: Optional[float]
    rank: Optional[int]
    attendance_summary: Optional[dict[str, Any]]


class ClassResultRow(BaseModel):
    rank: int
    student_id: UUID
    student_name: str
    admission_number: str
    roll_number: Optional[str]
    subject_marks: list[dict[str, Any]]  # {subject_name, marks, full_marks, grade}
    total_marks: float
    total_full_marks: int
    percentage: float
    overall_grade: Optional[str]
    is_pass: bool


class ClassResultResponse(BaseModel):
    exam_type_name: str
    class_name: str
    academic_year_name: str
    results: list[ClassResultRow]
    total_students: int
    passed_students: int
    failed_students: int
    class_average: float


# ──────────────────────────────────────────────────────────────────────────
# Publish
# ──────────────────────────────────────────────────────────────────────────

class ResultPublishRequest(BaseModel):
    exam_type_id: UUID
    class_id: UUID
    year_id: UUID
    notify_parents: bool = True


class ResultPublishResponse(BaseModel):
    published: bool
    exams_updated: int
    students_notified: int


# ──────────────────────────────────────────────────────────────────────────
# Report Card Templates
# ──────────────────────────────────────────────────────────────────────────

class ReportCardTemplateCreate(BaseModel):
    template_name: str = Field(..., max_length=200)
    exam_type_id: Optional[UUID] = None
    layout_config: Optional[dict[str, Any]] = None
    is_default: bool = False


class ReportCardTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    template_name: str
    exam_type_id: Optional[UUID]
    layout_config: Optional[dict[str, Any]]
    is_default: bool


# ──────────────────────────────────────────────────────────────────────────
# Admit Card Configs
# ──────────────────────────────────────────────────────────────────────────

class AdmitCardConfigCreate(BaseModel):
    template_name: str = Field(..., max_length=200)
    show_photo: bool = True
    show_instructions: bool = True
    instructions: Optional[str] = None
    header_note: Optional[str] = None
    footer_note: Optional[str] = None
    is_default: bool = False


class AdmitCardConfigUpdate(BaseModel):
    template_name: Optional[str] = None
    show_photo: Optional[bool] = None
    show_instructions: Optional[bool] = None
    instructions: Optional[str] = None
    header_note: Optional[str] = None
    footer_note: Optional[str] = None
    is_default: Optional[bool] = None


class AdmitCardConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    template_name: str
    show_photo: bool
    show_instructions: bool
    instructions: Optional[str]
    header_note: Optional[str]
    footer_note: Optional[str]
    is_default: bool
