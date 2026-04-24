from datetime import date, datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models.attendance import AttendanceSource, HolidayType, SessionType, StaffAttendanceStatus, StudentAttendanceStatus


class AttendanceMarkEntry(BaseModel):
    student_id: str
    status: StudentAttendanceStatus = StudentAttendanceStatus.present
    remarks: Optional[str] = None


class AttendanceMarkRequest(BaseModel):
    section_id: str
    academic_year_id: str
    date: date
    session_type: SessionType = SessionType.full_day
    entries: List[AttendanceMarkEntry]


class AttendanceUpdateRequest(BaseModel):
    status: StudentAttendanceStatus
    remarks: Optional[str] = None


class AttendanceRecord(BaseModel):
    id: str
    student_id: str
    student_name: str
    admission_number: str
    date: date
    status: StudentAttendanceStatus
    session: SessionType
    remarks: Optional[str] = None
    marked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SectionAttendanceSummary(BaseModel):
    section_id: str
    date: date
    session: SessionType
    total: int
    present: int
    absent: int
    late: int
    half_day: int
    leave: int
    attendance_pct: float
    entries: List[AttendanceRecord]


class StudentAttendanceSummary(BaseModel):
    student_id: str
    student_name: Optional[str] = None
    total_working_days: int
    days_present: int
    days_absent: int
    days_late: int
    days_leave: int
    attendance_pct: float
    is_low: bool


class AttendanceReportParams(BaseModel):
    section_id: Optional[str] = None
    class_id: Optional[str] = None
    academic_year_id: str
    from_date: date
    to_date: date
    student_id: Optional[str] = None
    status: Optional[StudentAttendanceStatus] = None
    min_attendance_pct: Optional[float] = None
    max_attendance_pct: Optional[float] = None


class StaffAttendanceMarkRequest(BaseModel):
    staff_id: str
    date: date
    status: StaffAttendanceStatus = StaffAttendanceStatus.present
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    source: AttendanceSource = AttendanceSource.manual
    remarks: Optional[str] = None


class StaffAttendanceRecord(BaseModel):
    id: str
    staff_id: str
    staff_name: Optional[str] = None
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: StaffAttendanceStatus
    source: AttendanceSource
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HolidayCreate(BaseModel):
    academic_year_id: str
    name: str
    date: date
    holiday_type: HolidayType = HolidayType.school


class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    holiday_type: Optional[HolidayType] = None


class HolidayResponse(BaseModel):
    id: UUID
    school_id: UUID
    academic_year_id: UUID
    name: str
    date: date
    holiday_type: HolidayType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id", "school_id", "academic_year_id")
    def serialize_uuid(self, v: UUID, _info) -> str:
        return str(v)
