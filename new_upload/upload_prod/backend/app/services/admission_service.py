from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from app.models.admissions import AdmissionStatus
from app.repositories.admission_repository import AdmissionRepository
from app.repositories.school_repository import SchoolRepository
from app.utils.file_upload import ALLOWED_DOCUMENT_TYPES, save_upload_file


class AdmissionService:
    def __init__(self, admission_repo: AdmissionRepository, school_repo: SchoolRepository):
        self.admission_repo = admission_repo
        self.school_repo = school_repo

    async def submit_application(self, data: dict, files: list[UploadFile] | None = None):
        school_slug = data["school_slug"]
        school = await self.school_repo.get_by_slug(school_slug)
        if not school:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")

        config = await self.admission_repo.get_config(str(school.id), str(data["academic_year_id"]))
        if not config or not config.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admissions are currently closed")

        today = datetime.now(timezone.utc).date()
        if config.open_date and today < config.open_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admissions have not opened yet")
        if config.close_date and today > config.close_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admissions are closed")

        timestamp_part = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        reference = f"{school.slug.upper()}-{today.year}-{timestamp_part}"

        documents = []
        for file in (files or []):
            path = await save_upload_file(file, folder=f"{school.id}/admissions", allowed_types=ALLOWED_DOCUMENT_TYPES)
            documents.append({"doc_type": file.filename, "file_url": path})

        payload = {
            "school_id": str(school.id),
            "academic_year_id": str(data["academic_year_id"]),
            "reference_number": reference,
            "applicant_name": data["applicant_name"],
            "date_of_birth": data["date_of_birth"],
            "gender": data.get("gender"),
            "applying_for_class_id": data.get("applying_for_class_id"),
            "parent_name": data.get("parent_name"),
            "parent_phone": data.get("parent_phone"),
            "parent_email": data.get("parent_email"),
            "address": data.get("address"),
            "previous_school": data.get("previous_school"),
            "documents": documents,
            "extra_metadata": data.get("metadata"),
            "status": AdmissionStatus.submitted,
            "submitted_at": datetime.now(timezone.utc),
        }

        form = await self.admission_repo.create_form(payload)

        if form.parent_email:
            try:
                from app.tasks.emails import send_admission_acknowledgement
                send_admission_acknowledgement.delay(
                    form.parent_email,
                    form.reference_number,
                    school.name,
                    form.applicant_name,
                )
            except Exception:
                pass

        # SMS/WhatsApp acknowledgement to the (not-yet-onboarded) applicant's parent.
        if form.parent_phone:
            from app.services.notifications.notify import notify_event
            notify_event(
                str(school.id), "admission_submitted", audience="direct",
                direct_contacts=[{"phone": form.parent_phone, "name": form.parent_name or "Parent"}],
                default_channels=["sms", "whatsapp"],
                title="Application Received",
                body=(f"Dear {form.parent_name or 'Parent'}, we received the admission application "
                      f"for {form.applicant_name}. Reference: {form.reference_number}."),
            )

        return form

    async def review_application(self, form_id: str, reviewer_id: str, data: dict):
        form = await self.admission_repo.get_form_by_id(form_id)
        if not form:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission form not found")

        status_value = data["status"]
        if status_value == "approved" and not data.get("assigned_admission_number"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="assigned_admission_number is required for approval",
            )

        update_payload = {
            "status": status_value,
            "remarks": data.get("remarks"),
            "assigned_admission_number": data.get("assigned_admission_number"),
            "reviewed_by": reviewer_id,
            "reviewed_at": datetime.now(timezone.utc),
        }
        updated = await self.admission_repo.update_status(form_id, update_payload)

        if updated and updated.parent_email:
            try:
                from app.tasks.emails import send_admission_approved, send_admission_rejected
                if status_value == "approved":
                    send_admission_approved.delay(
                        updated.parent_email,
                        updated.applicant_name,
                        updated.assigned_admission_number or "",
                        "School",
                    )
                elif status_value == "rejected":
                    send_admission_rejected.delay(
                        updated.parent_email,
                        updated.applicant_name,
                        updated.remarks or "",
                        "School",
                    )
            except Exception:
                pass

        if updated and updated.parent_phone and status_value in ("approved", "rejected"):
            from app.services.notifications.notify import notify_event
            if status_value == "approved":
                _body = (f"Congratulations! Admission for {updated.applicant_name} is APPROVED. "
                         f"Admission No: {updated.assigned_admission_number or ''}.")
            else:
                _body = (f"Update: the admission application for {updated.applicant_name} was not "
                         f"approved. {('Remarks: ' + updated.remarks) if updated.remarks else ''}")
            notify_event(
                str(updated.school_id), f"admission_{status_value}", audience="direct",
                direct_contacts=[{"phone": updated.parent_phone, "name": updated.applicant_name}],
                default_channels=["sms", "whatsapp"],
                title="Admission Update", body=_body,
            )

        return updated

    async def bulk_approve(self, form_ids: list[UUID], reviewer_id: str, class_section_map: dict | None = None) -> int:
        approved_count = 0
        for form_id in form_ids:
            form = await self.admission_repo.get_form_by_id(str(form_id))
            if not form:
                continue
            if str(form.status) == AdmissionStatus.approved.value:
                continue
            admission_number = form.assigned_admission_number or f"STU-{datetime.now(timezone.utc).strftime('%Y')}-{approved_count + 1001}"
            await self.admission_repo.update_status(
                str(form_id),
                {
                    "status": AdmissionStatus.approved,
                    "assigned_admission_number": admission_number,
                    "reviewed_by": reviewer_id,
                    "reviewed_at": datetime.now(timezone.utc),
                },
            )
            approved_count += 1
        return approved_count

