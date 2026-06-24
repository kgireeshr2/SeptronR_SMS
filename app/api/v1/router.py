from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.roles import permissions_router
from app.api.v1.endpoints.schools import router as schools_router
from app.api.v1.endpoints.academic_years import router as academic_years_router
from app.api.v1.endpoints.admissions import router as admissions_router
from app.api.v1.endpoints.classes import router as classes_router
from app.api.v1.endpoints.subjects import router as subjects_router
from app.api.v1.endpoints.timetable import router as timetable_router
from app.api.v1.endpoints.students import router as students_router
from app.api.v1.endpoints.departments import router as departments_router
from app.api.v1.endpoints.staff import router as staff_router
from app.api.v1.endpoints.leaves import router as leaves_router
from app.api.v1.endpoints.payroll import router as payroll_router
from app.api.v1.endpoints.attendance import router as attendance_router
from app.api.v1.endpoints.staff_attendance import router as staff_attendance_router
from app.api.v1.endpoints.holidays import router as holidays_router
from app.api.v1.endpoints.fees import router as fees_router
from app.api.v1.endpoints.fees_v2 import router as fees_v2_router
from app.api.v1.endpoints.exams import (
    exam_types_router,
    grading_router,
    exams_router,
    rc_templates_router,
    admit_config_router,
)
from app.api.v1.endpoints.transport import vehicles_router, routes_router, transport_router
from app.api.v1.endpoints.inventory import (
    categories_router as inv_cat_router,
    suppliers_router,
    stores_router,
    items_router,
    po_router,
)
from app.api.v1.endpoints.accounting import (
    income_cat_router,
    expense_cat_router,
    income_router,
    expense_router,
    budget_router,
    summary_router,
)
from app.api.v1.endpoints.library import (
    lib_cat_router,
    books_router,
    members_router,
    issues_router,
)

api_router = APIRouter()

# Phase 2: Auth & RBAC
api_router.include_router(auth_router)
api_router.include_router(roles_router)
api_router.include_router(permissions_router)

# Phase 3: School settings, academic years, admissions
api_router.include_router(schools_router)
api_router.include_router(academic_years_router)
api_router.include_router(admissions_router)

# Phase 4: Classes, subjects, timetable
api_router.include_router(classes_router)
api_router.include_router(subjects_router)
api_router.include_router(timetable_router)

# Phase 5: Student Management
# Self-service router first so `/students/me` matches before `/students/{student_id}`.
from app.api.v1.endpoints.student_self import router as student_self_router
api_router.include_router(student_self_router)
api_router.include_router(students_router, prefix="/students", tags=["students"])

# Phase 6: Staff Management
api_router.include_router(departments_router, tags=["departments", "staff"])
api_router.include_router(staff_router, prefix="/staff", tags=["staff"])
api_router.include_router(leaves_router, prefix="/leaves", tags=["leaves", "staff"])
api_router.include_router(payroll_router, prefix="/payroll", tags=["payroll", "staff"])

# Phase 7: Attendance Management
api_router.include_router(attendance_router, prefix="/attendance", tags=["attendance"])
api_router.include_router(staff_attendance_router, prefix="/staff-attendance", tags=["staff-attendance"])
api_router.include_router(holidays_router, prefix="/holidays", tags=["holidays"])

# Phase 8: Fee Management
api_router.include_router(fees_router, prefix="/fees", tags=["fees"])
api_router.include_router(fees_v2_router)

# Phase 9: Exam Management
api_router.include_router(exam_types_router)
api_router.include_router(grading_router)
api_router.include_router(exams_router)
api_router.include_router(rc_templates_router)
api_router.include_router(admit_config_router)

# Phase 10: Transport Management
api_router.include_router(vehicles_router)
api_router.include_router(routes_router)
api_router.include_router(transport_router)

# Phase 11: Inventory Management
api_router.include_router(inv_cat_router)
api_router.include_router(suppliers_router)
api_router.include_router(stores_router)
api_router.include_router(items_router)
api_router.include_router(po_router)

# Phase 12: Accounting
api_router.include_router(income_cat_router)
api_router.include_router(expense_cat_router)
api_router.include_router(income_router)
api_router.include_router(expense_router)
api_router.include_router(budget_router)
api_router.include_router(summary_router)

# Phase 13: Library Management
api_router.include_router(lib_cat_router)
api_router.include_router(books_router)
api_router.include_router(members_router)
api_router.include_router(issues_router)

# Phase 14: Communications & Notifications
from app.api.v1.endpoints.communications import (
    templates_router as comm_templates_router,
    notifications_router,
    bulk_router,
    announcements_router,
    logs_router as comm_logs_router,
    devices_router,
)
api_router.include_router(comm_templates_router)
api_router.include_router(notifications_router)
api_router.include_router(bulk_router)
api_router.include_router(announcements_router)
api_router.include_router(comm_logs_router)
api_router.include_router(devices_router)

# Phase 15: Homework & PTM
from app.api.v1.endpoints.homework import homework_router, lesson_plans_router, ptm_router
api_router.include_router(homework_router)
api_router.include_router(lesson_plans_router)
api_router.include_router(ptm_router)

# Phase 16: Calendar
from app.api.v1.endpoints.calendar import calendar_router
api_router.include_router(calendar_router)

# Phase 17: Document Templates
from app.api.v1.endpoints.document_templates import templates_router as doc_templates_router
api_router.include_router(doc_templates_router)

# Phase 18: Audit Logs
from app.api.v1.endpoints.audit_logs import audit_router
api_router.include_router(audit_router)

# Phase 19: Settings
from app.api.v1.endpoints.settings import settings_router
api_router.include_router(settings_router)

# Phase 20: Dashboard
from app.api.v1.endpoints.dashboard import dashboard_router
api_router.include_router(dashboard_router)

# Phase 21: Super Admin
from app.api.v1.endpoints.super_admin import superadmin_router
api_router.include_router(superadmin_router)

# Phase 22: Reports
from app.api.v1.endpoints.reports import reports_router
api_router.include_router(reports_router)

# Chat Assistant
from app.api.v1.endpoints.chat import router as chat_router
api_router.include_router(chat_router)

# WhatsApp Webhook (no auth — Meta calls this directly)
from app.api.v1.endpoints.whatsapp_webhook import whatsapp_router
api_router.include_router(whatsapp_router)

# Credential Management
from app.api.v1.endpoints.credentials import router as credentials_router
api_router.include_router(credentials_router)

# Vendor Inventory
from app.api.v1.endpoints.vendor_inventory import router as vendor_inventory_router
api_router.include_router(vendor_inventory_router)

# Personal Expenses (student-level, independent from school fees)
from app.api.v1.endpoints.personal_expenses import router as personal_expenses_router
api_router.include_router(personal_expenses_router)

# Installation (one-time setup)
from app.api.v1.endpoints.install import router as install_router
api_router.include_router(install_router)

# Phase 23: Public School Website (public site + admin management)
from app.api.v1.endpoints.public_site import router as public_site_router
from app.api.v1.endpoints.website_admin import router as website_admin_router
api_router.include_router(public_site_router)
api_router.include_router(website_admin_router)
