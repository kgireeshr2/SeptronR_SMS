from datetime import datetime, time
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class SectionCreate(BaseModel):
    name: str
    capacity: int = 40
    class_teacher_id: Optional[UUID] = None
    room_number: Optional[str] = None


class SectionUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    class_teacher_id: Optional[UUID] = None
    room_number: Optional[str] = None
    is_active: Optional[bool] = None


class SectionResponse(BaseModel):
    id: UUID
    class_id: UUID
    name: str
    capacity: int
    class_teacher_id: Optional[UUID] = None
    class_teacher_name: Optional[str] = None
    room_number: Optional[str] = None
    is_active: bool
    student_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ClassCreate(BaseModel):
    name: str
    academic_year_id: UUID


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class ClassResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    academic_year_id: UUID
    is_active: bool
    created_at: datetime
    sections: Optional[List[SectionResponse]] = None
    student_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SubjectCreate(BaseModel):
    name: str
    code: Optional[str] = None
    is_elective: bool = False
    full_marks: int = 100
    pass_marks: int = 35


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    is_elective: Optional[bool] = None
    full_marks: Optional[int] = None
    pass_marks: Optional[int] = None
    is_active: Optional[bool] = None


class SubjectResponse(SubjectCreate):
    id: UUID
    school_id: UUID
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ClassSubjectAssign(BaseModel):
    subject_id: UUID
    teacher_id: Optional[UUID] = None


class ClassSubjectDetail(BaseModel):
    subject_id: UUID
    subject_name: str
    subject_code: Optional[str] = None
    teacher_id: Optional[UUID] = None
    teacher_name: Optional[str] = None


class ClassSubjectsResponse(BaseModel):
    class_id: UUID
    subjects: List[ClassSubjectDetail]


class DuplicateClassesRequest(BaseModel):
    from_year_id: UUID
    to_year_id: UUID


class TimetableEntryCreate(BaseModel):
    subject_id: UUID
    teacher_id: Optional[UUID] = None
    day_of_week: int = Field(ge=1, le=7)
    period_number: int = Field(ge=1)
    start_time: time
    end_time: time

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, value: time, info: ValidationInfo):
        start = info.data.get("start_time")
        if start and value <= start:
            raise ValueError("end_time must be greater than start_time")
        return value


class TimetableEntryResponse(TimetableEntryCreate):
    id: UUID
    section_id: UUID
    subject_name: str
    teacher_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TimetableGridResponse(BaseModel):
    section_id: UUID
    section_name: str
    class_name: str
    academic_year_id: UUID
    grid: Dict[int, Dict[int, Optional[TimetableEntryResponse]]]
    days: List[str]
    periods: List[int]


class TimetableBulkUpsertRequest(BaseModel):
    entries: List[TimetableEntryCreate]
