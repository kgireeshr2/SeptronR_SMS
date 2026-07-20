from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.fees import (
    DiscountApplicableTo,
    DiscountNature,
    DiscountType,
    FeeFrequency,
    FineCalcType,
    InvoiceStatus,
)
from app.models.staff import PaymentMethod


class FeeCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class FeeCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FeeCategoryResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeeStructureItem(BaseModel):
    fee_category_id: str
    amount: int = Field(ge=0)
    frequency: FeeFrequency = FeeFrequency.monthly
    due_day: Optional[int] = Field(default=None, ge=1, le=31)
    is_active: bool = True


class FeeStructureCreate(BaseModel):
    class_id: str
    academic_year_id: str
    items: list[FeeStructureItem]


class FeeStructureResponse(BaseModel):
    id: str
    school_id: str
    academic_year_id: str
    class_id: str
    fee_category_id: str
    amount: int
    frequency: FeeFrequency
    due_day: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    fee_category_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FeeDiscountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: DiscountType = DiscountType.percentage
    value: float = Field(ge=0)
    nature: Optional[DiscountNature] = None
    applicable_to: DiscountApplicableTo = DiscountApplicableTo.student
    is_active: bool = True


class FeeDiscountUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    type: Optional[DiscountType] = None
    value: Optional[float] = Field(default=None, ge=0)
    nature: Optional[DiscountNature] = None
    applicable_to: Optional[DiscountApplicableTo] = None
    is_active: Optional[bool] = None


class FeeDiscountResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    type: DiscountType
    value: float
    nature: Optional[DiscountNature] = None
    applicable_to: DiscountApplicableTo
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignFeesToStudentsRequest(BaseModel):
    academic_year_id: str
    class_id: Optional[str] = None
    discount_map: dict[str, str] = Field(default_factory=dict)


class InvoiceGenerationRequest(BaseModel):
    academic_year_id: str
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)
    class_id: Optional[str] = None
    student_id: Optional[str] = None


class FeeInvoiceItemResponse(BaseModel):
    id: str
    fee_category_id: str
    fee_category_name: Optional[str] = None
    amount: int
    discount_amt: int
    fine_applied: int


class FeeInvoiceResponse(BaseModel):
    id: str
    school_id: str
    student_id: str
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    academic_year_id: str
    invoice_number: str
    invoice_date: date
    due_date: date
    status: InvoiceStatus
    total_amount: int
    paid_amount: int
    balance_amount: int
    items: list[FeeInvoiceItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CollectFeeRequest(BaseModel):
    invoice_id: str
    amount: int = Field(gt=0)
    payment_date: date
    payment_method: PaymentMethod
    transaction_id: Optional[str] = None
    remarks: Optional[str] = None


class FeePaymentResponse(BaseModel):
    id: str
    school_id: str
    invoice_id: str
    invoice_number: Optional[str] = None
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    amount: int
    payment_date: date
    payment_method: PaymentMethod
    transaction_id: Optional[str] = None
    receipt_number: str
    collected_by: str
    remarks: Optional[str] = None
    is_reversed: bool = False
    reversal_reason: Optional[str] = None
    created_at: datetime


class ReversePaymentRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class StudentDiscountCreate(BaseModel):
    discount_id: str
    academic_year_id: str
    remarks: Optional[str] = None


class StudentDiscountResponse(BaseModel):
    id: str
    student_id: str
    discount_id: str
    discount_name: str
    discount_type: DiscountType
    discount_value: float
    discount_nature: Optional[DiscountNature] = None
    academic_year_id: str
    remarks: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeeClearanceResponse(BaseModel):
    student_id: str
    student_name: str
    academic_year_id: str
    has_outstanding: bool
    total_outstanding: int
    outstanding_invoices: int


class FeeRolloverRequest(BaseModel):
    from_year_id: str
    to_year_id: str


class FineConfigurationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: FineCalcType = FineCalcType.fixed
    value: float = Field(ge=0)
    applicable_after_days: int = Field(default=0, ge=0)
    is_active: bool = True


class FineConfigurationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    type: Optional[FineCalcType] = None
    value: Optional[float] = Field(default=None, ge=0)
    applicable_after_days: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class FineConfigurationResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    type: FineCalcType
    value: float
    applicable_after_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentFeeStatement(BaseModel):
    student_id: str
    student_name: str
    academic_year_id: str
    total_amount: int
    total_paid: int
    total_due: int
    invoices: list[FeeInvoiceResponse] = Field(default_factory=list)


class DefaulterEntry(BaseModel):
    student_id: str
    student_name: str
    invoice_id: str
    invoice_number: str
    due_date: date
    balance_amount: int
    days_overdue: int


class CollectionSummary(BaseModel):
    total_collected: int
    transaction_count: int
    by_method: dict[str, int]


class OnlinePaymentInitRequest(BaseModel):
    invoice_id: str
    amount: int = Field(gt=0)
    gateway: str = "razorpay"


class OnlinePaymentInitResponse(BaseModel):
    order_id: str
    gateway: str
    amount: int
    currency: str = "INR"
    key_id: Optional[str] = None   # public gateway key for the checkout widget


class OnlinePaymentCallbackRequest(BaseModel):
    order_id: str                  # gateway order id (razorpay_order_id)
    invoice_id: str
    payment_date: date
    # Razorpay checkout result — signature is verified server-side; amount is
    # reconciled from the gateway, NOT trusted from these client fields.
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    transaction_id: Optional[str] = None
    amount: Optional[int] = None
    gateway_response: dict = Field(default_factory=dict)
