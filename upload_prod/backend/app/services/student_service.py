from datetime import datetime
from typing import List, Optional
from uuid import UUID
import csv
import io

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.repositories.student_repository import StudentRepository
from app.schemas.phase5 import (
    BulkImportResult,
    IssueTCRequest,
    PromoteStudentsRequest,
    StudentCreate,
    StudentDocumentCreate,
    StudentEnrollmentCreate,
    StudentParentCreate,
    StudentUpdate,
)
from app.utils.admission_number import generate_admission_number
from app.core.security import hash_password


class StudentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = StudentRepository(session)

    async def create_student(
        self, school_id: UUID, student_data: StudentCreate, current_user: User
    ):
        """Create a new student with auto-generated admission number if not provided."""
        # Generate admission number if not provided
        if not student_data.admission_number:
            admission_number = await generate_admission_number(self.session, school_id)
        else:
            # Validate uniqueness
            existing = await self.repository.get_by_admission_number(
                student_data.admission_number, school_id
            )
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Admission number {student_data.admission_number} already exists",
                )
            admission_number = student_data.admission_number

        # Create student
        student = await self.repository.create(school_id, student_data, admission_number)

        # Auto-create student user account (username = admission number, password = DOB as DDMMYYYY)
        student_user_id = await self._create_student_login(school_id, student, admission_number, student_data.date_of_birth)
        if student_user_id:
            student.user_id = student_user_id
            await self.session.flush()

        # Create enrollment if provided
        if student_data.enrollment:
            await self.repository.add_enrollment(
                student.id, school_id, student_data.enrollment
            )

        # Create parents if provided
        for parent_data in student_data.parents:
            # Auto-create parent login whenever phone or email is available
            user_id = None
            if parent_data.phone or parent_data.email:
                user_id = await self._create_parent_login(school_id, parent_data, student.id)

            await self.repository.add_parent(student.id, school_id, parent_data, user_id)

        await self.session.commit()
        return await self.repository.get_detail(student.id, school_id)

    async def _create_student_login(
        self, school_id: UUID, student: any, admission_number: str, date_of_birth
    ) -> Optional[UUID]:
        """Auto-create a user account for a student (username = admission_number, password = DOB as DDMMYYYY)."""
        from sqlalchemy import select
        from app.models.auth import User
        from app.models.rbac import Role, UserRole as UserRoleModel
        from datetime import datetime, timezone

        # Skip if user already exists with this admission number as username
        result = await self.session.execute(
            select(User).where(User.username == admission_number, User.school_id == str(school_id))
        )
        if result.scalar_one_or_none():
            return None

        # Default password = DOB formatted as DDMMYYYY
        dob = date_of_birth
        default_password = dob.strftime("%d%m%Y") if hasattr(dob, "strftime") else str(dob).replace("-", "")

        user = User(
            school_id=school_id,
            username=admission_number,
            password_hash=hash_password(default_password),
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()

        # Assign "student" role if it exists
        role_result = await self.session.execute(
            select(Role).where(Role.school_id == str(school_id), Role.slug == "student")
        )
        student_role = role_result.scalar_one_or_none()
        if student_role:
            self.session.add(UserRoleModel(
                user_id=user.id,
                role_id=student_role.id,
                assigned_at=datetime.now(timezone.utc),
            ))
            await self.session.flush()

        return user.id

    async def _create_parent_login(
        self, school_id: UUID, parent_data: StudentParentCreate, student_id: UUID
    ) -> Optional[UUID]:
        """Create user account for parent portal access (auto-created when phone or email is present)."""
        from sqlalchemy import select
        from app.models.auth import User
        from app.models.rbac import Role, UserRole as UserRoleModel
        from datetime import datetime, timezone

        # Check for existing user by phone first, then email
        existing_user = None
        if parent_data.phone:
            r = await self.session.execute(
                select(User).where(User.phone == parent_data.phone, User.school_id == str(school_id))
            )
            existing_user = r.scalar_one_or_none()
        if not existing_user and parent_data.email:
            r = await self.session.execute(
                select(User).where(User.email == parent_data.email, User.school_id == str(school_id))
            )
            existing_user = r.scalar_one_or_none()
        if existing_user:
            return existing_user.id

        # Default credentials: username = phone (or email prefix), password = "Parent@123"
        default_password = "Parent@123"
        if parent_data.phone:
            import re
            digits = re.sub(r"\D", "", parent_data.phone)
            username = digits[-10:] if len(digits) >= 10 else digits
        elif parent_data.email:
            username = parent_data.email.split("@")[0]
        else:
            return None

        # Ensure username uniqueness within school
        r = await self.session.execute(
            select(User).where(User.username == username, User.school_id == str(school_id))
        )
        if r.scalar_one_or_none():
            suffix = str(student_id)[:8]
            username = f"{username}_{suffix}"

        user = User(
            school_id=school_id,
            username=username,
            phone=parent_data.phone or None,
            email=parent_data.email or None,
            password_hash=hash_password(default_password),
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()

        # Assign "parent" role
        role_result = await self.session.execute(
            select(Role).where(Role.school_id == str(school_id), Role.slug == "parent")
        )
        parent_role = role_result.scalar_one_or_none()
        if parent_role:
            self.session.add(UserRoleModel(
                user_id=user.id,
                role_id=parent_role.id,
                assigned_at=datetime.now(timezone.utc),
            ))
            await self.session.flush()

        return user.id

    async def update_student(
        self, student_id: UUID, school_id: UUID, student_data: StudentUpdate
    ):
        """Update student details."""
        student = await self.repository.update(student_id, school_id, student_data)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        await self.session.commit()
        return await self.repository.get_detail(student_id, school_id)

    async def delete_student(self, student_id: UUID, school_id: UUID, current_user: User):
        """Soft delete student."""
        success = await self.repository.soft_delete(student_id, school_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Student not found")

        await self.session.commit()
        return {"message": "Student deleted successfully"}

    async def promote_students(
        self, school_id: UUID, request: PromoteStudentsRequest, current_user: User
    ):
        """Bulk promote students to next academic year and class."""
        promotions = []

        for student_id in request.student_ids:
            # Get current enrollment
            current_enrollment = await self.repository.get_current_enrollment(
                student_id, school_id
            )
            if not current_enrollment:
                continue

            # Mark current enrollment as inactive
            await self.repository.mark_enrollment_inactive(
                current_enrollment.id, school_id
            )

            # Create new enrollment
            new_enrollment_data = StudentEnrollmentCreate(
                academic_year_id=request.to_academic_year_id,
                class_id=request.to_class_id,
                section_id=request.to_section_id,
                roll_number=None,  # Will be assigned later
                is_current=True,
            )
            await self.repository.add_enrollment(
                student_id, school_id, new_enrollment_data
            )

            # Record promotion
            promotion = await self.repository.promote_student(
                student_id=student_id,
                school_id=school_id,
                from_class_id=current_enrollment.class_id,
                to_class_id=request.to_class_id,
                from_year_id=request.from_academic_year_id,
                to_year_id=request.to_academic_year_id,
                promoted_by=current_user.id,
            )
            promotions.append(promotion)

        await self.session.commit()
        return promotions

    async def issue_transfer_certificate(
        self,
        student_id: UUID,
        school_id: UUID,
        tc_request: IssueTCRequest,
        current_user: User,
    ):
        """Issue transfer certificate and mark student as inactive."""
        student = await self.repository.get_by_id(student_id, school_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Mark student as inactive
        await self.repository.update(
            student_id, school_id, StudentUpdate(is_active=False)
        )

        # Issue TC
        transfer = await self.repository.issue_transfer_certificate(
            student_id=student_id,
            school_id=school_id,
            tc_number=tc_request.transfer_certificate_no,
            leaving_date=tc_request.leaving_date,
            reason=tc_request.reason,
            issued_by=current_user.id,
        )

        await self.session.commit()
        return transfer

    async def bulk_import_students(
        self, school_id: UUID, file: UploadFile, current_user: User
    ) -> BulkImportResult:
        """Bulk import students from CSV file."""
        content = await file.read()
        csv_file = io.StringIO(content.decode("utf-8"))
        reader = csv.DictReader(csv_file)

        success_count = 0
        error_count = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):  # Start from 2 (header is row 1)
            try:
                # Parse student data
                student_data = StudentCreate(
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    date_of_birth=datetime.strptime(row["date_of_birth"], "%Y-%m-%d").date(),
                    gender=row["gender"],
                    blood_group=row.get("blood_group"),
                    religion=row.get("religion"),
                    category=row.get("category"),
                    nationality=row.get("nationality", "Indian"),
                    admission_date=datetime.strptime(row["admission_date"], "%Y-%m-%d").date(),
                )

                # Create student
                await self.create_student(school_id, student_data, current_user)
                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append({"row": row_num, "error": str(e)})

        await self.session.commit()

        return BulkImportResult(
            success_count=success_count,
            error_count=error_count,
            errors=errors,
        )

    async def export_students_csv(self, school_id: UUID) -> str:
        """Export students to CSV format."""
        students, _ = await self.repository.list(school_id, skip=0, limit=100000)

        output = io.StringIO()
        fieldnames = [
            "admission_number",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "blood_group",
            "religion",
            "category",
            "nationality",
            "admission_date",
            "is_active",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for student in students:
            writer.writerow(
                {
                    "admission_number": student.admission_number,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "date_of_birth": student.date_of_birth.isoformat(),
                    "gender": student.gender,
                    "blood_group": student.blood_group or "",
                    "religion": student.religion or "",
                    "category": student.category or "",
                    "nationality": student.nationality,
                    "admission_date": student.admission_date.isoformat(),
                    "is_active": student.is_active,
                }
            )

        return output.getvalue()

