from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.students import (
    Student,
    StudentDocument,
    StudentEnrollment,
    StudentParent,
    StudentPromotion,
    StudentTransfer,
)
from app.schemas.phase5 import (
    StudentCreate,
    StudentDocumentCreate,
    StudentEnrollmentCreate,
    StudentParentCreate,
    StudentUpdate,
)


class StudentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        school_id: UUID,
        student_data: StudentCreate,
        admission_number: str,
    ) -> Student:
        """Create a new student."""
        student = Student(
            school_id=school_id,
            admission_number=admission_number,
            first_name=student_data.first_name,
            last_name=student_data.last_name,
            date_of_birth=student_data.date_of_birth,
            gender=student_data.gender,
            blood_group=student_data.blood_group,
            religion=student_data.religion,
            category=student_data.category,
            nationality=student_data.nationality,
            photo_url=student_data.photo_url,
            admission_date=student_data.admission_date,
            is_active=student_data.is_active,
            aadhaar_number=student_data.aadhaar_number,
            pan_number=student_data.pan_number,
            apaar_number=student_data.apaar_number,
        )
        self.session.add(student)
        await self.session.flush()
        return student

    async def get_by_id(self, student_id: UUID, school_id: UUID) -> Optional[Student]:
        """Get student by ID."""
        result = await self.session.execute(
            select(Student)
            .where(Student.id == student_id)
            .where(Student.school_id == school_id)
            .where(Student.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_detail(self, student_id: UUID, school_id: UUID) -> Optional[Student]:
        """Get student with all relationships."""
        result = await self.session.execute(
            select(Student)
            .options(
                selectinload(Student.parents),
                selectinload(Student.enrollments),
                selectinload(Student.documents),
            )
            .where(Student.id == student_id)
            .where(Student.school_id == school_id)
            .where(Student.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_admission_number(
        self, admission_number: str, school_id: UUID
    ) -> Optional[Student]:
        """Get student by admission number."""
        result = await self.session.execute(
            select(Student)
            .where(Student.admission_number == admission_number)
            .where(Student.school_id == school_id)
            .where(Student.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        school_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        class_id: Optional[UUID] = None,
        section_id: Optional[UUID] = None,
        academic_year_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[Student], int]:
        """List students with filters."""
        # Base query
        query = (
            select(Student)
            .where(Student.school_id == school_id)
            .where(Student.deleted_at.is_(None))
        )

        # Apply filters
        if search:
            search_filter = or_(
                Student.first_name.ilike(f"%{search}%"),
                Student.last_name.ilike(f"%{search}%"),
                Student.admission_number.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        if is_active is not None:
            query = query.where(Student.is_active == is_active)

        # Join with enrollment for class/section/year filters
        if class_id or section_id or academic_year_id:
            query = query.join(StudentEnrollment, Student.id == StudentEnrollment.student_id)
            if class_id:
                query = query.where(StudentEnrollment.class_id == class_id)
            if section_id:
                query = query.where(StudentEnrollment.section_id == section_id)
            if academic_year_id:
                query = query.where(StudentEnrollment.academic_year_id == academic_year_id)
            query = query.where(StudentEnrollment.is_current == True)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and order
        query = query.order_by(Student.admission_number.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        students = list(result.scalars().all())

        return students, total

    async def update(
        self, student_id: UUID, school_id: UUID, student_data: StudentUpdate
    ) -> Optional[Student]:
        """Update student."""
        student = await self.get_by_id(student_id, school_id)
        if not student:
            return None

        update_dict = student_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(student, field, value)

        await self.session.flush()
        return student

    async def soft_delete(self, student_id: UUID, school_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete student."""
        result = await self.session.execute(
            update(Student)
            .where(Student.id == student_id)
            .where(Student.school_id == school_id)
            .where(Student.deleted_at.is_(None))
            .values(deleted_at=datetime.utcnow(), deleted_by=deleted_by)
        )
        return result.rowcount > 0

    # ========== Parent Management ==========
    async def add_parent(
        self,
        student_id: UUID,
        school_id: UUID,
        parent_data: StudentParentCreate,
        user_id: Optional[UUID] = None,
    ) -> StudentParent:
        """Add parent to student."""
        parent = StudentParent(
            school_id=school_id,
            student_id=student_id,
            user_id=user_id,
            relation=parent_data.relation,
            name=parent_data.name,
            phone=parent_data.phone,
            email=parent_data.email,
            occupation=parent_data.occupation,
            address=parent_data.address,
            is_primary_contact=parent_data.is_primary_contact,
            can_access_portal=parent_data.can_access_portal,
            aadhaar_number=parent_data.aadhaar_number,
            pan_number=parent_data.pan_number,
            ration_card_number=parent_data.ration_card_number,
        )
        self.session.add(parent)
        await self.session.flush()
        return parent

    async def get_parents(self, student_id: UUID, school_id: UUID) -> List[StudentParent]:
        """Get all parents of a student."""
        result = await self.session.execute(
            select(StudentParent)
            .where(StudentParent.student_id == student_id)
            .where(StudentParent.school_id == school_id)
        )
        return list(result.scalars().all())

    async def delete_parent(self, parent_id: UUID, school_id: UUID) -> bool:
        """Delete a parent."""
        result = await self.session.execute(
            select(StudentParent)
            .where(StudentParent.id == parent_id)
            .where(StudentParent.school_id == school_id)
        )
        parent = result.scalar_one_or_none()
        if parent:
            await self.session.delete(parent)
            await self.session.flush()
            return True
        return False

    # ========== Enrollment Management ==========
    async def add_enrollment(
        self,
        student_id: UUID,
        school_id: UUID,
        enrollment_data: StudentEnrollmentCreate,
    ) -> StudentEnrollment:
        """Add enrollment for student."""
        enrollment = StudentEnrollment(
            school_id=school_id,
            student_id=student_id,
            academic_year_id=enrollment_data.academic_year_id,
            class_id=enrollment_data.class_id,
            section_id=enrollment_data.section_id,
            roll_number=enrollment_data.roll_number,
            is_current=enrollment_data.is_current,
        )
        self.session.add(enrollment)
        await self.session.flush()
        return enrollment

    async def get_current_enrollment(
        self, student_id: UUID, school_id: UUID
    ) -> Optional[StudentEnrollment]:
        """Get current enrollment of student."""
        result = await self.session.execute(
            select(StudentEnrollment)
            .where(StudentEnrollment.student_id == student_id)
            .where(StudentEnrollment.school_id == school_id)
            .where(StudentEnrollment.is_current == True)
        )
        return result.scalar_one_or_none()

    async def mark_enrollment_inactive(self, enrollment_id: UUID, school_id: UUID) -> bool:
        """Mark enrollment as inactive."""
        result = await self.session.execute(
            update(StudentEnrollment)
            .where(StudentEnrollment.id == enrollment_id)
            .where(StudentEnrollment.school_id == school_id)
            .values(is_current=False)
        )
        return result.rowcount > 0

    # ========== Document Management ==========
    async def add_document(
        self,
        student_id: UUID,
        school_id: UUID,
        document_data: StudentDocumentCreate,
    ) -> StudentDocument:
        """Add document for student."""
        document = StudentDocument(
            school_id=school_id,
            student_id=student_id,
            doc_type=document_data.doc_type,
            file_url=document_data.file_url,
        )
        self.session.add(document)
        await self.session.flush()
        return document

    async def get_documents(self, student_id: UUID, school_id: UUID) -> List[StudentDocument]:
        """Get all documents of a student."""
        result = await self.session.execute(
            select(StudentDocument)
            .where(StudentDocument.student_id == student_id)
            .where(StudentDocument.school_id == school_id)
        )
        return list(result.scalars().all())

    async def delete_document(self, document_id: UUID, school_id: UUID) -> bool:
        """Delete a document."""
        result = await self.session.execute(
            select(StudentDocument)
            .where(StudentDocument.id == document_id)
            .where(StudentDocument.school_id == school_id)
        )
        document = result.scalar_one_or_none()
        if document:
            await self.session.delete(document)
            await self.session.flush()
            return True
        return False

    # ========== Promotion ==========
    async def promote_student(
        self,
        student_id: UUID,
        school_id: UUID,
        from_class_id: UUID,
        to_class_id: UUID,
        from_year_id: UUID,
        to_year_id: UUID,
        promoted_by: UUID,
    ) -> StudentPromotion:
        """Record student promotion."""
        promotion = StudentPromotion(
            school_id=school_id,
            student_id=student_id,
            from_class_id=from_class_id,
            to_class_id=to_class_id,
            from_year_id=from_year_id,
            to_year_id=to_year_id,
            promoted_by=promoted_by,
        )
        self.session.add(promotion)
        await self.session.flush()
        return promotion

    # ========== Transfer Certificate ==========
    async def issue_transfer_certificate(
        self,
        student_id: UUID,
        school_id: UUID,
        tc_number: str,
        leaving_date: date,
        reason: Optional[str],
        issued_by: UUID,
    ) -> StudentTransfer:
        """Issue transfer certificate."""
        transfer = StudentTransfer(
            school_id=school_id,
            student_id=student_id,
            transfer_certificate_no=tc_number,
            leaving_date=leaving_date,
            reason=reason,
            issued_by=issued_by,
        )
        self.session.add(transfer)
        await self.session.flush()
        return transfer

    async def get_transfer_certificate(
        self, student_id: UUID, school_id: UUID
    ) -> Optional[StudentTransfer]:
        """Get transfer certificate for student."""
        result = await self.session.execute(
            select(StudentTransfer)
            .where(StudentTransfer.student_id == student_id)
            .where(StudentTransfer.school_id == school_id)
        )
        return result.scalar_one_or_none()

    # ========== Statistics ==========
    async def get_stats(self, school_id: UUID) -> dict:
        """Get student statistics."""
        # Total students
        total_result = await self.session.execute(
            select(func.count(Student.id))
            .where(Student.school_id == school_id)
            .where(Student.deleted_at.is_(None))
        )
        total = total_result.scalar_one()

        # Active students
        active_result = await self.session.execute(
            select(func.count(Student.id))
            .where(Student.school_id == school_id)
            .where(Student.is_active == True)
            .where(Student.deleted_at.is_(None))
        )
        active = active_result.scalar_one()

        # Gender breakdown
        male_result = await self.session.execute(
            select(func.count(Student.id))
            .where(Student.school_id == school_id)
            .where(Student.gender.in_(["Male", "male", "M"]))
            .where(Student.deleted_at.is_(None))
        )
        male = male_result.scalar_one()

        female_result = await self.session.execute(
            select(func.count(Student.id))
            .where(Student.school_id == school_id)
            .where(Student.gender.in_(["Female", "female", "F"]))
            .where(Student.deleted_at.is_(None))
        )
        female = female_result.scalar_one()

        return {
            "total_students": total,
            "active_students": active,
            "inactive_students": total - active,
            "male_students": male,
            "female_students": female,
        }

