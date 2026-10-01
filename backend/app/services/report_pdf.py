"""
Renders a ReportResponse to PDF bytes with reportlab.

Two things worth knowing:
  * Text goes through xml escaping before hitting Paragraph. Merchant names
    are user-supplied, and reportlab paragraphs parse an XML-like markup, so
    a merchant such as "A&B <Co>" would otherwise raise or garble the PDF.
  * The bundled DejaVu Sans font is used because the built-in Helvetica has
    no ₹ glyph. If the font files are missing, we fall back to Helvetica and
    write "Rs. " instead of "₹" rather than emitting a broken glyph.
"""
import io
import logging
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.report import ReportResponse

logger = logging.getLogger("expense_manager")

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_unicode_font_ok: bool | None = None

INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6b7280")
LINE = colors.HexColor("#e5e7eb")
HEADER_BG = colors.HexColor("#f3f4f6")
ACCENT = colors.HexColor("#2563eb")


def _ensure_fonts() -> bool:
    global _unicode_font_ok
    if _unicode_font_ok is None:
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", str(FONT_DIR / "DejaVuSans.ttf")))
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
            _unicode_font_ok = True
        except Exception:
            logger.warning("Bundled DejaVu fonts not found; PDF will use Helvetica and 'Rs.'.")
            _unicode_font_ok = False
    return _unicode_font_ok


def build_pdf(report: ReportResponse) -> bytes:
    unicode_ok = _ensure_fonts()
    regular = "DejaVuSans" if unicode_ok else "Helvetica"
    bold = "DejaVuSans-Bold" if unicode_ok else "Helvetica-Bold"

    def t(text: str) -> str:
        """Fallback currency substitution + XML escaping for Paragraph content."""
        if not unicode_ok:
            text = text.replace("₹", "Rs. ")
        return escape(text)

    def money(amount: float) -> str:
        return t(f"₹{amount:,.2f}")

    body = ParagraphStyle("body", fontName=regular, fontSize=9.5, leading=14, textColor=INK)
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=11, textColor=MUTED)
    title = ParagraphStyle("title", parent=body, fontName=bold, fontSize=20, leading=24)
    subtitle = ParagraphStyle("subtitle", parent=body, fontSize=11, leading=15, textColor=MUTED)
    h2 = ParagraphStyle("h2", parent=body, fontName=bold, fontSize=12, leading=16, spaceBefore=14, spaceAfter=6)
    cell = ParagraphStyle("cell", parent=body, fontSize=9, leading=12)
    cell_r = ParagraphStyle("cell_r", parent=cell, alignment=TA_RIGHT)
    head = ParagraphStyle("head", parent=cell, fontName=bold, textColor=MUTED, fontSize=8)
    head_r = ParagraphStyle("head_r", parent=head, alignment=TA_RIGHT)
    metric_label = ParagraphStyle("metric_label", parent=small)
    metric_value = ParagraphStyle("metric_value", parent=body, fontName=bold, fontSize=13, leading=17)

    doc_width = A4[0] - 36 * mm

    def data_table(rows, col_widths, right_cols=()):
        table = Table(rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    story = []
    story.append(Paragraph("Expense Report", title))
    story.append(Paragraph(t(report.period_label), subtitle))
    if report.category_filter:
        story.append(Paragraph(t(f"Category: {report.category_filter}"), subtitle))
    story.append(Spacer(1, 10))

    # Headline metrics
    cmp = report.comparison
    if cmp.change_percent is None:
        change_text = "N/A"
    else:
        change_text = f"{cmp.change_percent:+.1f}%"
    metrics = Table(
        [
            [Paragraph("Total expenses", metric_label), Paragraph("Transactions", metric_label),
             Paragraph("Average expense", metric_label), Paragraph("Vs previous period", metric_label)],
            [Paragraph(money(report.total_expenses), metric_value), Paragraph(str(report.transaction_count), metric_value),
             Paragraph(money(report.average_expense), metric_value), Paragraph(t(change_text), metric_value)],
        ],
        colWidths=[doc_width / 4] * 4,
    )
    metrics.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(metrics)

    # Summary
    story.append(Paragraph("Summary", h2))
    story.append(Paragraph(t(report.summary), body))
    if report.ai_summary:
        story.append(Paragraph("AI-written summary", h2))
        story.append(Paragraph(t(report.ai_summary), body))
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "Written by an AI model from the aggregate figures in this report; it may contain errors.", small))

    # Category breakdown
    section = [Paragraph("Category breakdown", h2)]
    if report.category_breakdown:
        rows = [[Paragraph("Category", head), Paragraph("Amount", head_r),
                 Paragraph("Share", head_r), Paragraph("Transactions", head_r)]]
        for c in report.category_breakdown:
            rows.append([Paragraph(t(c.category), cell), Paragraph(money(c.total), cell_r),
                         Paragraph(f"{c.percentage}%", cell_r), Paragraph(str(c.transaction_count), cell_r)])
        section.append(data_table(rows, [doc_width * 0.4, doc_width * 0.25, doc_width * 0.15, doc_width * 0.2]))
    else:
        section.append(Paragraph("No expenses in this period.", body))
    story.append(KeepTogether(section))

    # Comparison (heading and table kept on one page)
    sign = "+" if cmp.change_amount > 0 else "-" if cmp.change_amount < 0 else ""
    change_amt = f"{sign}₹{abs(cmp.change_amount):,.2f}"
    rows = [
        [Paragraph("Period", head), Paragraph("Total", head_r)],
        [Paragraph(t(report.period_label + " (this report)"), cell), Paragraph(money(cmp.current_total), cell_r)],
        [Paragraph(t(cmp.previous_period_label), cell), Paragraph(money(cmp.previous_total), cell_r)],
        [Paragraph("Change", cell),
         Paragraph(t(f"{change_amt} ({change_text})"), cell_r)],
    ]
    story.append(KeepTogether([Paragraph("Comparison with previous period", h2),
                               data_table(rows, [doc_width * 0.6, doc_width * 0.4])]))

    # Top expenses
    section = [Paragraph("Top expenses", h2)]
    if report.top_expenses:
        rows = [[Paragraph("Date", head), Paragraph("Merchant", head),
                 Paragraph("Category", head), Paragraph("Amount", head_r)]]
        for e in report.top_expenses:
            rows.append([Paragraph(t(e.expense_date.strftime("%d %b %Y")), cell), Paragraph(t(e.merchant), cell),
                         Paragraph(t(e.category), cell), Paragraph(money(e.amount), cell_r)])
        section.append(data_table(rows, [doc_width * 0.18, doc_width * 0.38, doc_width * 0.24, doc_width * 0.2]))
    else:
        section.append(Paragraph("No expenses in this period.", body))
    story.append(KeepTogether(section))

    story.append(Spacer(1, 16))
    story.append(Paragraph(t(report.disclaimer), small))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(regular, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 10 * mm, "Smart Expense Manager")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Expense Report - {report.period_label}", author="Smart Expense Manager",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
