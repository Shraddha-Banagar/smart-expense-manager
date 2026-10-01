"""
Expense reports: a period (a calendar month, or a custom date range),
optionally filtered to one category, summarised as totals, a category
breakdown, a comparison against the preceding period, and top expenses.

Summary text follows the same principle as the Insights feature:
  * `summary` is ASSEMBLED FROM THE COMPUTED FIGURES (deterministic, always
    present, cannot state a number that isn't in the report).
  * `ai_summary` is an OPTIONAL LLM-written narrative, generated only when the
    caller asks for it. It is fed aggregate figures only — never merchant
    names or descriptions — and it degrades to "unavailable" (never an
    error) if no provider is configured or the call fails, because the
    report is fully usable without it.
"""
import calendar
import logging
import re
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.schemas.report import ReportComparison, ReportResponse, TopExpenseItem
from app.services import ai_service
from app.services.analytics_service import _get_expenses, category_breakdown_from_expenses

logger = logging.getLogger("expense_manager")

DISCLAIMER = (
    "This report is generated from your logged expenses for informational "
    "purposes only. It is not financial advice."
)
TOP_EXPENSES_LIMIT = 5
_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")


class ReportParamError(ValueError):
    """Raised for invalid report parameters (bad month, incomplete/reversed range)."""


def _money(amount: float) -> str:
    return f"₹{amount:,.2f}"


def _fmt_date(d: date) -> str:
    return f"{d.day} {calendar.month_abbr[d.month]} {d.year}"


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def _range_label(start: date, end: date) -> str:
    return f"{_fmt_date(start)} – {_fmt_date(end)}"


def resolve_period(
    month: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    today: Optional[date] = None,
) -> tuple[date, date, str, date, date, str]:
    """
    Returns (start, end, label, prev_start, prev_end, prev_label).

    - Custom range (date_from + date_to): compared against the immediately
      preceding period of the same length.
    - Otherwise a calendar month ("YYYY-MM", default current month):
      compared against the previous calendar month.
    """
    today = today or date.today()

    if date_from is not None or date_to is not None:
        if date_from is None or date_to is None:
            raise ReportParamError("Both date_from and date_to are required for a custom range.")
        if date_from > date_to:
            raise ReportParamError("date_from must be on or before date_to.")
        length = (date_to - date_from).days + 1
        prev_end = date_from - timedelta(days=1)
        prev_start = prev_end - timedelta(days=length - 1)
        return (
            date_from, date_to, _range_label(date_from, date_to),
            prev_start, prev_end, _range_label(prev_start, prev_end),
        )

    if month is None:
        year, mon = today.year, today.month
    else:
        match = _MONTH_RE.match(month)
        if not match:
            raise ReportParamError("month must be in YYYY-MM format.")
        year, mon = int(match.group(1)), int(match.group(2))
        if not 1 <= mon <= 12 or year < 1900:
            raise ReportParamError("month must be a valid month in YYYY-MM format.")

    start, end = _month_bounds(year, mon)
    prev_year, prev_mon = (year, mon - 1) if mon > 1 else (year - 1, 12)
    prev_start, prev_end = _month_bounds(prev_year, prev_mon)
    return (
        start, end, f"{calendar.month_name[mon]} {year}",
        prev_start, prev_end, f"{calendar.month_name[prev_mon]} {prev_year}",
    )


def _fetch(db: Session, user_id: int, start: date, end: date, category: Optional[str]) -> list[Expense]:
    expenses = _get_expenses(db, user_id, date_from=start, date_to=end)
    if category:
        expenses = [e for e in expenses if e.category == category]
    return expenses


def _build_summary(report: ReportResponse) -> str:
    scope = f" in {report.category_filter}" if report.category_filter else ""
    if report.transaction_count == 0:
        return f"No expenses were recorded{scope} for {report.period_label}."

    noun = "expense" if report.transaction_count == 1 else "expenses"
    parts = [
        f"For {report.period_label}, you recorded {report.transaction_count} {noun}{scope} "
        f"totalling {_money(report.total_expenses)}, averaging {_money(report.average_expense)} each."
    ]

    if not report.category_filter and report.category_breakdown:
        top = report.category_breakdown[0]
        parts.append(f"{top.category} was your largest category at {_money(top.total)} ({top.percentage}% of the total).")

    cmp = report.comparison
    if cmp.previous_total > 0 and cmp.change_percent is not None:
        if cmp.change_percent > 0:
            parts.append(f"Spending was {cmp.change_percent}% higher than {cmp.previous_period_label} ({_money(cmp.previous_total)}).")
        elif cmp.change_percent < 0:
            parts.append(f"Spending was {abs(cmp.change_percent)}% lower than {cmp.previous_period_label} ({_money(cmp.previous_total)}).")
        else:
            parts.append(f"Spending was unchanged from {cmp.previous_period_label} ({_money(cmp.previous_total)}).")
    else:
        parts.append(f"There were no recorded expenses in {cmp.previous_period_label} to compare against.")

    if report.top_expenses:
        big = report.top_expenses[0]
        parts.append(f"Your largest single expense was {_money(big.amount)} at {big.merchant}.")

    return " ".join(parts)


def _generate_ai_summary(report: ReportResponse) -> tuple[Optional[str], str]:
    """Returns (text_or_None, status). Never raises."""
    if report.transaction_count == 0:
        return None, "unavailable"

    # Aggregate figures ONLY — no merchant names, descriptions, or per-transaction rows.
    facts = {
        "period": report.period_label,
        "category_filter": report.category_filter,
        "total_expenses": report.total_expenses,
        "transaction_count": report.transaction_count,
        "average_expense": report.average_expense,
        "category_breakdown": [
            {"category": c.category, "total": c.total, "percentage": c.percentage}
            for c in report.category_breakdown
        ],
        "previous_period": report.comparison.previous_period_label,
        "previous_period_total": report.comparison.previous_total,
        "change_percent_vs_previous": report.comparison.change_percent,
    }
    prompt = f"""You are writing the short narrative summary section of a personal expense report.

Write 3 to 4 plain sentences describing the spending in the data below. Use ONLY the figures provided — do not invent, estimate, or infer any number, merchant, or transaction that is not in the data. Do not give financial advice or recommendations. No headings, no bullet points, no markdown.

Report data (JSON):
{facts}

Summary:"""

    try:
        text = ai_service._call_llm(prompt).strip()
    except ai_service.AIConfigError:
        return None, "unavailable"
    except Exception:
        logger.exception("LLM call failed while generating report summary.")
        return None, "unavailable"

    if not text:
        return None, "unavailable"
    return text[:1500], "generated"


def build_report(
    db: Session,
    user_id: int,
    month: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = None,
    ai_summary: bool = False,
) -> ReportResponse:
    start, end, label, prev_start, prev_end, prev_label = resolve_period(month, date_from, date_to)

    current = _fetch(db, user_id, start, end, category)
    previous = _fetch(db, user_id, prev_start, prev_end, category)

    total = round(sum(e.amount for e in current), 2)
    prev_total = round(sum(e.amount for e in previous), 2)
    count = len(current)
    change_amount = round(total - prev_total, 2)
    change_percent = round((change_amount / prev_total) * 100, 1) if prev_total > 0 else None

    top = sorted(current, key=lambda e: (e.amount, e.expense_date), reverse=True)[:TOP_EXPENSES_LIMIT]

    report = ReportResponse(
        period_start=start,
        period_end=end,
        period_label=label,
        category_filter=category or None,
        total_expenses=total,
        transaction_count=count,
        average_expense=round(total / count, 2) if count else 0.0,
        category_breakdown=category_breakdown_from_expenses(current),
        comparison=ReportComparison(
            previous_period_label=prev_label,
            previous_total=prev_total,
            current_total=total,
            change_amount=change_amount,
            change_percent=change_percent,
        ),
        top_expenses=[
            TopExpenseItem(
                id=e.id, merchant=e.merchant, amount=e.amount,
                category=e.category, expense_date=e.expense_date,
            )
            for e in top
        ],
        summary="",
        disclaimer=DISCLAIMER,
    )
    report.summary = _build_summary(report)

    if ai_summary:
        report.ai_summary, report.ai_summary_status = _generate_ai_summary(report)

    return report
