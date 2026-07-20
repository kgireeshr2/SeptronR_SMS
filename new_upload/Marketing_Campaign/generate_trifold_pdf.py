from reportlab.lib.colors import CMYKColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
BLEED = 3 * mm
SAFE_MARGIN = 7 * mm
PANEL_WIDTH = PAGE_WIDTH / 3

PRIMARY = CMYKColor(95, 65, 0, 10)   # deep blue
ACCENT = CMYKColor(0, 55, 95, 0)     # warm accent
DARK = CMYKColor(0, 0, 0, 85)
LIGHT = CMYKColor(2, 1, 1, 0)
WHITE = CMYKColor(0, 0, 0, 0)

COMPANY = "SeptronR"
TAGLINE = "A leading tech solution"
PHONE = "9490426524 | 7416123742"
ADDRESS = "Banglore 560036"
WEBSITE = "https://septronr.com"

FEATURE_DATA = [
    ("Academic", 22),
    ("Admin", 16),
    ("Finance", 18),
    ("Communication", 14),
    ("Mobile App", 12),
    ("Transport & Inventory", 10),
    ("Audit & Roles", 8),
]


def draw_guides(c: canvas.Canvas):
    c.setStrokeColor(CMYKColor(0, 0, 0, 18))
    c.setLineWidth(0.5)
    c.rect(BLEED, BLEED, PAGE_WIDTH - (2 * BLEED), PAGE_HEIGHT - (2 * BLEED), stroke=1, fill=0)

    for x in [PANEL_WIDTH, PANEL_WIDTH * 2]:
        c.setDash(3, 2)
        c.line(x, BLEED, x, PAGE_HEIGHT - BLEED)
    c.setDash()


def panel_origin(panel_index: int):
    x = panel_index * PANEL_WIDTH
    y = 0
    return x, y


def draw_panel_bg(c: canvas.Canvas, panel_index: int, color):
    x, y = panel_origin(panel_index)
    c.setFillColor(color)
    c.rect(x, y, PANEL_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)


def draw_heading(c: canvas.Canvas, x, y, text, size=22, color=WHITE):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y, text)


def draw_subheading(c: canvas.Canvas, x, y, text, size=11, color=WHITE):
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    c.drawString(x, y, text)


def draw_multiline(c: canvas.Canvas, x, y, lines, size=10, leading=14, color=DARK, bold=False):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    current_y = y
    for line in lines:
        c.drawString(x, current_y, line)
        current_y -= leading


def draw_feature_chip(c: canvas.Canvas, x, y, w, h, title):
    c.setFillColor(WHITE)
    c.roundRect(x, y, w, h, 6, stroke=0, fill=1)
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + w / 2, y + h / 2 - 3, title)


def draw_placeholder(c: canvas.Canvas, x, y, w, h, label):
    c.setFillColor(LIGHT)
    c.roundRect(x, y, w, h, 8, stroke=0, fill=1)
    c.setStrokeColor(CMYKColor(0, 0, 0, 20))
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 8, stroke=1, fill=0)
    c.setFillColor(CMYKColor(0, 0, 0, 55))
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + w / 2, y + h / 2 - 3, label)


def draw_feature_pie(c: canvas.Canvas, x, y, w, h):
    drawing = Drawing(w, h)
    pie = Pie()
    pie.x = 5
    pie.y = 8
    pie.width = w * 0.55
    pie.height = h * 0.82
    pie.data = [value for _, value in FEATURE_DATA]
    pie.labels = [name for name, _ in FEATURE_DATA]
    pie.simpleLabels = 0
    pie.sideLabels = 1
    pie.slices.strokeWidth = 0.5
    pie.slices[0].fillColor = CMYKColor(95, 65, 0, 8)
    pie.slices[1].fillColor = CMYKColor(75, 38, 0, 12)
    pie.slices[2].fillColor = CMYKColor(0, 58, 95, 0)
    pie.slices[3].fillColor = CMYKColor(62, 5, 22, 0)
    pie.slices[4].fillColor = CMYKColor(45, 10, 0, 0)
    pie.slices[5].fillColor = CMYKColor(8, 66, 95, 0)
    pie.slices[6].fillColor = CMYKColor(0, 0, 0, 38)
    pie.slices[0].popout = 4
    pie.slices[0].strokeColor = WHITE
    drawing.add(pie)

    legend_x = w * 0.62
    legend_y = h - 18
    for idx, (name, value) in enumerate(FEATURE_DATA):
        swatch_color = pie.slices[idx].fillColor
        row_y = legend_y - (idx * 16)
        drawing.add(String(legend_x + 18, row_y + 2, f"{name} ({value}%)", fontName="Helvetica", fontSize=8, fillColor=DARK))
        from reportlab.graphics.shapes import Rect
        drawing.add(Rect(legend_x, row_y - 6, 12, 12, fillColor=swatch_color, strokeColor=swatch_color))

    renderPDF.draw(drawing, c, x, y)


def outside_page(c: canvas.Canvas):
    # Outside order: [Column 1, Column 2, Fold-in]
    # Requirement applied: first two columns used as premium front-page spread.

    front_x = 0
    front_w = PANEL_WIDTH * 2
    c.setFillColor(PRIMARY)
    c.rect(front_x, 0, front_w, PAGE_HEIGHT, stroke=0, fill=1)

    # Rich content top band
    c.setFillColor(CMYKColor(0, 0, 0, 18))
    c.rect(front_x, PAGE_HEIGHT - 48, front_w, 48, stroke=0, fill=1)
    draw_heading(c, SAFE_MARGIN, PAGE_HEIGHT - 28, f"{COMPANY} | {TAGLINE}", size=16, color=WHITE)
    draw_subheading(c, SAFE_MARGIN, PAGE_HEIGHT - 41, "AI-powered School Management System for growth-focused institutions", size=9, color=WHITE)

    draw_heading(c, SAFE_MARGIN, PAGE_HEIGHT - 74, "Outsmart Traditional School ERP", size=25, color=WHITE)
    draw_subheading(
        c,
        SAFE_MARGIN,
        PAGE_HEIGHT - 92,
        "Admissions to outcomes, fees to communication, classroom to mobile app — unified with intelligence.",
        size=10,
        color=WHITE,
    )

    draw_multiline(
        c,
        SAFE_MARGIN,
        PAGE_HEIGHT - 115,
        [
            "• Increase operational speed with connected workflows",
            "• Give principals instant visibility across academics and finance",
            "• Keep parents engaged with real-time updates on mobile + WhatsApp",
            "• Build trust through role-based governance and audit transparency",
        ],
        size=9,
        leading=12,
        color=WHITE,
    )

    # Hero + pie chart zone
    left_block_w = front_w * 0.48
    right_block_w = front_w * 0.48
    gap = front_w * 0.04
    left_x = SAFE_MARGIN
    right_x = left_x + left_block_w + gap

    draw_placeholder(c, left_x, 42, left_block_w - SAFE_MARGIN, 108, "HERO VISUAL: DASHBOARD + MOBILE USER")
    draw_feature_pie(c, right_x, 34, right_block_w - SAFE_MARGIN, 122)

    chip_y = 18
    chip_w = (front_w - (2 * SAFE_MARGIN) - 24) / 5
    labels = ["Admissions", "Attendance", "Fees", "Exams", "Mobile App"]
    for index, label in enumerate(labels):
        draw_feature_chip(c, SAFE_MARGIN + index * (chip_w + 6), chip_y, chip_w, 16, label)

    c.setFillColor(ACCENT)
    c.roundRect(SAFE_MARGIN, 2, front_w - (2 * SAFE_MARGIN), 14, 5, stroke=0, fill=1)
    draw_subheading(c, SAFE_MARGIN + 7, 6, f"Book Your Live Demo: {PHONE}  |  {WEBSITE}", size=8, color=WHITE)

    # Panel 3: Fold-in flap
    draw_panel_bg(c, 2, WHITE)
    p3x, _ = panel_origin(2)
    x3 = p3x + SAFE_MARGIN

    c.setFillColor(PRIMARY)
    c.rect(p3x, PAGE_HEIGHT - 45, PANEL_WIDTH, 45, stroke=0, fill=1)
    draw_heading(c, x3, PAGE_HEIGHT - 31, "Execution Confidence", size=15, color=WHITE)

    draw_multiline(
        c,
        x3,
        PAGE_HEIGHT - 65,
        [
            "• Go-live roadmap tailored to your school workflow",
            "• Staff training and role-based onboarding support",
            "• Data migration support from sheets/legacy tools",
            "• Real-time parent communication on mobile and WhatsApp",
            "• Ongoing support for admissions, fees, exams and reporting",
        ],
        size=9,
        leading=13,
        color=DARK,
    )

    draw_placeholder(c, x3, 60, PANEL_WIDTH - (2 * SAFE_MARGIN), 70, "IMPLEMENTATION TIMELINE VISUAL")
    c.setFillColor(ACCENT)
    c.roundRect(x3, 28, PANEL_WIDTH - (2 * SAFE_MARGIN), 22, 6, stroke=0, fill=1)
    draw_subheading(c, x3 + 8, 35, "Get a 20-minute guided walkthrough", size=8.5, color=WHITE)
    draw_multiline(
        c,
        x3,
        16,
        [
            "Call: " + PHONE,
            "Web: " + WEBSITE,
            "Addr: " + ADDRESS,
        ],
        size=8,
        leading=10,
        color=DARK,
    )


def inside_page(c: canvas.Canvas):
    # Inside order: [Inside Left, Inside Center, Inside Right]

    # Panel 4
    draw_panel_bg(c, 0, WHITE)
    p4x, _ = panel_origin(0)
    x4 = p4x + SAFE_MARGIN

    c.setFillColor(PRIMARY)
    c.rect(p4x, PAGE_HEIGHT - 42, PANEL_WIDTH, 42, stroke=0, fill=1)
    draw_heading(c, x4, PAGE_HEIGHT - 28, "Complete School Operations", size=14, color=WHITE)

    draw_multiline(
        c,
        x4,
        PAGE_HEIGHT - 60,
        [
            "Academic Management",
            "• Academic year, class, section, subject",
            "• Timetable planning and homework",
            "• Calendar and day-to-day coordination",
            "",
            "Student & Staff Management",
            "• Admissions and student lifecycle",
            "• Staff profiles, departments and leave",
            "• Daily attendance workflows",
        ],
        size=9,
        leading=12,
        color=DARK,
    )
    draw_placeholder(c, x4, 22, PANEL_WIDTH - (2 * SAFE_MARGIN), 65, "DASHBOARD SCREENSHOT")

    # Panel 5
    draw_panel_bg(c, 1, WHITE)
    p5x, _ = panel_origin(1)
    x5 = p5x + SAFE_MARGIN

    c.setFillColor(PRIMARY)
    c.rect(p5x, PAGE_HEIGHT - 42, PANEL_WIDTH, 42, stroke=0, fill=1)
    draw_heading(c, x5, PAGE_HEIGHT - 28, "Finance, Exams & Governance", size=14, color=WHITE)

    draw_multiline(
        c,
        x5,
        PAGE_HEIGHT - 60,
        [
            "Fees & Accounting",
            "• Fee structures, invoices, receipts",
            "• Payment tracking and due visibility",
            "",
            "Exams & Reports",
            "• Exam setup, marks and result publishing",
            "• Performance insights and reporting",
            "",
            "Governance",
            "• Role-based permissions and audit logs",
            "• Multi-school ready architecture",
        ],
        size=9,
        leading=12,
        color=DARK,
    )
    draw_placeholder(c, x5, 22, PANEL_WIDTH - (2 * SAFE_MARGIN), 65, "FEES + EXAMS VISUAL")

    # Panel 6
    draw_panel_bg(c, 2, LIGHT)
    p6x, _ = panel_origin(2)
    x6 = p6x + SAFE_MARGIN

    c.setFillColor(PRIMARY)
    c.rect(p6x, PAGE_HEIGHT - 42, PANEL_WIDTH, 42, stroke=0, fill=1)
    draw_heading(c, x6, PAGE_HEIGHT - 28, "Mobile App Experience", size=14, color=WHITE)

    draw_multiline(
        c,
        x6,
        PAGE_HEIGHT - 60,
        [
            "Your school in every hand:",
            "• Parent app: attendance, fees, homework, exams",
            "• Teacher app: class and attendance workflows",
            "• Management visibility and approvals",
            "• Instant notifications + WhatsApp integration",
        ],
        size=9,
        leading=12,
        color=DARK,
    )

    mock_w = (PANEL_WIDTH - (2 * SAFE_MARGIN) - 12) / 3
    start_x = x6
    for i, label in enumerate(["Parent App", "Teacher App", "Admin View"]):
        draw_placeholder(c, start_x + i * (mock_w + 6), 40, mock_w, 75, label)

    c.setFillColor(ACCENT)
    c.roundRect(x6, 14, PANEL_WIDTH - (2 * SAFE_MARGIN), 20, 6, stroke=0, fill=1)
    draw_subheading(c, x6 + 7, 20, f"Schedule Demo: {PHONE}", size=8.5, color=WHITE)


def generate_pdf(output_path: str):
    c = canvas.Canvas(output_path, pagesize=landscape(A4))
    c.setTitle("SeptronR_School_ERP_A4_Trifold")

    outside_page(c)
    draw_guides(c)
    c.showPage()

    inside_page(c)
    draw_guides(c)
    c.showPage()

    c.save()


if __name__ == "__main__":
    output_file = "Marketing_Campaign/SeptronR_A4_TriFold_Print_Ready.pdf"
    generate_pdf(output_file)
    print(f"Generated: {output_file}")
