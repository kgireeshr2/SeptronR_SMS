from datetime import date, datetime
import csv
import io
from calendar import monthrange
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.models.students import StudentEnrollment
from app.repositories.attendance_repository import AttendanceRepository, StaffAttendanceRepository
from app.schemas.phase7 import (
    AttendanceMarkRequest,
    AttendanceRecord,
    AttendanceReportParams,
    SectionAttendanceSummary,
    StaffAttendanceMarkRequest,
    StudentAttendanceSummary,
)


class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def mark_section_attendance(self, school_id: str, payload: AttendanceMarkRequest, marked_by: str) -> SectionAttendanceSummary:
        holiday = await AttendanceRepository.get_holiday_by_date(self.db, school_id, payload.date)
        if holiday:
            raise ValueError("Cannot mark attendance on a holiday")

        section_result = await self.db.execute(
            select(StudentEnrollment.class_id)
            .where(
                StudentEnrollment.school_id == school_id,
                StudentEnrollment.section_id == payload.section_id,
                StudentEnrollment.academic_year_id == payload.academic_year_id,
                StudentEnrollment.is_current == True,
            )
            .limit(1)
        )
        class_id = section_result.scalar_one_or_none()
        if not class_id:
            raise ValueError("No active students found for section/year")

        session = await AttendanceRepository.get_or_create_session(
            self.db,
            school_id=school_id,
            class_id=str(class_id),
            section_id=payload.section_id,
            academic_year_id=payload.academic_year_id,
            date_=payload.date,
            session_type=payload.session_type,
            taken_by=marked_by,
        )

        await AttendanceRepository.bulk_upsert_student_attendance(
            self.db,
            school_id=school_id,
            session_id=str(session.id),
            entries=[entry.model_dump() for entry in payload.entries],
        )

        entries = await AttendanceRepository.get_session_entries(self.db, school_id, str(session.id))

        present = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "present")
        absent = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "absent")
        late = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "late")
        half_day = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "half_day")
        leave = sum(1 for e in entries if getattr(e["status"], "value", e["status"]) == "leave")
        total = len(entries)
        attendance_pct = round(((present + late + (half_day * 0.5)) / total * 100), 2) if total else 0.0

        return SectionAttendanceSummary(
            section_id=payload.section_id,
            date=payload.date,
            session=payload.session_type,
            total=total,
            present=present,
            absent=absent,
            late=late,
            half_day=half_day,
            leave=leave,
            attendance_pct=attendance_pct,
            entries=[
                AttendanceRecord(
                    id=e["id"],
                    student_id=e["student_id"],
                    student_name=e["student_name"],
                    admission_number=e["admission_number"],
                    date=payload.date,
                    status=e["status"],
                    session=payload.session_type,
                    remarks=e["remarks"],
                    marked_at=e["marked_at"],
                )
                for e in entries
            ],
        )

    async def get_student_summary(
        self,
        school_id: str,
        student_id: str,
        from_date: date,
        to_date: date,
    ) -> StudentAttendanceSummary:
        summary = await AttendanceRepository.get_student_summary(
            self.db,
            school_id=school_id,
            student_id=student_id,
            from_date=from_date,
            to_date=to_date,
        )
        return StudentAttendanceSummary(**summary)

    async def mark_staff_attendance(
        self,
        school_id: str,
        payload: List[StaffAttendanceMarkRequest],
    ) -> int:
        return await StaffAttendanceRepository.bulk_upsert(
            self.db,
            school_id=school_id,
            entries=[entry.model_dump() for entry in payload],
        )

    async def get_attendance_report(
        self,
        school_id: str,
        params: AttendanceReportParams,
    ) -> List[StudentAttendanceSummary]:
        student_ids = await AttendanceRepository.get_students_by_filters(
            self.db,
            school_id=school_id,
            academic_year_id=params.academic_year_id,
            class_id=params.class_id,
            section_id=params.section_id,
            student_id=params.student_id,
        )

        summaries: List[StudentAttendanceSummary] = []
        for student_id in student_ids:
            summary = await self.get_student_summary(
                school_id=school_id,
                student_id=student_id,
                from_date=params.from_date,
                to_date=params.to_date,
            )

            if params.min_attendance_pct is not None and summary.attendance_pct < params.min_attendance_pct:
                continue
            if params.max_attendance_pct is not None and summary.attendance_pct > params.max_attendance_pct:
                continue
            if params.status and summary.total_working_days > 0:
                status_value = params.status.value
                if status_value == "absent" and summary.days_absent == 0:
                    continue
                if status_value == "late" and summary.days_late == 0:
                    continue
                if status_value == "leave" and summary.days_leave == 0:
                    continue

            summaries.append(summary)

        return summaries

    async def export_report_excel(
        self,
        school_id: str,
        params: AttendanceReportParams,
    ) -> bytes:
        from openpyxl import Workbook

        rows = await self.get_attendance_report(school_id, params)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Attendance Report"

        headers = [
            "Student ID",
            "Student Name",
            "Total Days",
            "Present",
            "Absent",
            "Late",
            "Leave",
            "Attendance %",
            "Low Attendance",
        ]
        sheet.append(headers)

        for row in rows:
            sheet.append(
                [
                    row.student_id,
                    row.student_name,
                    row.total_working_days,
                    row.days_present,
                    row.days_absent,
                    row.days_late,
                    row.days_leave,
                    row.attendance_pct,
                    "Yes" if row.is_low else "No",
                ]
            )

        stream = io.BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return stream.getvalue()

    async def generate_monthly_sheet_pdf(
        self,
        school_id: str,
        section_id: str,
        academic_year_id: str,
        month: int,
        year: int,
    ) -> bytes:
        data = await AttendanceRepository.get_monthly_sheet_data(
            self.db,
            school_id=school_id,
            section_id=section_id,
            academic_year_id=academic_year_id,
            month=month,
            year=year,
        )

        students = data["students"]
        cell_map = data["cell_map"]

        stream = io.BytesIO()
        pdf = canvas.Canvas(stream, pagesize=landscape(A4))
        width, height = landscape(A4)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(1.2 * cm, height - 1.2 * cm, f"Monthly Attendance Sheet - Section {section_id}")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(1.2 * cm, height - 1.8 * cm, f"Month: {month:02d}/{year} | Academic Year: {academic_year_id}")

        y = height - 3.0 * cm
        x_start = 1.2 * cm
        row_height = 0.55 * cm
        col_student = 6.0 * cm
        col_date = 0.75 * cm

        max_days = monthrange(year, month)[1]
        dates = [f"{year:04d}-{month:02d}-{d:02d}" for d in range(1, max_days + 1)]

        pdf.setFont("Helvetica-Bold", 7)
        pdf.drawString(x_start, y, "Student")
        x = x_start + col_student
        for date_str in dates:
            day = date_str[-2:]
            pdf.drawString(x, y, day)
            x += col_date
        y -= row_height

        pdf.setFont("Helvetica", 7)
        for student in students:
            if y < 1.5 * cm:
                pdf.showPage()
                y = height - 2.0 * cm
                pdf.setFont("Helvetica-Bold", 7)
                pdf.drawString(x_start, y, "Student")
                x = x_start + col_student
                for date_str in dates:
                    day = date_str[-2:]
                    pdf.drawString(x, y, day)
                    x += col_date
                y -= row_height
                pdf.setFont("Helvetica", 7)

            pdf.drawString(x_start, y, student["student_name"][:35])
            x = x_start + col_student
            sid = student["student_id"]
            row_map = cell_map.get(sid, {})
            for date_str in dates:
                status = row_map.get(date_str, "")
                symbol = {
                    "present": "P",
                    "absent": "A",
                    "late": "L",
                    "half_day": "H",
                    "leave": "LV",
                    "holiday": "HOL",
                }.get(status, "-")
                pdf.drawString(x, y, symbol)
                x += col_date

            y -= row_height

        pdf.save()
        stream.seek(0)
        return stream.getvalue()

    async def import_biometric_csv(
        self,
        school_id: str,
        date_: date,
        file_content: bytes,
    ) -> dict:
        content = file_content.decode("utf-8", errors="replace")
        rows = list(csv.DictReader(io.StringIO(content)))

        employee_ids = [str((row.get("employee_id") or "")).strip() for row in rows if row.get("employee_id")]
        staff_map = await StaffAttendanceRepository.get_staff_map_by_employee_ids(
            self.db,
            school_id=school_id,
            employee_ids=[eid.lower() for eid in employee_ids],
        )

        success_entries = []
        failed = []
        for row in rows:
            employee_id = str((row.get("employee_id") or "")).strip()
            if not employee_id:
                failed.append({"employee_id": "", "reason": "employee_id missing"})
                continue

            staff = staff_map.get(employee_id.lower())
            if not staff:
                failed.append({"employee_id": employee_id, "reason": "staff not found"})
                continue

            try:
                in_time_raw = str(row.get("in_time") or "").strip()
                out_time_raw = str(row.get("out_time") or "").strip()

                check_in = datetime.fromisoformat(in_time_raw) if in_time_raw else None
                check_out = datetime.fromisoformat(out_time_raw) if out_time_raw else None

                success_entries.append(
                    {
                        "staff_id": str(staff.id),
                        "date": date_,
                        "status": "present" if check_in else "absent",
                        "check_in": check_in,
                        "check_out": check_out,
                        "source": "biometric",
                        "remarks": None,
                    }
                )
            except Exception:
                failed.append({"employee_id": employee_id, "reason": "invalid datetime format"})

        count = 0
        if success_entries:
            count = await StaffAttendanceRepository.bulk_upsert(
                self.db,
                school_id=school_id,
                entries=success_entries,
            )

        return {
            "success": count,
            "failed": failed,
        }

