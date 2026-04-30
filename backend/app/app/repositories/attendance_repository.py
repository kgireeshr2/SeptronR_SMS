from datetime import date, datetime
from typing import Dict, List, Optional

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceSession, Holiday, SessionType, StaffAttendance, StudentAttendance
from app.models.students import Student, StudentEnrollment
from app.models.staff import Staff


class AttendanceRepository:
    @staticmethod
    async def get_or_create_session(
        db: AsyncSession,
        school_id: str,
        class_id: str,
        section_id: str,
        academic_year_id: str,
        date_: date,
        session_type: SessionType,
        taken_by: str,
    ) -> AttendanceSession:
        result = await db.execute(
            select(AttendanceSession).where(
                AttendanceSession.school_id == school_id,
                AttendanceSession.section_id == section_id,
                AttendanceSession.date == date_,
                AttendanceSession.session_type == session_type,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        session = AttendanceSession(
            school_id=school_id,
            class_id=class_id,
            section_id=section_id,
            date=date_,
            session_type=session_type,
            taken_by=taken_by,
            is_finalized=False,
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)
        return session

    @staticmethod
    async def bulk_upsert_student_attendance(
        db: AsyncSession,
        school_id: str,
        session_id: str,
        entries: list,
    ) -> int:
        affected = 0
        for entry in entries:
            result = await db.execute(
                select(StudentAttendance).where(
                    StudentAttendance.session_id == session_id,
                    StudentAttendance.student_id == entry["student_id"],
                )
            )
            row = result.scalar_one_or_none()
            if row:
                row.status = entry["status"]
                row.remarks = entry.get("remarks")
                row.updated_at = datetime.utcnow()
            else:
                row = StudentAttendance(
                    school_id=school_id,
                    session_id=session_id,
                    student_id=entry["student_id"],
                    status=entry["status"],
                    remarks=entry.get("remarks"),
                )
                db.add(row)
            affected += 1
        await db.flush()
        return affected

    @staticmethod
    async def get_section_session(
        db: AsyncSession,
        school_id: str,
        section_id: str,
        date_: date,
        session_type: SessionType,
    ) -> Optional[AttendanceSession]:
        result = await db.execute(
            select(AttendanceSession).where(
                AttendanceSession.school_id == school_id,
                AttendanceSession.section_id == section_id,
                AttendanceSession.date == date_,
                AttendanceSession.session_type == session_type,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_session_entries(
        db: AsyncSession,
        school_id: str,
        session_id: str,
    ) -> List[dict]:
        result = await db.execute(
            select(StudentAttendance, Student)
            .join(Student, Student.id == StudentAttendance.student_id)
            .where(
                StudentAttendance.school_id == school_id,
                StudentAttendance.session_id == session_id,
            )
            .order_by(Student.first_name, Student.last_name)
        )
        rows = []
        for attendance, student in result.all():
            rows.append(
                {
                    "id": str(attendance.id),
                    "student_id": str(student.id),
                    "student_name": f"{student.first_name} {student.last_name}",
                    "admission_number": student.admission_number,
                    "status": attendance.status,
                    "remarks": attendance.remarks,
                    "marked_at": attendance.updated_at,
                }
            )
        return rows

    @staticmethod
    async def get_student_summary(
        db: AsyncSession,
        school_id: str,
        student_id: str,
        from_date: date,
        to_date: date,
        threshold: float = 75,
    ) -> dict:
        result = await db.execute(
            select(StudentAttendance.status, func.count(StudentAttendance.id))
            .join(AttendanceSession, AttendanceSession.id == StudentAttendance.session_id)
            .where(
                StudentAttendance.school_id == school_id,
                StudentAttendance.student_id == student_id,
                AttendanceSession.date >= from_date,
                AttendanceSession.date <= to_date,
            )
            .group_by(StudentAttendance.status)
        )
        counts = {status.value: count for status, count in result.all()}

        student_row = await db.execute(
            select(Student).where(Student.id == student_id, Student.school_id == school_id)
        )
        student = student_row.scalar_one_or_none()

        present = counts.get("present", 0)
        late = counts.get("late", 0)
        half_day = counts.get("half_day", 0)
        leave = counts.get("leave", 0)
        absent = counts.get("absent", 0)
        total = present + late + half_day + leave + absent
        pct = ((present + late + (half_day * 0.5)) / total * 100) if total else 0.0

        return {
            "student_id": student_id,
            "student_name": f"{student.first_name} {student.last_name}" if student else None,
            "total_working_days": total,
            "days_present": present,
            "days_absent": absent,
            "days_late": late,
            "days_leave": leave,
            "attendance_pct": round(pct, 2),
            "is_low": pct < threshold,
        }

    @staticmethod
    async def get_students_by_filters(
        db: AsyncSession,
        school_id: str,
        academic_year_id: str,
        class_id: Optional[str] = None,
        section_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> List[str]:
        query = (
            select(Student.id)
            .join(StudentEnrollment, StudentEnrollment.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                Student.is_active == True,
                StudentEnrollment.school_id == school_id,
                StudentEnrollment.academic_year_id == academic_year_id,
                StudentEnrollment.is_current == True,
            )
        )
        if class_id:
            query = query.where(StudentEnrollment.class_id == class_id)
        if section_id:
            query = query.where(StudentEnrollment.section_id == section_id)
        if student_id:
            query = query.where(Student.id == student_id)

        result = await db.execute(query.order_by(Student.first_name, Student.last_name))
        return [str(row[0]) for row in result.all()]

    @staticmethod
    async def get_students_in_section(
        db: AsyncSession,
        school_id: str,
        academic_year_id: str,
        section_id: str,
    ) -> List[dict]:
        result = await db.execute(
            select(Student.id, Student.first_name, Student.last_name, Student.admission_number)
            .join(StudentEnrollment, StudentEnrollment.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                Student.is_active == True,
                StudentEnrollment.school_id == school_id,
                StudentEnrollment.academic_year_id == academic_year_id,
                StudentEnrollment.section_id == section_id,
                StudentEnrollment.is_current == True,
            )
            .order_by(Student.first_name, Student.last_name)
        )
        return [
            {
                "student_id": str(row[0]),
                "student_name": f"{row[1]} {row[2]}",
                "admission_number": row[3],
            }
            for row in result.all()
        ]

    @staticmethod
    async def get_low_attendance(
        db: AsyncSession,
        school_id: str,
        academic_year_id: str,
        threshold: float,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[dict]:
        student_ids = await AttendanceRepository.get_students_by_filters(
            db,
            school_id=school_id,
            academic_year_id=academic_year_id,
        )
        out = []
        if not student_ids:
            return out

        start = from_date or date(date.today().year, 1, 1)
        end = to_date or date.today()
        for student_id in student_ids:
            summary = await AttendanceRepository.get_student_summary(
                db,
                school_id,
                student_id,
                start,
                end,
                threshold=threshold,
            )
            if summary["attendance_pct"] < threshold:
                out.append(summary)
        return out

    @staticmethod
    async def get_monthly_sheet_data(
        db: AsyncSession,
        school_id: str,
        section_id: str,
        academic_year_id: str,
        month: int,
        year: int,
    ) -> dict:
        students = await AttendanceRepository.get_students_in_section(
            db, school_id=school_id, academic_year_id=academic_year_id, section_id=section_id
        )

        result = await db.execute(
            select(
                StudentAttendance.student_id,
                AttendanceSession.date,
                StudentAttendance.status,
            )
            .join(AttendanceSession, AttendanceSession.id == StudentAttendance.session_id)
            .where(
                StudentAttendance.school_id == school_id,
                AttendanceSession.school_id == school_id,
                AttendanceSession.section_id == section_id,
                extract("month", AttendanceSession.date) == month,
                extract("year", AttendanceSession.date) == year,
            )
        )

        cell_map: Dict[str, Dict[str, str]] = {}
        dates = set()
        for student_id, att_date, status in result.all():
            sid = str(student_id)
            d = att_date.isoformat()
            dates.add(d)
            cell_map.setdefault(sid, {})[d] = status.value if hasattr(status, "value") else str(status)

        return {
            "students": students,
            "dates": sorted(dates),
            "cell_map": cell_map,
        }

    @staticmethod
    async def get_holidays(
        db: AsyncSession,
        school_id: str,
        academic_year_id: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[Holiday]:
        query = select(Holiday).where(Holiday.school_id == school_id)
        if academic_year_id:
            query = query.where(Holiday.academic_year_id == academic_year_id)
        if from_date:
            query = query.where(Holiday.date >= from_date)
        if to_date:
            query = query.where(Holiday.date <= to_date)
        query = query.order_by(Holiday.date.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_holiday_by_id(db: AsyncSession, school_id: str, holiday_id: str) -> Optional[Holiday]:
        result = await db.execute(
            select(Holiday).where(Holiday.school_id == school_id, Holiday.id == holiday_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_holiday_by_date(db: AsyncSession, school_id: str, date_: date) -> Optional[Holiday]:
        result = await db.execute(
            select(Holiday).where(Holiday.school_id == school_id, Holiday.date == date_)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_holiday(db: AsyncSession, school_id: str, payload: dict) -> Holiday:
        holiday = Holiday(school_id=school_id, **payload)
        db.add(holiday)
        await db.flush()
        await db.refresh(holiday)
        return holiday

    @staticmethod
    async def update_holiday(db: AsyncSession, holiday: Holiday, payload: dict) -> Holiday:
        for field, value in payload.items():
            setattr(holiday, field, value)
        await db.flush()
        await db.refresh(holiday)
        return holiday

    @staticmethod
    async def delete_holiday(db: AsyncSession, holiday: Holiday) -> None:
        await db.delete(holiday)
        await db.flush()


class StaffAttendanceRepository:
    @staticmethod
    async def bulk_upsert(
        db: AsyncSession,
        school_id: str,
        entries: list,
    ) -> int:
        affected = 0
        for entry in entries:
            result = await db.execute(
                select(StaffAttendance).where(
                    StaffAttendance.school_id == school_id,
                    StaffAttendance.staff_id == entry["staff_id"],
                    StaffAttendance.date == entry["date"],
                )
            )
            row = result.scalar_one_or_none()
            if row:
                row.status = entry["status"]
                row.check_in = entry.get("check_in")
                row.check_out = entry.get("check_out")
                row.source = entry.get("source", row.source)
                row.remarks = entry.get("remarks")
                row.updated_at = datetime.utcnow()
            else:
                row = StaffAttendance(
                    school_id=school_id,
                    staff_id=entry["staff_id"],
                    date=entry["date"],
                    status=entry["status"],
                    check_in=entry.get("check_in"),
                    check_out=entry.get("check_out"),
                    source=entry.get("source"),
                    remarks=entry.get("remarks"),
                )
                db.add(row)
            affected += 1
        await db.flush()
        return affected

    @staticmethod
    async def list_for_date(db: AsyncSession, school_id: str, date_: date) -> List[dict]:
        result = await db.execute(
            select(StaffAttendance, Staff)
            .join(Staff, Staff.id == StaffAttendance.staff_id)
            .where(StaffAttendance.school_id == school_id, StaffAttendance.date == date_)
            .order_by(Staff.first_name, Staff.last_name)
        )
        rows = []
        for attendance, staff in result.all():
            rows.append(
                {
                    "id": str(attendance.id),
                    "staff_id": str(staff.id),
                    "staff_name": f"{staff.first_name} {staff.last_name}",
                    "date": attendance.date,
                    "check_in": attendance.check_in,
                    "check_out": attendance.check_out,
                    "status": attendance.status,
                    "source": attendance.source,
                    "remarks": attendance.remarks,
                }
            )
        return rows

    @staticmethod
    async def get_staff_map_by_employee_ids(
        db: AsyncSession,
        school_id: str,
        employee_ids: List[str],
    ) -> Dict[str, Staff]:
        if not employee_ids:
            return {}
        result = await db.execute(
            select(Staff).where(
                Staff.school_id == school_id,
                Staff.employee_id.in_(employee_ids),
                Staff.deleted_at.is_(None),
            )
        )
        rows = result.scalars().all()
        return {str(row.employee_id).strip().lower(): row for row in rows}

    @staticmethod
    async def monthly_summary(db: AsyncSession, school_id: str, month: int, year: int) -> List[dict]:
        result = await db.execute(
            select(
                Staff.id,
                Staff.employee_id,
                Staff.first_name,
                Staff.last_name,
                StaffAttendance.status,
                func.count(StaffAttendance.id),
            )
            .join(StaffAttendance, StaffAttendance.staff_id == Staff.id, isouter=True)
            .where(
                Staff.school_id == school_id,
                Staff.deleted_at.is_(None),
                (extract("month", StaffAttendance.date) == month) | (StaffAttendance.date.is_(None)),
                (extract("year", StaffAttendance.date) == year) | (StaffAttendance.date.is_(None)),
            )
            .group_by(Staff.id, Staff.employee_id, Staff.first_name, Staff.last_name, StaffAttendance.status)
            .order_by(Staff.first_name, Staff.last_name)
        )

        grouped: Dict[str, dict] = {}
        for sid, emp_id, first_name, last_name, status, count in result.all():
            key = str(sid)
            if key not in grouped:
                grouped[key] = {
                    "staff_id": key,
                    "employee_id": emp_id,
                    "staff_name": f"{first_name} {last_name}",
                    "present": 0,
                    "absent": 0,
                    "late": 0,
                    "half_day": 0,
                    "on_leave": 0,
                    "holiday": 0,
                    "total_marked": 0,
                }
            if status is not None:
                status_key = status.value if hasattr(status, "value") else str(status)
                if status_key in grouped[key]:
                    grouped[key][status_key] += int(count)
                grouped[key]["total_marked"] += int(count)

        return list(grouped.values())

