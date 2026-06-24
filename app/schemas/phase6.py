from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, computed_field, model_validator

from app.models.staff import EmploymentType, SalaryType, LeaveStatus, PaymentMethod


class UUIDStrMixin(BaseModel):
    """Mixin that converts UUID fields to strings before validation."""

    @model_validator(mode='before')
    @classmethod
    def convert_uuids(cls, values):
        if hasattr(values, '__dict__'):
            values = {k: v for k, v in values.__dict__.items() if not k.startswith('_')}
        if isinstance(values, dict):
            return {k: str(v) if isinstance(v, UUID) else v for k, v in values.items()}
        return values


# ===================== Department Schemas =====================
class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100)
    hod_id: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    hod_id: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(UUIDStrMixin, DepartmentBase):
    id: str
    school_id: str
    is_active: bool
    hod_name: Optional[str] = None
    staff_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===================== Designation Schemas =====================
class DesignationBase(BaseModel):
    name: str = Field(..., max_length=100)


class DesignationCreate(DesignationBase):
    pass


class DesignationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class DesignationResponse(UUIDStrMixin, DesignationBase):
    id: str
    school_id: str
    is_active: bool
    staff_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===================== Staff Schemas =====================
class StaffBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=10)
    department_id: Optional[str] = None
    designation_id: Optional[str] = None
    date_of_joining: Optional[date] = None
    employment_type: EmploymentType = EmploymentType.permanent
    salary_type: SalaryType = SalaryType.monthly
    monthly_salary: int = 0  # paise
    bank_account_no: Optional[str] = Field(None, max_length=30)
    bank_name: Optional[str] = Field(None, max_length=100)
    ifsc_code: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    qualifications: List[Dict[str, Any]] = Field(default_factory=list)
    experience_years: Optional[float] = None
    # Government IDs
    aadhaar_number: Optional[str] = Field(None, max_length=20)
    pan_number: Optional[str] = Field(None, max_length=15)
    driving_licence: Optional[str] = Field(None, max_length=30)

    @field_validator('qualifications', mode='before')
    @classmethod
    def coerce_qualifications(cls, v: Any) -> List[Dict[str, Any]]:
        return v if v is not None else []


class StaffCreate(StaffBase):
    email: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=15)
    role_ids: List[str] = Field(default_factory=list)


class StaffUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=10)
    department_id: Optional[str] = None
    designation_id: Optional[str] = None
    date_of_joining: Optional[date] = None
    employment_type: Optional[EmploymentType] = None
    salary_type: Optional[SalaryType] = None
    monthly_salary: Optional[int] = None
    bank_account_no: Optional[str] = Field(None, max_length=30)
    bank_name: Optional[str] = Field(None, max_length=100)
    ifsc_code: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None
    qualifications: Optional[List[Dict[str, Any]]] = None
    experience_years: Optional[float] = None
    is_active: Optional[bool] = None
    aadhaar_number: Optional[str] = Field(None, max_length=20)
    pan_number: Optional[str] = Field(None, max_length=15)
    driving_licence: Optional[str] = Field(None, max_length=30)


class StaffResponse(UUIDStrMixin, StaffBase):
    id: str
    school_id: str
    employee_id: str
    user_id: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool
    email: Optional[str] = None
    phone: Optional[str] = None
    department_name: Optional[str] = None
    designation_name: Optional[str] = None
    temp_password: Optional[str] = None  # Only set on creation, shown once
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @computed_field
    @property
    def age(self) -> Optional[int]:
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    @field_serializer("date_of_birth", "date_of_joining")
    def serialize_date(self, dt: Optional[date]) -> Optional[str]:
        return dt.isoformat() if dt else None

    model_config = ConfigDict(from_attributes=True)


class StaffDetailResponse(StaffResponse):
    documents: Optional[List["StaffDocumentResponse"]] = None
    leave_balances: Optional[List["LeaveBalanceResponse"]] = None


class StaffTerminate(BaseModel):
    reason: Optional[str] = None


# ===================== Staff Document Schemas =====================
class StaffDocumentBase(BaseModel):
    doc_type: str = Field(..., max_length=60)
    file_url: str


class StaffDocumentCreate(StaffDocumentBase):
    pass


class StaffDocumentResponse(UUIDStrMixin, StaffDocumentBase):
    id: str
    school_id: str
    staff_id: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===================== Leave Type Schemas =====================
class LeaveTypeBase(BaseModel):
    name: str = Field(..., max_length=60)
    max_days_per_year: int = 0
    is_paid: bool = True


class LeaveTypeCreate(LeaveTypeBase):
    pass


class LeaveTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=60)
    max_days_per_year: Optional[int] = None
    is_paid: Optional[bool] = None
    is_active: Optional[bool] = None


class LeaveTypeResponse(UUIDStrMixin, LeaveTypeBase):
    id: str
    school_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===================== Staff Leave Schemas =====================
class LeaveApplicationBase(BaseModel):
    leave_type_id: str
    from_date: date
    to_date: date
    total_days: float
    reason: Optional[str] = None


class LeaveApplicationCreate(LeaveApplicationBase):
    pass


class LeaveApplicationUpdate(BaseModel):
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    total_days: Optional[float] = None
    reason: Optional[str] = None


class LeaveApplicationReview(BaseModel):
    status: LeaveStatus = Field(..., description="approved or rejected")
    remarks: Optional[str] = None


class LeaveApplicationResponse(UUIDStrMixin, LeaveApplicationBase):
    id: str
    school_id: str
    staff_id: str
    status: LeaveStatus
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    remarks: Optional[str] = None
    staff_name: Optional[str] = None
    leave_type_name: Optional[str] = None
    approver_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("from_date", "to_date")
    def serialize_date(self, dt: date) -> str:
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


# ===================== Leave Balance Schemas =====================
class LeaveBalanceResponse(UUIDStrMixin):
    id: str
    school_id: str
    staff_id: str
    leave_type_id: str
    academic_year_id: str
    entitled_days: float
    used_days: float
    remaining_days: float
    leave_type_name: Optional[str] = None
    academic_year_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeaveAllocationRequest(BaseModel):
    staff_id: str
    leave_type_id: str
    academic_year_id: str
    entitled_days: float


class LeaveBalanceUpdateRequest(BaseModel):
    entitled_days: float


# ===================== Payroll Schemas =====================
class PayrollGenerateRequest(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000, le=2100)
    academic_year_id: str
    staff_ids: Optional[List[str]] = Field(
        None, description="If None, generate for all active staff"
    )


class PayrollEntryCreate(BaseModel):
    staff_id: str
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000, le=2100)
    academic_year_id: str
    basic_salary: int  # paise
    allowances: Dict[str, int] = Field(default_factory=dict)  # {"hra": 0, "da": 0, "ta": 0, "other": 0}
    deductions: Dict[str, int] = Field(default_factory=dict)  # {"pf": 0, "esi": 0, "tds": 0, "loan": 0, "other": 0}
    gross_salary: int
    net_salary: int
    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None


class PayrollUpdate(BaseModel):
    basic_salary: Optional[int] = None
    allowances: Optional[Dict[str, int]] = None
    deductions: Optional[Dict[str, int]] = None
    gross_salary: Optional[int] = None
    net_salary: Optional[int] = None
    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    is_paid: Optional[bool] = None


class PayrollMarkPaidRequest(BaseModel):
    payroll_ids: List[str]
    payment_date: date
    payment_method: PaymentMethod


class PayrollResponse(UUIDStrMixin):
    id: str
    school_id: str
    staff_id: str
    academic_year_id: str
    month: int
    year: int
    basic_salary: int
    allowances: Dict[str, int]
    deductions: Dict[str, int]
    gross_salary: int
    net_salary: int
    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    is_paid: bool
    receipt_url: Optional[str] = None
    staff_name: Optional[str] = None
    employee_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("payment_date")
    def serialize_date(self, dt: Optional[date]) -> Optional[str]:
        return dt.isoformat() if dt else None

    model_config = ConfigDict(from_attributes=True)


# ===================== Statistics Schemas =====================
class StaffStatistics(BaseModel):
    total_staff: int = 0
    active_staff: int = 0
    inactive_staff: int = 0
    by_department: Dict[str, int] = Field(default_factory=dict)
    by_designation: Dict[str, int] = Field(default_factory=dict)
    by_employment_type: Dict[str, int] = Field(default_factory=dict)


class LeaveStatistics(BaseModel):
    total_leaves: int = 0
    pending_leaves: int = 0
    approved_leaves: int = 0
    rejected_leaves: int = 0
    by_leave_type: Dict[str, int] = Field(default_factory=dict)
