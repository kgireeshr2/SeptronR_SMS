"""Celery report generation tasks — implemented in Phase 22."""
from app.tasks.celery_app import celery


@celery.task(name="app.tasks.reports.generate_pdf_report", queue="reports")
def generate_pdf_report(report_type: str, params: dict, user_id: str):
    """Generate PDF report for download."""
    pass


@celery.task(name="app.tasks.reports.generate_excel_export", queue="reports")
def generate_excel_export(module: str, filters: dict, user_id: str):
    """Generate Excel export for module data."""
    pass
