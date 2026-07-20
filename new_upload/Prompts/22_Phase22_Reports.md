# PHASE 22 — REPORTS MODULE

## Pre-Requisite
Phases 1–21 complete. All module data available: students, attendance, fees, exams, staff, library, transport, accounting.

## Objective
Comprehensive reports for all modules with PDF and Excel export. Built-in reports plus a simple custom report builder.

---

## 22.1 Report Categories & Types

### Student Reports
| ID | Report Name | Filters |
|----|-------------|---------|
| student_list | Student Master List | class, section, gender, status |
| student_attendance | Student Attendance Summary | class, section, month, year_id |
| low_attendance | Low Attendance Report | class, threshold_pct, month |
| fee_defaulters | Fee Defaulters Report | class, category, as_of_date |
| fee_collection | Fee Collection Report | date_from, date_to, class, category |
| fee_collection_summary | Fee Collection Summary | month, year_id |
| exam_performance | Exam Performance Report | exam_id, class, section |
| class_result | Class Result Sheet | exam_id, class_id, section_id |
| library_activity | Library Activity Report | date_from, date_to |
| admission_register | Admission Register | year_id, class |
| withdrawn_students | Withdrawn/TC Issued | year_id |

### Staff Reports
| ID | Report Name | Filters |
|----|-------------|---------|
| staff_list | Staff Master List | department, designation, status |
| staff_attendance | Staff Attendance Summary | month, department |
| leave_summary | Leave Utilization Summary | year_id, department |
| payroll_summary | Payroll Summary | month, year |
| staff_by_dept | Staff by Department | — |

### Financial Reports
| ID | Report Name | Filters |
|----|-------------|---------|
| income_expense | Income vs Expense | month, year |
| monthly_pl | Monthly P&L | year_id |
| daily_collection | Daily Fee Collection | date |
| fee_category_wise | Fee Category-wise Collection | year_id |
| expense_category | Expense by Category | date_from, date_to |
| budget_vs_actual | Budget vs Actual | year_id |

---

## 22.2 Report Request Model

```python
class ReportRequest(BaseModel):
    report_id: str
    format: Literal["pdf", "excel", "json"] = "json"
    filters: Dict[str, Any] = {}
    # filters examples:
    # { "class_id": "UUID", "section_id": "UUID", "month": 3, "year": 2025 }
    # { "date_from": "2025-01-01", "date_to": "2025-03-31" }
    # { "threshold_pct": 75, "year_id": "UUID" }
```

---

## 22.3 Report Service Architecture

```python
# backend/app/services/report_service.py

REPORT_REGISTRY: Dict[str, Type[BaseReport]] = {}

def register_report(report_id: str):
    """Decorator to register a report class."""
    def decorator(cls):
        REPORT_REGISTRY[report_id] = cls
        return cls
    return decorator

class BaseReport(ABC):
    """Base class for all reports."""
    def __init__(self, school_id: str, year_id: Optional[str], filters: dict, db: AsyncSession):
        self.school_id = school_id
        self.year_id = year_id
        self.filters = filters
        self.db = db

    @abstractmethod
    async def fetch_data(self) -> List[dict]: ...

    @abstractmethod
    def get_columns(self) -> List[ReportColumn]: ...

    async def as_json(self) -> dict:
        data = await self.fetch_data()
        return {"columns": self.get_columns(), "rows": data, "total": len(data)}

    async def as_excel(self) -> bytes:
        data = await self.fetch_data()
        df = pd.DataFrame(data, columns=[c.key for c in self.get_columns()])
        df.columns = [c.label for c in self.get_columns()]
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Report")
            # Auto-size columns
            ws = writer.sheets["Report"]
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or "")) for c in col) + 4
        buf.seek(0)
        return buf.read()

    async def as_pdf(self) -> bytes:
        data = await self.fetch_data()
        html = render_jinja_template(
            f"reports/{self.__class__.__name__}.html",
            rows=data, columns=self.get_columns(), school=self.school_info, filters=self.filters
        )
        return generate_pdf_from_html(html)

class ReportColumn(BaseModel):
    key: str; label: str; data_type: str = "string"   # string/number/date/money

@register_report("fee_defaulters")
class FeeDefaultersReport(BaseReport):
    def get_columns(self):
        return [
            ReportColumn(key="adm_no", label="Adm. No."),
            ReportColumn(key="student_name", label="Student Name"),
            ReportColumn(key="class_section", label="Class"),
            ReportColumn(key="parent_phone", label="Parent Phone"),
            ReportColumn(key="fee_category", label="Fee Category"),
            ReportColumn(key="amount_due", label="Amount Due", data_type="money"),
            ReportColumn(key="due_date", label="Due Date", data_type="date"),
            ReportColumn(key="days_overdue", label="Days Overdue", data_type="number"),
        ]

    async def fetch_data(self) -> List[dict]:
        # Query: fee_invoices WHERE status IN ('unpaid','partial') AND due_date <= as_of_date
        # JOIN students, student_enrollments, classes, sections, fee_categories
        # Filter by class_id if provided
        as_of = self.filters.get("as_of_date", date.today().isoformat())
        class_id = self.filters.get("class_id")
        ...
```

---

## 22.4 API Endpoints

```
GET  /api/v1/reports                     → list available reports with metadata
POST /api/v1/reports/generate            → generate report (JSON response)
     body: ReportRequest
POST /api/v1/reports/generate?format=pdf   → stream PDF
POST /api/v1/reports/generate?format=excel → stream Excel
GET  /api/v1/reports/scheduled            → list scheduled report jobs
POST /api/v1/reports/scheduled            → create scheduled report
DELETE /api/v1/reports/scheduled/{id}     → delete schedule
```

---

## 22.5 Scheduled Reports via Celery Beat

```python
# backend/app/tasks/report_tasks.py

@celery_app.task
def send_scheduled_report(schedule_id: str):
    """
    1. Load schedule config (report_id, filters, recipients, format)
    2. Generate report using report service
    3. Store file in temp path / S3
    4. Email file as attachment to all recipients
    5. Update last_sent_at
    """

# Scheduled report config stored in school_settings:
# category=reports, key=scheduled_reports, value=JSON array of schedule objects:
# [{
#   "id": "UUID",
#   "report_id": "fee_defaulters",
#   "cron": "0 8 1 * *",     ← 8 AM on 1st of every month
#   "filters": {"as_of_date": "last_month_end"},
#   "recipients": ["principal@school.com"],
#   "format": "excel"
# }]
```

---

## 22.6 Frontend Reports Page (`/admin/reports`)

**Layout:**
- Left panel: Report category accordion (Student / Staff / Financial)
- Right panel: Report form (filter inputs) + Preview + Export buttons

**Report Runner Component:**
```tsx
function ReportRunner({ reportId }: { reportId: string }) {
  const { data: meta } = useQuery(['report-meta', reportId], () => reportsApi.getMeta(reportId));
  const [filters, setFilters] = useState({});
  const [data, setData] = useState(null);

  // Render filter inputs dynamically based on meta.filters config
  // Run report → show table preview
  // Export: PDF / Excel buttons trigger file download

  const runReport = async () => {
    const result = await reportsApi.generate({ report_id: reportId, filters, format: 'json' });
    setData(result.data);
  };

  const exportPdf = () => {
    const url = `/api/v1/reports/generate?format=pdf`;
    downloadFile(url, `POST`, { report_id: reportId, filters, format: 'pdf' });
  };
}
```

**Report Preview:**
- shadcn/ui Table with pagination (client-side for JSON response)
- Money columns formatted as ₹X,XX,XXX (Indian number formatting)
- Date columns formatted per school date_format setting

### `frontend/src/api/reports.ts`
```typescript
export const reportsApi = {
  listAvailable: () => api.get('/reports'),
  generate: (request: ReportRequest) => api.post('/reports/generate', request),
  downloadExcel: async (request: ReportRequest) => {
    const response = await api.post('/reports/generate', { ...request, format: 'excel' }, { responseType: 'blob' });
    downloadBlob(response.data, `${request.report_id}_${Date.now()}.xlsx`);
  },
  downloadPdf: async (request: ReportRequest) => {
    const response = await api.post('/reports/generate', { ...request, format: 'pdf' }, { responseType: 'blob' });
    downloadBlob(response.data, `${request.report_id}_${Date.now()}.pdf`);
  },
  getScheduled: () => api.get('/reports/scheduled'),
  createScheduled: (data: any) => api.post('/reports/scheduled', data),
  deleteScheduled: (id: string) => api.delete(`/reports/scheduled/${id}`),
};
```

---

## 22.7 Report PDF Templates (`backend/app/templates/reports/`)

Create Jinja2 HTML templates for PDF reports:
```
fee_defaulters_report.html
fee_collection_report.html
attendance_summary_report.html
exam_performance_report.html
class_result_report.html
student_list_report.html
staff_attendance_report.html
payroll_summary_report.html
income_expense_report.html
```

Each template structure:
```html
<!-- School letterhead, report title, filters applied, date generated -->
<!-- Table with columns, data rows -->
<!-- Footer: page number, generated by -->
```

---

## 22.8 Tests

```python
async def test_fee_defaulters_report_correct_data(): ...
async def test_report_excel_export_valid_xlsx(): ...
async def test_report_pdf_export_valid_pdf(): ...
async def test_report_school_data_isolation(): ...    # school A can't see school B data
async def test_all_reports_register_correctly(): ...  # REPORT_REGISTRY has all 22 reports
async def test_scheduled_report_sends_email(): ...
```

---

## 22.9 Deliverables Checklist

- [ ] BaseReport ABC with fetch_data, get_columns, as_json, as_excel, as_pdf
- [ ] REPORT_REGISTRY decorator pattern
- [ ] All 22+ reports implemented with correct queries and columns
- [ ] JSON, Excel (openpyxl), and PDF (WeasyPrint) export formats
- [ ] Streaming responses for large Excel/PDF (StreamingResponse)
- [ ] Report API: list, generate, scheduled CRUD
- [ ] Frontend report runner with dynamic filter forms
- [ ] Report preview table with Indian money formatting
- [ ] Scheduled reports stored in school_settings JSON
- [ ] Celery task sends scheduled reports via email
- [ ] All report PDF templates in Jinja2 HTML
- [ ] Money columns displayed in ₹ format (paise ÷ 100, Indian locale)
- [ ] Pagination for large JSON report results
