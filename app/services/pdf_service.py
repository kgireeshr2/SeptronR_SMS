"""
PDF Generation Service — uses reportlab for all document types.
Covers: Fee Receipt, Report Card, Admit Card, Transfer Certificate, ID Card, Payslip.
"""
from __future__ import annotations

import io
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _fmt_money(paise: int) -> str:
    """Convert paise/cents (integer) to display string like ₹ 1,234.00"""
    rupees = paise / 100.0
    return f"\u20b9 {rupees:,.2f}"


def _fmt_date(d: Optional[date | str]) -> str:
    if d is None:
        return "—"
    if isinstance(d, str):
        try:
            d = datetime.fromisoformat(d).date()
        except Exception:
            return str(d)
    return d.strftime("%d %b %Y")


# ── Fee Receipt ───────────────────────────────────────────────────────────────

def generate_fee_receipt_pdf(data: dict) -> bytes:
    """
    data keys:
      school_name, school_address?, school_phone?, school_logo_url?
      receipt_number, payment_date, payment_method, transaction_ref?
      student_name, admission_number, class_name?, section_name?
      collected_by_name?
      items: [{fee_type_name, amount_paid, discount_amount}]
      total_amount, total_discount, remarks?
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    bold = ParagraphStyle("bold", parent=styles["Normal"], fontName="Helvetica-Bold")
    center_bold = ParagraphStyle(
        "center_bold", parent=styles["Normal"], fontName="Helvetica-Bold", alignment=TA_CENTER
    )
    center = ParagraphStyle("center", parent=styles["Normal"], alignment=TA_CENTER)
    right = ParagraphStyle("right_style", parent=styles["Normal"], alignment=TA_RIGHT)

    story = []

    # Header
    story.append(Paragraph(data.get("school_name", "School"), center_bold))
    if data.get("school_address"):
        story.append(Paragraph(data["school_address"], center))
    if data.get("school_phone"):
        story.append(Paragraph(f"Phone: {data['school_phone']}", center))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("FEE RECEIPT", center_bold))
    story.append(Spacer(1, 0.2 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.3 * cm))

    # Receipt meta grid
    meta = [
        [
            Paragraph(f"<b>Receipt No:</b> {data.get('receipt_number', '')}", styles["Normal"]),
            Paragraph(
                f"<b>Date:</b> {_fmt_date(data.get('payment_date'))}", styles["Normal"]
            ),
        ],
        [
            Paragraph(f"<b>Student:</b> {data.get('student_name', '')}", styles["Normal"]),
            Paragraph(
                f"<b>Adm No:</b> {data.get('admission_number', '')}", styles["Normal"]
            ),
        ],
    ]
    class_section = " - ".join(
        filter(None, [data.get("class_name"), data.get("section_name")])
    )
    if class_section:
        meta.append(
            [
                Paragraph(f"<b>Class:</b> {class_section}", styles["Normal"]),
                Paragraph(
                    f"<b>Mode:</b> {data.get('payment_method', '').replace('_', ' ').title()}",
                    styles["Normal"],
                ),
            ]
        )
    if data.get("transaction_ref"):
        meta.append(
            [
                Paragraph(
                    f"<b>Transaction Ref:</b> {data['transaction_ref']}", styles["Normal"]
                ),
                Paragraph("", styles["Normal"]),
            ]
        )

    meta_tbl = Table(meta, colWidths=[9 * cm, 9 * cm])
    meta_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(meta_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Items table
    headers = ["Fee Type", "Amount", "Discount", "Net Paid"]
    rows = [headers]
    for item in data.get("items", []):
        amt = item.get("amount_paid", 0)
        disc = item.get("discount_amount", 0)
        net = amt - disc
        rows.append(
            [
                item.get("fee_type_name", ""),
                _fmt_money(amt),
                _fmt_money(disc) if disc else "—",
                _fmt_money(net),
            ]
        )

    total = data.get("total_amount", 0)
    disc_total = data.get("total_discount", 0)
    rows.append(
        [
            Paragraph("<b>TOTAL</b>", bold),
            Paragraph(f"<b>{_fmt_money(total)}</b>", bold),
            Paragraph(f"<b>{_fmt_money(disc_total)}</b>" if disc_total else "<b>—</b>", bold),
            Paragraph(f"<b>{_fmt_money(total - disc_total)}</b>", bold),
        ]
    )

    col_widths = [8 * cm, 3.5 * cm, 3.5 * cm, 3 * cm]
    items_tbl = Table(rows, colWidths=col_widths)
    items_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f1f5f9")]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(items_tbl)
    story.append(Spacer(1, 0.5 * cm))

    if data.get("remarks"):
        story.append(Paragraph(f"<i>Remarks: {data['remarks']}</i>", styles["Normal"]))
        story.append(Spacer(1, 0.3 * cm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.3 * cm))
    footer_data = [
        [
            Paragraph(
                f"Collected by: {data.get('collected_by_name', '—')}", styles["Normal"]
            ),
            Paragraph("Authorised Signatory", right),
        ]
    ]
    footer_tbl = Table(footer_data, colWidths=[9 * cm, 9 * cm])
    story.append(footer_tbl)
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("_________________________________", right))
    story.append(Paragraph("Signature & Stamp", right))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Report Card ───────────────────────────────────────────────────────────────

def generate_report_card_pdf(data: dict) -> bytes:
    """
    data keys:
      school_name, school_address?, academic_year_name, exam_type_name
      student_name, admission_number, class_name, section_name,
      roll_number?, date_of_birth?
      subjects: [{subject_name, full_marks, pass_marks, marks_obtained,
                  grade?, percentage?, result}]
      total_marks, total_obtained, overall_percentage, overall_grade?,
      class_rank?, section_rank?, result (Pass/Fail, etc.), remarks?
      principal_name?
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    center_bold = ParagraphStyle(
        "cb", parent=styles["Normal"], fontName="Helvetica-Bold", alignment=TA_CENTER, fontSize=13
    )
    center = ParagraphStyle("c", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9)
    normal = ParagraphStyle("n", parent=styles["Normal"], fontSize=9)
    bold9 = ParagraphStyle("b9", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9)

    story = []

    # Header
    story.append(Paragraph(data.get("school_name", "School"), center_bold))
    if data.get("school_address"):
        story.append(Paragraph(data["school_address"], center))
    story.append(Spacer(1, 0.2 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e40af")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            f"REPORT CARD &mdash; {data.get('exam_type_name', '')} "
            f"({data.get('academic_year_name', '')})",
            center_bold,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    # Student info grid
    info_rows = [
        [
            Paragraph(f"<b>Name:</b> {data.get('student_name', '')}", normal),
            Paragraph(f"<b>Adm No:</b> {data.get('admission_number', '')}", normal),
        ],
        [
            Paragraph(
                f"<b>Class:</b> {data.get('class_name', '')} &ndash; {data.get('section_name', '')}",
                normal,
            ),
            Paragraph(f"<b>Roll No:</b> {data.get('roll_number', '—')}", normal),
        ],
    ]
    if data.get("date_of_birth"):
        info_rows.append(
            [
                Paragraph(f"<b>DOB:</b> {_fmt_date(data['date_of_birth'])}", normal),
                Paragraph("", normal),
            ]
        )
    info_tbl = Table(info_rows, colWidths=[9 * cm, 9 * cm])
    info_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(info_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Marks table
    hdr = ["Subject", "Max Marks", "Pass Marks", "Obtained", "Grade", "Result"]
    rows = [hdr]
    for subj in data.get("subjects", []):
        rows.append(
            [
                subj.get("subject_name", ""),
                str(subj.get("full_marks", "")),
                str(subj.get("pass_marks", "")),
                str(subj.get("marks_obtained", "A")) if not subj.get("is_absent") else "AB",
                subj.get("grade") or "—",
                subj.get("result", "—"),
            ]
        )

    marks_tbl = Table(rows, colWidths=[5.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2 * cm, 2.5 * cm])
    marks_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f9ff")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(marks_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Summary row
    summary_data = [
        [
            Paragraph(f"<b>Total:</b> {data.get('total_obtained', 0)}/{data.get('total_marks', 0)}", bold9),
            Paragraph(f"<b>Percentage:</b> {data.get('overall_percentage', 0):.2f}%", bold9),
            Paragraph(f"<b>Grade:</b> {data.get('overall_grade', '—')}", bold9),
            Paragraph(
                f"<b>Result:</b> <font color='{'green' if data.get('result') == 'Pass' else 'red'}'>"
                f"{data.get('result', '—')}</font>",
                bold9,
            ),
        ]
    ]
    if data.get("class_rank"):
        summary_data[0].append(Paragraph(f"<b>Class Rank:</b> {data['class_rank']}", bold9))
    summary_tbl = Table(summary_data, colWidths=[4 * cm, 4 * cm, 3 * cm, 3 * cm, 4 * cm])
    summary_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e0f2fe")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#7dd3fc")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_tbl)

    if data.get("remarks"):
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(f"<b>Remarks:</b> {data['remarks']}", normal))

    # Signatures
    story.append(Spacer(1, 1.5 * cm))
    sig_data = [
        [
            Paragraph("Class Teacher", center),
            Paragraph("Examination Controller", center),
            Paragraph(f"Principal{': ' + data['principal_name'] if data.get('principal_name') else ''}", center),
        ]
    ]
    sig_tbl = Table(sig_data, colWidths=[6 * cm, 6 * cm, 6 * cm])
    sig_tbl.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 30),
                ("LINEABOVE", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    story.append(sig_tbl)

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Admit Card ────────────────────────────────────────────────────────────────

def generate_admit_card_pdf(student_exams_list: List[dict], config: dict) -> bytes:
    """
    student_exams_list: each dict has
      student_name, admission_number, class_name, section_name,
      roll_number?, exams: [{subject_name, exam_date, start_time, end_time, venue?}]
    config: school_name, school_address?, exam_type_name, instructions?
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    center_bold = ParagraphStyle(
        "cb", parent=styles["Normal"], fontName="Helvetica-Bold", alignment=TA_CENTER, fontSize=12
    )
    center = ParagraphStyle("c", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9)
    normal = ParagraphStyle("n", parent=styles["Normal"], fontSize=9)

    story = []

    for idx, student in enumerate(student_exams_list):
        if idx > 0:
            from reportlab.platypus import PageBreak
            story.append(PageBreak())

        story.append(Paragraph(config.get("school_name", "School"), center_bold))
        if config.get("school_address"):
            story.append(Paragraph(config["school_address"], center))
        story.append(Spacer(1, 0.2 * cm))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e40af")))
        story.append(Spacer(1, 0.2 * cm))
        story.append(
            Paragraph(
                f"ADMIT CARD &mdash; {config.get('exam_type_name', 'Examination')}",
                center_bold,
            )
        )
        story.append(Spacer(1, 0.3 * cm))

        # Student info
        info_rows = [
            [
                Paragraph(f"<b>Name:</b> {student.get('student_name', '')}", normal),
                Paragraph(f"<b>Adm No:</b> {student.get('admission_number', '')}", normal),
            ],
            [
                Paragraph(
                    f"<b>Class:</b> {student.get('class_name', '')} &ndash; {student.get('section_name', '')}",
                    normal,
                ),
                Paragraph(f"<b>Roll No:</b> {student.get('roll_number', '—')}", normal),
            ],
        ]
        info_tbl = Table(info_rows, colWidths=[9 * cm, 9 * cm])
        info_tbl.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(info_tbl)
        story.append(Spacer(1, 0.4 * cm))

        # Exam schedule table
        hdr = ["Subject", "Date", "Time", "Venue"]
        rows = [hdr]
        for exam in student.get("exams", []):
            time_str = f"{exam.get('start_time', '')} – {exam.get('end_time', '')}"
            rows.append(
                [
                    exam.get("subject_name", ""),
                    _fmt_date(exam.get("exam_date")),
                    time_str,
                    exam.get("venue") or "—",
                ]
            )

        exam_tbl = Table(rows, colWidths=[5 * cm, 4 * cm, 5 * cm, 4 * cm])
        exam_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f9ff")]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ]
            )
        )
        story.append(exam_tbl)

        if config.get("instructions"):
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph("<b>Instructions:</b>", normal))
            for line in config["instructions"].split("\n"):
                line = line.strip()
                if line:
                    story.append(Paragraph(f"• {line}", normal))

        story.append(Spacer(1, 1.5 * cm))
        sig_row = [
            [
                Paragraph("Student Signature", center),
                Paragraph("Parent Signature", center),
                Paragraph("Principal / Controller", center),
            ]
        ]
        sig_tbl = Table(sig_row, colWidths=[6 * cm, 6 * cm, 6 * cm])
        sig_tbl.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 30),
                    ("LINEABOVE", (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )
        story.append(sig_tbl)

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Transfer Certificate ──────────────────────────────────────────────────────

def generate_transfer_certificate_pdf(data: dict) -> bytes:
    """
    data keys:
      school_name, school_address?, school_phone?
      tc_number, issue_date
      student_name, admission_number, date_of_birth, gender, category?,
      nationality?, religion?, blood_group?
      class_last_studied, section?, academic_year_name?
      admission_date, leaving_date, reason?
      conduct?, remarks?
      principal_name?, issued_by_name?
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    center_bold = ParagraphStyle(
        "cb", parent=styles["Normal"], fontName="Helvetica-Bold", alignment=TA_CENTER, fontSize=14
    )
    center = ParagraphStyle("c", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10)
    center_sub = ParagraphStyle("cs", parent=styles["Normal"], alignment=TA_CENTER, fontSize=11, fontName="Helvetica-Bold")
    normal = ParagraphStyle("n", parent=styles["Normal"], fontSize=10)
    right = ParagraphStyle("r", parent=styles["Normal"], alignment=TA_RIGHT, fontSize=9)

    story = []

    story.append(Paragraph(data.get("school_name", "School"), center_bold))
    if data.get("school_address"):
        story.append(Paragraph(data["school_address"], center))
    if data.get("school_phone"):
        story.append(Paragraph(f"Phone: {data['school_phone']}", center))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("TRANSFER CERTIFICATE", center_sub))
    story.append(Spacer(1, 0.2 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 0.2 * cm))

    story.append(
        Paragraph(
            f"<b>TC No:</b> {data.get('tc_number', '')}  &nbsp;&nbsp;&nbsp; "
            f"<b>Issue Date:</b> {_fmt_date(data.get('issue_date'))}",
            right,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    fields = [
        ("1.", "Name of Student", data.get("student_name", "")),
        ("2.", "Admission Number", data.get("admission_number", "")),
        ("3.", "Date of Birth", _fmt_date(data.get("date_of_birth"))),
        ("4.", "Gender", data.get("gender", "").title()),
        ("5.", "Nationality", data.get("nationality", "—")),
        ("6.", "Religion", data.get("religion", "—")),
        ("7.", "Category", data.get("category", "—")),
        ("8.", "Blood Group", data.get("blood_group", "—")),
        ("9.", "Date of Admission", _fmt_date(data.get("admission_date"))),
        ("10.", "Class last studied", data.get("class_last_studied", "—")),
        ("11.", "Academic Year", data.get("academic_year_name", "—")),
        ("12.", "Date of Leaving", _fmt_date(data.get("leaving_date"))),
        ("13.", "Reason for Leaving", data.get("reason", "—")),
        ("14.", "Conduct", data.get("conduct", "Good")),
        ("15.", "Remarks", data.get("remarks", "—")),
    ]

    for num, label, value in fields:
        row_tbl = Table(
            [[Paragraph(f"<b>{num}</b>", normal), Paragraph(f"<b>{label}</b>", normal), Paragraph(value, normal)]],
            colWidths=[1 * cm, 6.5 * cm, 9 * cm],
        )
        row_tbl.setStyle(
            TableStyle(
                [
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
                ]
            )
        )
        story.append(row_tbl)

    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            "This certificate is issued on the request of the student / parent.",
            ParagraphStyle("italic_center", parent=styles["Normal"], alignment=TA_CENTER, fontName="Helvetica-Oblique"),
        )
    )
    story.append(Spacer(1, 1.5 * cm))

    sig_data = [
        [
            Paragraph("Class Teacher", center),
            Paragraph(
                f"{'Principal: ' + data['principal_name'] if data.get('principal_name') else 'Principal'}",
                center,
            ),
        ]
    ]
    sig_tbl = Table(sig_data, colWidths=[9 * cm, 9 * cm])
    sig_tbl.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 30),
                ("LINEABOVE", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    story.append(sig_tbl)

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Student ID Card ───────────────────────────────────────────────────────────

def generate_id_card_pdf(students: List[dict], school_info: dict) -> bytes:
    """
    students: list of dicts:
      student_name, admission_number, class_name, section_name,
      date_of_birth?, blood_group?, address?, phone?
    school_info: school_name, school_address?, school_phone?, school_email?
    Renders 4 ID cards per A4 page (2×2 grid).
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1 * cm,
        leftMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
    )
    styles = getSampleStyleSheet()
    card_title = ParagraphStyle(
        "ct", parent=styles["Normal"], fontName="Helvetica-Bold", alignment=TA_CENTER, fontSize=8
    )
    card_school = ParagraphStyle(
        "cs", parent=styles["Normal"], fontName="Helvetica-Bold", alignment=TA_CENTER, fontSize=7
    )
    card_field = ParagraphStyle("cf", parent=styles["Normal"], fontSize=7)
    card_small = ParagraphStyle("csm", parent=styles["Normal"], fontSize=6, alignment=TA_CENTER)

    card_w = 8.5 * cm
    card_h = 5.5 * cm
    col_widths = [card_w, 0.5 * cm, card_w]

    def _build_card(student: dict) -> List:
        """Build a list of paragraphs for one ID card."""
        items = []
        items.append(Paragraph(school_info.get("school_name", ""), card_school))
        items.append(Spacer(1, 2))
        items.append(HRFlowable(width=card_w - 0.4 * cm, thickness=1, color=colors.HexColor("#1e40af")))
        items.append(Spacer(1, 2))
        items.append(Paragraph("STUDENT IDENTITY CARD", card_title))
        items.append(Spacer(1, 3))

        fields_inner = [
            ("Name", student.get("student_name", "")),
            ("Adm. No.", student.get("admission_number", "")),
            ("Class", f"{student.get('class_name', '')} - {student.get('section_name', '')}"),
        ]
        if student.get("blood_group"):
            fields_inner.append(("Blood Grp", student["blood_group"]))
        if student.get("date_of_birth"):
            fields_inner.append(("DOB", _fmt_date(student["date_of_birth"])))

        for lbl, val in fields_inner:
            tbl = Table(
                [[Paragraph(f"<b>{lbl}:</b>", card_field), Paragraph(val, card_field)]],
                colWidths=[2 * cm, 5.5 * cm],
            )
            tbl.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 2)]))
            items.append(tbl)

        items.append(Spacer(1, 3))
        if school_info.get("school_phone"):
            items.append(Paragraph(f"Ph: {school_info['school_phone']}", card_small))
        return items

    story = []
    # Pair students into rows of 2
    for i in range(0, len(students), 2):
        left = students[i]
        right = students[i + 1] if i + 1 < len(students) else None

        left_cell = _build_card(left)
        right_cell = _build_card(right) if right else [Paragraph("", card_small)]

        row_data = [[left_cell, "", right_cell]]
        grid = Table(row_data, colWidths=col_widths)
        grid.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (0, 0), 1, colors.HexColor("#1e40af")),
                    ("BOX", (2, 0), (2, 0), 1, colors.HexColor("#1e40af") if right else colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(grid)
        story.append(Spacer(1, 0.5 * cm))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Payslip PDF ───────────────────────────────────────────────────────────────

def generate_payslip_pdf(data: dict) -> bytes:
    """
    data keys:
      school_name, school_address?
      employee_name, employee_id, designation, department?
      month, year, payment_date?
      basic_salary (paise), allowances: [{name, amount}],
      deductions: [{name, amount}], net_salary (paise)
      bank_name?, bank_account_no?
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    center_bold = ParagraphStyle(
        "cb", parent=styles["Normal"], fontName="Helvetica-Bold", alignment=TA_CENTER, fontSize=14
    )
    center_sub = ParagraphStyle(
        "cs", parent=styles["Normal"], fontName="Helvetica-Bold", alignment=TA_CENTER, fontSize=11
    )
    center = ParagraphStyle("c", parent=styles["Normal"], alignment=TA_CENTER)
    normal = ParagraphStyle("n", parent=styles["Normal"], fontSize=10)
    bold10 = ParagraphStyle("b10", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10)
    right = ParagraphStyle("r", parent=styles["Normal"], alignment=TA_RIGHT, fontSize=10)

    story = []

    story.append(Paragraph(data.get("school_name", "School"), center_bold))
    if data.get("school_address"):
        story.append(Paragraph(data["school_address"], center))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.black))
    story.append(Spacer(1, 0.2 * cm))

    import calendar as cal
    month_name = cal.month_name[data.get("month", 1)]
    story.append(Paragraph(f"PAYSLIP &mdash; {month_name} {data.get('year', '')}", center_sub))
    story.append(Spacer(1, 0.3 * cm))

    emp_rows = [
        [
            Paragraph(f"<b>Name:</b> {data.get('employee_name', '')}", normal),
            Paragraph(f"<b>Emp. ID:</b> {data.get('employee_id', '')}", normal),
        ],
        [
            Paragraph(f"<b>Designation:</b> {data.get('designation', '')}", normal),
            Paragraph(f"<b>Department:</b> {data.get('department', '—')}", normal),
        ],
    ]
    if data.get("payment_date"):
        emp_rows.append(
            [
                Paragraph(f"<b>Payment Date:</b> {_fmt_date(data['payment_date'])}", normal),
                Paragraph("", normal),
            ]
        )
    emp_tbl = Table(emp_rows, colWidths=[9 * cm, 9 * cm])
    emp_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(emp_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Earnings & Deductions side by side
    earnings = [["Earnings", "Amount"]]
    earnings.append(["Basic Salary", _fmt_money(data.get("basic_salary", 0))])
    for a in data.get("allowances", []):
        earnings.append([a.get("name", "Allowance"), _fmt_money(a.get("amount", 0))])

    deductions = [["Deductions", "Amount"]]
    for d in data.get("deductions", []):
        deductions.append([d.get("name", "Deduction"), _fmt_money(d.get("amount", 0))])
    if not data.get("deductions"):
        deductions.append(["—", "—"])

    # Pad rows for equal length
    max_rows = max(len(earnings), len(deductions))
    while len(earnings) < max_rows:
        earnings.append(["", ""])
    while len(deductions) < max_rows:
        deductions.append(["", ""])

    # Combine
    combined = []
    for e_row, d_row in zip(earnings, deductions):
        combined.append(e_row + [""] + d_row)

    combined_tbl = Table(combined, colWidths=[4 * cm, 3.5 * cm, 0.5 * cm, 4 * cm, 3.5 * cm])
    combined_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#15803d")),
                ("BACKGROUND", (3, 0), (4, 0), colors.HexColor("#b91c1c")),
                ("TEXTCOLOR", (0, 0), (1, 0), colors.white),
                ("TEXTCOLOR", (3, 0), (4, 0), colors.white),
                ("FONTNAME", (0, 0), (4, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("ALIGN", (4, 0), (4, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (1, -1), [colors.white, colors.HexColor("#f0fdf4")]),
                ("ROWBACKGROUNDS", (3, 1), (4, -1), [colors.white, colors.HexColor("#fef2f2")]),
                ("GRID", (0, 0), (1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("GRID", (3, 0), (4, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(combined_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Net salary
    net_row = Table(
        [[Paragraph("<b>NET SALARY</b>", bold10), Paragraph(f"<b>{_fmt_money(data.get('net_salary', 0))}</b>", right)]],
        colWidths=[14 * cm, 4 * cm],
    )
    net_row.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(net_row)

    if data.get("bank_name"):
        story.append(Spacer(1, 0.3 * cm))
        story.append(
            Paragraph(
                f"Bank: {data['bank_name']}  |  A/C: {data.get('bank_account_no', '—')}",
                ParagraphStyle("bank", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#64748b")),
            )
        )

    story.append(Spacer(1, 1.5 * cm))
    story.append(
        Paragraph(
            "This is a computer-generated payslip and does not require signature.",
            ParagraphStyle(
                "disc",
                parent=styles["Normal"],
                alignment=TA_CENTER,
                fontSize=8,
                textColor=colors.HexColor("#94a3b8"),
            ),
        )
    )

    doc.build(story)
    buf.seek(0)
    return buf.read()
