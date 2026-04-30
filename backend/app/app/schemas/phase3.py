from datetime import date, datetime
from typing import Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SchoolProfileUpdate(BaseModel):
    school_name: Optional[str] = None
    tagline: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    established_year: Optional[int] = None
    affiliation_board: Optional[str] = None
    affiliation_number: Optional[str] = None
    principal_name: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None
    academic_start_month: Optional[int] = Field(default=None, ge=1, le=12)


class SchoolBootstrapCreate(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    pincode: Optional[str] = None
    # Optional: auto-create a school admin account
    admin_first_name: Optional[str] = Field(None, max_length=100)
    admin_last_name: Optional[str] = Field(None, max_length=100)
    admin_email: Optional[EmailStr] = None
    admin_password: Optional[str] = Field(None, min_length=8)
    admin_phone: Optional[str] = None


class SchoolProfileResponse(SchoolProfileUpdate):
    id: UUID
    school_id: UUID
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    principal_signature_url: Optional[str] = None
    school_seal_url: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingUpdate(BaseModel):
    value: str


class BulkSettingsUpdate(BaseModel):
    settings: Dict[str, str]


class SettingResponse(BaseModel):
    key: str
    value: str
    category: str
    data_type: str
    is_public: bool

    model_config = ConfigDict(from_attributes=True)


class AcademicTermCreate(BaseModel):
    name: str
    start_date: date
    end_date: date


class AcademicTermUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AcademicTermResponse(BaseModel):
    id: UUID
    academic_year_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool

    model_config = ConfigDict(from_attributes=True)


class AcademicYearCreate(BaseModel):
    name: str
    start_date: date
    end_date: date


class AcademicYearUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AcademicYearResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool
    is_locked: bool
    created_at: datetime
    terms: Optional[List[AcademicTermResponse]] = None

    model_config = ConfigDict(from_attributes=True)


class AdmissionFormConfigCreate(BaseModel):
    academic_year_id: UUID
    fields_config: List[Dict] = []
    required_documents: List[Dict] = []
    open_date: Optional[date] = None
    close_date: Optional[date] = None
    is_active: bool = False


class AdmissionApplicationCreate(BaseModel):
    school_slug: str
    academic_year_id: UUID
    applicant_name: str
    date_of_birth: date
    gender: Optional[str] = None
    applying_for_class_id: Optional[UUID] = None
    parent_name: str
    parent_phone: str
    parent_email: Optional[EmailStr] = None
    address: Optional[str] = None
    previous_school: Optional[str] = None


class AdmissionReviewRequest(BaseModel):
    status: Literal["approved", "rejected", "waitlisted", "under_review"]
    remarks: Optional[str] = None
    assigned_admission_number: Optional[str] = None


class AdmissionBulkApproveRequest(BaseModel):
    form_ids: List[UUID]
    class_section_map: Optional[Dict[str, Dict[str, str]]] = None


class AdmissionFormResponse(BaseModel):
    id: UUID
    reference_number: str
    applicant_name: str
    date_of_birth: date
    gender: Optional[str] = None
    status: str
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    remarks: Optional[str] = None
    documents: List[Dict] = []

    model_config = ConfigDict(from_attributes=True)
