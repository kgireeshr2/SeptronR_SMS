"""
Import all models here so that SQLAlchemy metadata is populated for Alembic migrations.
"""
from app.db.session import Base  # noqa: F401
from app.models.school import School  # noqa: F401
from app.models.auth import User, PasswordResetToken  # noqa: F401
from app.models.rbac import Role, Permission, RolePermission, UserRole  # noqa: F401
from app.models.foundation import SchoolProfile, SchoolSetting  # noqa: F401
from app.models.academic import AcademicYear, AcademicTerm  # noqa: F401
from app.models.admissions import AdmissionFormConfig, AdmissionForm, AdmissionStatus  # noqa: F401
from app.models.classes import Class, Section, Subject, ClassSubject, Timetable  # noqa: F401
from app.models.students import (  # noqa: F401
    Student,
    StudentEnrollment,
    StudentParent,
    StudentDocument,
    StudentPromotion,
    StudentTransfer,
    ParentRelation,
)
from app.models.staff import (  # noqa: F401
    Department,
    Designation,
    Staff,
    StaffDocument,
    LeaveType,
    StaffLeave,
    StaffLeaveBalance,
    StaffPayroll,
    EmploymentType,
    SalaryType,
    LeaveStatus,
    PaymentMethod,
)
from app.models.attendance import (  # noqa: F401
    Holiday,
    AttendanceSession,
    StudentAttendance,
    StaffAttendance,
    SessionType,
    StudentAttendanceStatus,
    StaffAttendanceStatus,
    AttendanceSource,
    HolidayType,
)
from app.models.fees import (  # noqa: F401
    FeeCategory,
    FeeStructure,
    FeeDiscount,
    StudentFeeAssignment,
    FeeInvoice,
    FeeInvoiceItem,
    FeePayment,
    FineConfiguration,
    FeeFrequency,
    DiscountType,
    DiscountApplicableTo,
    InvoiceStatus,
    FineCalcType,
)
from app.models.exams import (  # noqa: F401
    ExamType,
    Exam,
    StudentMark,
    GradingScale,
    ReportCardTemplate,
    AdmitCardConfig,
)
from app.models.library import (  # noqa: F401
    BookCategory,
    Book,
    LibraryMember,
    BookIssue,
)
from app.models.transport import (  # noqa: F401
    Vehicle,
    Route,
    Stop,
    StudentTransport,
    VehicleMaintenance,
    VehicleFuelLog,
)
from app.models.inventory import (  # noqa: F401
    InventoryCategory,
    Supplier,
    Store,
    Item,
    PurchaseOrder,
    PurchaseOrderItem,
    StockEntry,
    StockIssue,
)
from app.models.accounting import (  # noqa: F401
    IncomeCategory,
    ExpenseCategory,
    IncomeRecord,
    ExpenseRecord,
    BudgetHead,
)
from app.models.communications import (  # noqa: F401
    NotificationTemplate,
    Notification,
    BulkMessage,
    MessageLog,
    Announcement,
)
from app.models.calendar import CalendarEvent  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.homework_ptm import (  # noqa: F401
    Homework,
    HomeworkSubmission,
    LessonPlan,
    PTMEvent,
    PTMSlot,
    PTMBooking,
)
from app.models.document_templates import DocumentTemplate  # noqa: F401
from app.models.super_admin import (  # noqa: F401
    SubscriptionPlan,
    SchoolSubscription,
    SchoolFeatureFlag,
    ImpersonationLog,
)
from app.models.vendor_inventory import (  # noqa: F401
    Vendor,
    VendorProduct,
    VendorStock,
    VendorInvoice,
    VendorInvoiceItem,
    VendorSale,
    VendorSaleItem,
    VendorPayment,
)
from app.models.personal_expenses import PersonalExpenseCategory, PersonalExpense  # noqa: F401
