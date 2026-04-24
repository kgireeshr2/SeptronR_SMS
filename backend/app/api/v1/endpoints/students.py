from typing import List, Optional
from uuid import UUID
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_school_id
from app.db.session import get_db
from app.models.auth import User
from app.repositories.student_repository import StudentRepository
from app.schemas.phase5 import (
    BulkImportResult,
    IssueTCRequest,
    PromoteStudentsRequest,
    StudentCreate,
    StudentDetailResponse,
    StudentDocumentCreate,
    StudentDocumentResponse,
    StudentEnrollmentCreate,
    StudentEnrollmentResponse,
    StudentParentCreate,
    StudentParentResponse,
    StudentPromotionResponse,
    StudentResponse,
    StudentStats,
    StudentTransferResponse,
    StudentUpdate,
)
from app.services.student_service import StudentService
from io import BytesIO

router = APIRouter()


@router.post("/", response_model=StudentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student: StudentCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new student with optional enrollment and parents."""
    service = StudentService(db)
    return await service.create_student(school_id, student, current_user)


@router.get("/", response_model=List[StudentResponse])
async def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    class_id: Optional[UUID] = Query(None),
    section_id: Optional[UUID] = Query(None),
    academic_year_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all students with optional filters."""
    repository = StudentRepository(db)
    students, total = await repository.list(
        school_id=school_id,
        skip=skip,
        limit=limit,
        search=search,
        class_id=class_id,
        section_id=section_id,
        academic_year_id=academic_year_id,
        is_active=is_active,
    )
    return students


@router.get("/stats", response_model=StudentStats)
async def get_student_stats(
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get student statistics."""
    repository = StudentRepository(db)
    stats = await repository.get_stats(school_id)
    return StudentStats(**stats, students_by_class=[])


@router.get("/{student_id}", response_model=StudentDetailResponse)
async def get_student(
    student_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get student details with all relationships."""
    repository = StudentRepository(db)
    student = await repository.get_detail(student_id, school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=StudentDetailResponse)
async def update_student(
    student_id: UUID,
    student_update: StudentUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update student details."""
    service = StudentService(db)
    return await service.update_student(student_id, school_id, student_update)


@router.delete("/{student_id}", status_code=status.HTTP_200_OK)
async def delete_student(
    student_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete student."""
    service = StudentService(db)
    return await service.delete_student(student_id, school_id, current_user)


# ========== Parent Management ==========
@router.post("/{student_id}/parents", response_model=StudentParentResponse)
async def add_parent(
    student_id: UUID,
    parent: StudentParentCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a parent to a student."""
    repository = StudentRepository(db)
    
    # Verify student exists
    student = await repository.get_by_id(student_id, school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    service = StudentService(db)
    
    # Auto-create parent login when phone or email is available
    user_id = None
    if parent.phone or parent.email:
        user_id = await service._create_parent_login(school_id, parent, student_id)
    
    parent_record = await repository.add_parent(student_id, school_id, parent, user_id)
    await db.commit()
    return parent_record


@router.get("/{student_id}/parents", response_model=List[StudentParentResponse])
async def get_parents(
    student_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all parents of a student."""
    repository = StudentRepository(db)
    return await repository.get_parents(student_id, school_id)


@router.delete("/parents/{parent_id}", status_code=status.HTTP_200_OK)
async def delete_parent(
    parent_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a parent."""
    repository = StudentRepository(db)
    success = await repository.delete_parent(parent_id, school_id)
    if not success:
        raise HTTPException(status_code=404, detail="Parent not found")
    await db.commit()
    return {"message": "Parent deleted successfully"}


# ========== Enrollment Management ==========
@router.post("/{student_id}/enrollments", response_model=StudentEnrollmentResponse)
async def add_enrollment(
    student_id: UUID,
    enrollment: StudentEnrollmentCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an enrollment for a student."""
    repository = StudentRepository(db)
    
    # Verify student exists
    student = await repository.get_by_id(student_id, school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    enrollment_record = await repository.add_enrollment(student_id, school_id, enrollment)
    await db.commit()
    return enrollment_record


# ========== Document Management ==========
@router.post("/{student_id}/documents", response_model=StudentDocumentResponse)
async def add_document(
    student_id: UUID,
    document: StudentDocumentCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a document for a student."""
    repository = StudentRepository(db)
    
    # Verify student exists
    student = await repository.get_by_id(student_id, school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    document_record = await repository.add_document(student_id, school_id, document)
    await db.commit()
    return document_record


@router.get("/{student_id}/documents", response_model=List[StudentDocumentResponse])
async def get_documents(
    student_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all documents of a student."""
    repository = StudentRepository(db)
    return await repository.get_documents(student_id, school_id)


@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document."""
    repository = StudentRepository(db)
    success = await repository.delete_document(document_id, school_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.commit()
    return {"message": "Document deleted successfully"}


# ========== Photo Upload ==========
@router.post("/{student_id}/photo")
async def upload_photo(
    student_id: UUID,
    file: UploadFile = File(...),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload student photo."""
    # TODO: Implement file storage (S3, local, etc.)
    # For now, just return a placeholder URL
    repository = StudentRepository(db)
    
    student = await repository.get_by_id(student_id, school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Placeholder: save file and get URL
    photo_url = f"/uploads/students/{student_id}/{file.filename}"
    
    from app.schemas.phase5 import StudentUpdate
    await repository.update(student_id, school_id, StudentUpdate(photo_url=photo_url))
    await db.commit()
    
    return {"photo_url": photo_url}


# ========== Bulk Operations ==========
@router.post("/promote", response_model=List[StudentPromotionResponse])
async def promote_students(
    request: PromoteStudentsRequest,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk promote students to next academic year and class."""
    service = StudentService(db)
    return await service.promote_students(school_id, request, current_user)


@router.post("/import", response_model=BulkImportResult)
async def bulk_import_students(
    file: UploadFile = File(...),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk import students from CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    service = StudentService(db)
    return await service.bulk_import_students(school_id, file, current_user)


@router.get("/export/csv")
async def export_students_csv(
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export all students to CSV file."""
    service = StudentService(db)
    csv_content = await service.export_students_csv(school_id)
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"},
    )


# ========== Transfer Certificate ==========
@router.post("/{student_id}/transfer-certificate", response_model=StudentTransferResponse)
async def issue_transfer_certificate(
    student_id: UUID,
    tc_request: IssueTCRequest,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Issue transfer certificate for a student."""
    service = StudentService(db)
    return await service.issue_transfer_certificate(
        student_id, school_id, tc_request, current_user
    )


@router.get("/{student_id}/transfer-certificate", response_model=StudentTransferResponse)
async def get_transfer_certificate(
    student_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get transfer certificate for a student."""
    repository = StudentRepository(db)
    tc = await repository.get_transfer_certificate(student_id, school_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Transfer certificate not found")
    return tc


@router.get("/{student_id}/transfer-certificate/pdf")
async def download_transfer_certificate_pdf(
    student_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download Transfer Certificate as PDF."""
    from app.services.pdf_service import generate_transfer_certificate_pdf
    from app.repositories.school_repository import SchoolRepository
    from sqlalchemy import text

    repository = StudentRepository(db)
    tc = await repository.get_transfer_certificate(student_id, school_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Transfer certificate not found")

    student = await repository.get_detail(student_id, school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(str(school_id))
    school_name = school.name if school else "School"

    # Last enrollment for class info
    class_last = "—"
    academic_year_name = "—"
    if hasattr(student, "enrollments") and student.enrollments:
        latest = sorted(student.enrollments, key=lambda e: str(e.academic_year_id))[-1]
        class_last = getattr(latest, "class_name", "—") or "—"

    pdf_data = {
        "school_name": school_name,
        "school_address": getattr(school, "address", None),
        "school_phone": getattr(school, "phone", None),
        "tc_number": getattr(tc, "transfer_certificate_no", None) or str(tc.id)[:8].upper(),
        "issue_date": str(tc.leaving_date) if hasattr(tc, "leaving_date") else None,
        "student_name": f"{student.first_name} {student.last_name}",
        "admission_number": student.admission_number,
        "date_of_birth": str(student.date_of_birth) if student.date_of_birth else None,
        "gender": student.gender or "",
        "nationality": getattr(student, "nationality", "—"),
        "religion": getattr(student, "religion", "—"),
        "category": getattr(student, "category", "—"),
        "blood_group": getattr(student, "blood_group", "—"),
        "admission_date": str(student.admission_date) if student.admission_date else None,
        "class_last_studied": class_last,
        "academic_year_name": academic_year_name,
        "leaving_date": str(tc.leaving_date) if hasattr(tc, "leaving_date") else None,
        "reason": getattr(tc, "reason", "—"),
        "conduct": "Good",
        "issued_by_name": getattr(current_user, "username", ""),
    }

    pdf_bytes = generate_transfer_certificate_pdf(pdf_data)
    filename = f"TC_{student.admission_number}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ========== ID Card Generation ==========
@router.get("/{student_id}/id-card")
async def generate_id_card(
    student_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate ID card PDF for a student."""
    from app.services.pdf_service import generate_id_card_pdf
    from app.repositories.school_repository import SchoolRepository

    repository = StudentRepository(db)
    student = await repository.get_detail(student_id, school_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(str(school_id))
    school_name = school.name if school else "School"

    class_name = "—"
    section_name = "—"
    if hasattr(student, "enrollments") and student.enrollments:
        latest = sorted(student.enrollments, key=lambda e: str(e.academic_year_id))[-1]
        class_name = getattr(latest, "class_name", "—") or "—"
        section_name = getattr(latest, "section_name", "—") or "—"

    student_data = [
        {
            "student_name": f"{student.first_name} {student.last_name}",
            "admission_number": student.admission_number,
            "class_name": class_name,
            "section_name": section_name,
            "date_of_birth": str(student.date_of_birth) if student.date_of_birth else None,
            "blood_group": getattr(student, "blood_group", None),
        }
    ]

    school_info = {
        "school_name": school_name,
        "school_address": getattr(school, "address", None),
        "school_phone": getattr(school, "phone", None),
        "school_email": getattr(school, "email", None),
    }

    pdf_bytes = generate_id_card_pdf(student_data, school_info)
    filename = f"id_card_{student.admission_number}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/id-cards/bulk")
async def generate_bulk_id_cards(
    student_ids: List[UUID],
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate ID cards PDF for multiple students at once."""
    from app.services.pdf_service import generate_id_card_pdf
    from app.repositories.school_repository import SchoolRepository

    repository = StudentRepository(db)
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(str(school_id))
    school_name = school.name if school else "School"
    school_info = {
        "school_name": school_name,
        "school_address": getattr(school, "address", None),
        "school_phone": getattr(school, "phone", None),
    }

    students_data = []
    for sid in student_ids:
        student = await repository.get_detail(sid, school_id)
        if not student:
            continue
        class_name = "—"
        section_name = "—"
        if hasattr(student, "enrollments") and student.enrollments:
            latest = sorted(student.enrollments, key=lambda e: str(e.academic_year_id))[-1]
            class_name = getattr(latest, "class_name", "—") or "—"
            section_name = getattr(latest, "section_name", "—") or "—"
        students_data.append(
            {
                "student_name": f"{student.first_name} {student.last_name}",
                "admission_number": student.admission_number,
                "class_name": class_name,
                "section_name": section_name,
                "date_of_birth": str(student.date_of_birth) if student.date_of_birth else None,
                "blood_group": getattr(student, "blood_group", None),
            }
        )

    if not students_data:
        raise HTTPException(status_code=404, detail="No valid students found")

    pdf_bytes = generate_id_card_pdf(students_data, school_info)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="id_cards_bulk.pdf"'},
    )


