from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_serializer,computed_field

from app.models.students import ParentRelation


# ========== Student Parent Schemas ==========
class StudentParentBase(BaseModel):
    relation: ParentRelation
    name: str = Field(..., max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    occupation: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    is_primary_contact: bool = False
    can_access_portal: bool = True
    # Government IDs
    aadhaar_number: Optional[str] = Field(None, max_length=20)
    pan_number: Optional[str] = Field(None, max_length=15)
    ration_card_number: Optional[str] = Field(None, max_length=30)


class StudentParentCreate(StudentParentBase):
    create_login: bool = False


class StudentParentUpdate(BaseModel):
    relation: Optional[ParentRelation] = None
    name: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    occupation: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    is_primary_contact: Optional[bool] = None
    can_access_portal: Optional[bool] = None
    aadhaar_number: Optional[str] = Field(None, max_length=20)
    pan_number: Optional[str] = Field(None, max_length=15)
    ration_card_number: Optional[str] = Field(None, max_length=30)


class StudentParentResponse(StudentParentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


# ========== Student Enrollment Schemas ==========
class StudentEnrollmentBase(BaseModel):
    academic_year_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    roll_number: Optional[str] = Field(None, max_length=20)
    is_current: bool = True


class StudentEnrollmentCreate(StudentEnrollmentBase):
    pass


class StudentEnrollmentUpdate(BaseModel):
    roll_number: Optional[str] = Field(None, max_length=20)
    is_current: Optional[bool] = None


class StudentEnrollmentResponse(StudentEnrollmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    created_at: datetime
    updated_at: datetime


# ========== Student Document Schemas ==========
class StudentDocumentCreate(BaseModel):
    doc_type: str = Field(..., max_length=60)
    file_url: str


class StudentDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    doc_type: str
    file_url: str
    uploaded_at: datetime


# ========== Student Schemas ==========
class StudentBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    date_of_birth: date
    gender: str = Field(..., max_length=10)
    blood_group: Optional[str] = Field(None, max_length=5)
    religion: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=30)
    nationality: str = Field(default="Indian", max_length=60)
    photo_url: Optional[str] = None
    admission_date: date
    is_active: bool = True
    # Government IDs
    aadhaar_number: Optional[str] = Field(None, max_length=20)
    pan_number: Optional[str] = Field(None, max_length=15)
    apaar_number: Optional[str] = Field(None, max_length=30)
    # Contact & Address
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=60)
    pincode: Optional[str] = Field(None, max_length=10)
    # Additional Info
    caste: Optional[str] = Field(None, max_length=100)
    mother_tongue: Optional[str] = Field(None, max_length=60)
    previous_school: Optional[str] = Field(None, max_length=200)
    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)


class StudentCreate(StudentBase):
    admission_number: Optional[str] = Field(None, max_length=30)  # Auto-generated if None
    enrollment: Optional[StudentEnrollmentCreate] = None
    parents: List[StudentParentCreate] = []


class StudentUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=10)
    blood_group: Optional[str] = Field(None, max_length=5)
    religion: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=30)
    nationality: Optional[str] = Field(None, max_length=60)
    photo_url: Optional[str] = None
    admission_date: Optional[date] = None
    admission_number: Optional[str] = Field(None, max_length=30)
    is_active: Optional[bool] = None
    aadhaar_number: Optional[str] = Field(None, max_length=20)
    pan_number: Optional[str] = Field(None, max_length=15)
    apaar_number: Optional[str] = Field(None, max_length=30)
    # Contact & Address
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=60)
    pincode: Optional[str] = Field(None, max_length=10)
    # Additional Info
    caste: Optional[str] = Field(None, max_length=100)
    mother_tongue: Optional[str] = Field(None, max_length=60)
    previous_school: Optional[str] = Field(None, max_length=200)
    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)


class StudentResponse(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    admission_number: str
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @computed_field
    @property
    def age(self) -> int:
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

    @field_serializer("date_of_birth", "admission_date")
    def serialize_date(self, value: date, _info) -> str:
        return value.isoformat()


class StudentDetailResponse(StudentResponse):
    parents: List[StudentParentResponse] = []
    enrollments: List[StudentEnrollmentResponse] = []
    documents: List[StudentDocumentResponse] = []


# ========== Student Promotion Schemas ==========
class PromoteStudentsRequest(BaseModel):
    student_ids: List[UUID]
    from_academic_year_id: UUID
    to_academic_year_id: UUID
    to_class_id: UUID
    to_section_id: UUID


class StudentPromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    from_class_id: UUID
    to_class_id: UUID
    from_year_id: UUID
    to_year_id: UUID
    promoted_by: UUID
    promoted_at: datetime


# ========== Transfer Certificate Schemas ==========
class IssueTCRequest(BaseModel):
    transfer_certificate_no: str = Field(..., max_length=50)
    leaving_date: date
    reason: Optional[str] = None

    @field_serializer("leaving_date")
    def serialize_date(self, value: date, _info) -> str:
        return value.isoformat()


class StudentTransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    transfer_certificate_no: str
    leaving_date: date
    reason: Optional[str] = None
    issued_by: Optional[UUID] = None
    issued_at: datetime

    @field_serializer("leaving_date")
    def serialize_date(self, value: date, _info) -> str:
        return value.isoformat()


# ========== Bulk Import Schemas ==========
class BulkImportResult(BaseModel):
    success_count: int
    error_count: int
    errors: List[dict] = []  # List of {row: int, errors: List[str]}


# ========== Student Stats Schemas ==========
class StudentStats(BaseModel):
    total_students: int
    active_students: int
    inactive_students: int
    male_students: int
    female_students: int
    students_by_class: List[dict] = []  # List of {class_name: str, count: int}
