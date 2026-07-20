# Feature Prompt 26 — Reports Module

## Round: 4 of 4 — Advanced Features
## Prerequisites: All previous modules complete

---

## Objective

Implement a centralized reports module with 22+ pre-built report types, covering student, attendance, fees, payroll, exam, and financial reporting. Reports are generated as PDF or Excel with filters.

---

## 1. Architecture

```
backend/app/services/reports/
    __init__.py
    base_report.py          # BaseReport abstract class
    registry.py             # report_registry dict
    student_reports.py
    attendance_reports.py
    fee_reports.py
    exam_reports.py
    accounting_reports.py
    staff_reports.py
```

### BaseReport (`base_report.py`)

```python
from abc import ABC, abstractmethod

class BaseReport(ABC):
    name: str           # display name
    report_type: str    # unique key
    category: str       # student/attendance/fees/exam/accounting/staff
    permissions: list[str]  # required permissions

    @abstractmethod
    async def run(self, db, school_id: UUID, filters: dict) -> list[dict]:
        """Execute query and return rows."""

    async def to_excel(self, data: list[dict]) -> bytes:
        """Convert data to openpyxl workbook bytes."""

    async def to_pdf(self, data: list[dict], school, filters: dict) -> bytes:
        """Render WeasyPrint PDF."""
```

### Registry (`registry.py`)

```python
REPORT_REGISTRY: dict[str, type[BaseReport]] = {}

def register(cls):
    REPORT_REGISTRY[cls.report_type] = cls
    return cls
```

---

## 2. Report Types (22 reports)

### Student Reports
| Key | Name |
|-----|------|
| `student_list` | Student List by Class |
| `student_birthday` | Birthday List |
| `student_strength` | Class-wise Strength |
| `new_admissions` | New Admissions |
| `transfer_certificates` | TC Issued |
| `category_wise` | Category / Religion Wise |

### Attendance Reports  
| Key | Name |
|-----|------|
| `daily_attendance` | Daily Attendance Summary |
| `monthly_attendance` | Monthly Attendance Sheet |
| `low_attendance` | Low Attendance Students |
| `staff_attendance_monthly` | Staff Monthly Attendance |
| `absenteeism_trend` | Absenteeism Trend |

### Fee Reports
| Key | Name |
|-----|------|
| `fee_collection` | Fee Collection Report |
| `fee_defaulters` | Fee Defaulters |
| `fee_concession` | Waiver/Concession Report |
| `daily_collection` | Daily Collection Summary |

### Exam Reports
| Key | Name |
|-----|------|
| `merit_list` | Class Merit List |
| `subject_wise_results` | Subject-wise Performance |
| `result_summary` | Exam Result Summary |
| `failed_students` | Students Failed in Subject |

### Financial Reports
| Key | Name |
|-----|------|
| `income_expense` | Income vs Expense |
| `payroll_summary` | Monthly Payroll Summary |
| `budget_utilization` | Budget Utilization |

---

## 3. Sample Implementation

```python
@register
class StudentListReport(BaseReport):
    name = "Student List by Class"
    report_type = "student_list"
    category = "student"
    permissions = ["students:export"]

    async def run(self, db, school_id, filters) -> list[dict]:
        """
        filters: {academic_year_id, class_id, section_id, status, gender}
        Query: students with enrollment → return rows.
        """

@register
class FeeDefaultersReport(BaseReport):
    name = "Fee Defaulters"
    report_type = "fee_defaulters"
    category = "fees"
    permissions = ["fees:export"]

    async def run(self, db, school_id, filters) -> list[dict]:
        """
        filters: {academic_year_id, class_id, min_due_paise}
        Query: invoices with balance > 0, grouped by student.
        """
```

---

## 4. API Endpoints

```
GET    /reports                               → list all available reports     [auth]
GET    /reports/{report_type}?filters=        → run report, return JSON        [varies]
GET    /reports/{report_type}/excel?filters=  → download Excel                [varies]
GET    /reports/{report_type}/pdf?filters=    → download PDF                  [varies]
```

Filter params are passed as query strings and parsed per report type.

---

## 5. Frontend: Reports Page (`/reports`)

- **Category Tabs**: Student | Attendance | Fees | Exam | Financial | Staff
- Per report: Report card with name + Filter form + Run/Excel/PDF buttons
- Results rendered in DataTable with column definitions from report
- Export options always available after running

---

## 6. Report Excel Format

Each report Excel file:
- Sheet 1: Filters used + generated date/time
- Sheet 2: Report data with headers
- Styling: Bold headers, auto-column width, alternating row colors

---

## Verification Checklist

- [ ] All 22 reports registered in REPORT_REGISTRY
- [ ] `GET /reports` returns list with name, category, report_type
- [ ] Filters validated per report — missing required filter returns 422
- [ ] Excel output has 2 sheets (meta + data)
- [ ] Permission check per report's `permissions` list
- [ ] PDF output includes school header + logo + generated date
- [ ] Reports with large data (>1000 rows) use streaming Excel response
