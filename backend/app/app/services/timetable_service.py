import csv
import io
from datetime import time
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.repositories.class_repository import SectionRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.timetable_repository import TimetableRepository


def _parse_time(value: str) -> time:
    raw = value.strip()
    parts = raw.split(":")
    if len(parts) < 2:
        raise ValueError("Invalid time format")
    hour = int(parts[0])
    minute = int(parts[1])
    return time(hour=hour, minute=minute)


class TimetableService:
    def __init__(
        self,
        timetable_repo: TimetableRepository,
        section_repo: SectionRepository,
        subject_repo: SubjectRepository,
    ):
        self.timetable_repo = timetable_repo
        self.section_repo = section_repo
        self.subject_repo = subject_repo

    async def upsert_timetable_entry(self, section_id: str, year_id: str, school_id: str, data: dict):
        teacher_id: Optional[str] = data.get("teacher_id")
        day = data["day_of_week"]
        period = data["period_number"]

        if teacher_id:
            has_conflict = await self.timetable_repo.check_teacher_conflict(teacher_id, year_id, day, period)
            if has_conflict:
                details = await self.timetable_repo.get_teacher_conflict_details(teacher_id, year_id, day, period)
                detail = "Teacher conflict at this slot"
                if details:
                    detail = (
                        f"Teacher is already assigned to {details['subject_name']} in "
                        f"{details['class_name']} - {details['section_name']}"
                    )
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

        room_number = await self.section_repo.get_room_for_section(section_id)
        if room_number:
            room_conflict = await self.timetable_repo.check_room_conflict(room_number, year_id, day, period)
            if room_conflict:
                details = await self.timetable_repo.get_room_conflict_details(room_number, year_id, day, period)
                detail = f"Room {room_number} is already occupied at this slot"
                if details:
                    detail = f"Room {room_number} conflict with {details['class_name']} - {details['section_name']}"
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

        return await self.timetable_repo.upsert_entry(section_id, year_id, school_id, data)

    async def import_timetable_from_csv(self, section_id: str, year_id: str, school_id: str, file: UploadFile) -> dict:
        raw = await file.read()
        content = raw.decode("utf-8", errors="replace")
        rows = list(csv.DictReader(io.StringIO(content)))

        subjects = await self.subject_repo.list_by_school(school_id, active_only=False)
        subject_by_code = {str(sub.code).strip().lower(): str(sub.id) for sub in subjects if sub.code}

        entries = []
        skipped = 0
        for row in rows:
            subject_code = (row.get("subject_code") or "").strip().lower()
            subject_id = subject_by_code.get(subject_code)
            if not subject_id:
                skipped += 1
                continue
            try:
                entries.append(
                    {
                        "subject_id": subject_id,
                        "teacher_id": None,
                        "day_of_week": int(row.get("day_of_week") or 0),
                        "period_number": int(row.get("period") or 0),
                        "start_time": _parse_time(row.get("start_time") or ""),
                        "end_time": _parse_time(row.get("end_time") or ""),
                    }
                )
            except Exception:
                skipped += 1

        if not entries:
            return {"imported": 0, "skipped": skipped}

        imported = await self.timetable_repo.bulk_upsert(section_id, year_id, school_id, entries)
        return {"imported": imported, "skipped": skipped}

    async def get_timetable_pdf(self, section_id: str, year_id: str) -> bytes:
        grid = await self.timetable_repo.get_grid_for_section(section_id, year_id)

        stream = io.BytesIO()
        pdf = canvas.Canvas(stream, pagesize=A4)
        width, height = A4

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(2 * cm, height - 2 * cm, f"Timetable: {grid['class_name']} - {grid['section_name']}")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(2 * cm, height - 2.7 * cm, f"Academic Year: {grid['academic_year_id']}")

        y = height - 4 * cm
        for day in range(1, 8):
            day_name = grid["days"][day - 1]
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(2 * cm, y, day_name)
            y -= 0.5 * cm
            day_entries = grid["grid"].get(day, {})
            if not day_entries:
                pdf.setFont("Helvetica", 9)
                pdf.drawString(2.5 * cm, y, "No periods")
                y -= 0.5 * cm
            else:
                for period in sorted(day_entries.keys()):
                    slot = day_entries[period]
                    label = (
                        f"P{period}: {slot['subject_name']} "
                        f"({slot['start_time']} - {slot['end_time']})"
                    )
                    pdf.setFont("Helvetica", 9)
                    pdf.drawString(2.5 * cm, y, label)
                    y -= 0.45 * cm
            y -= 0.15 * cm
            if y < 2 * cm:
                pdf.showPage()
                y = height - 2 * cm

        pdf.save()
        stream.seek(0)
        return stream.getvalue()

