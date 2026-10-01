"""
Analytics computed from the user's own expenses. Aggregation is done in
Python (not SQL date-trunc) so behavior is identical across SQLite (tests)
and PostgreSQL (dev/prod).
"""
from calendar import month_abbr, monthrange
from datetime import date
from collections import defaultdict
from typing import Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.schemas.analytics import SummaryResponse, CategoryBreakdownItem, MonthlyTrendItem

VALID_RANGES = {
    "this_week",
    "this_month",
    "last_month",
    "last_3_months",
    "this_year",
    "custom",
    "all_time",
}


def resolve_date_range(
    range_key: str,
    custom_from: Optional[date] = None,
    custom_to: Optional[date] = None,
    today: Optional[date] = None,
) -> tuple[Optional[date], Optional[date]]:
    """
    Turns a named range (or "custom" + explicit dates) into a concrete
    (date_from, date_to) tuple. Returns (None, None) for "all_time",
    meaning no filtering.
    """
    today = today or date.today()

    if range_key == "custom":
        return custom_from, custom_to

    if range_key == "this_week":
        start = today - relativedelta(days=today.weekday())  # Monday
        return start, today

    if range_key == "this_month":
        return today.replace(day=1), today

    if range_key == "last_month":
        last_month_end = today.replace(day=1) - relativedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return last_month_start, last_month_end

    if range_key == "last_3_months":
        start = (today.replace(day=1) - relativedelta(months=2))
        return start, today

    if range_key == "this_year":
        return today.replace(month=1, day=1), today

    # "all_time" or unrecognized -> no filtering
    return None, None


def _get_expenses(
    db: Session,
    user_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[Expense]:
    query = db.query(Expense).filter(Expense.user_id == user_id)
    if date_from:
        query = query.filter(Expense.expense_date >= date_from)
    if date_to:
        query = query.filter(Expense.expense_date <= date_to)
    return query.all()


def get_summary(
    db: Session,
    user_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> SummaryResponse:
    expenses = _get_expenses(db, user_id, date_from, date_to)

    total_expenses = sum(e.amount for e in expenses)
    transaction_count = len(expenses)
    average_expense = round(total_expenses / transaction_count, 2) if transaction_count else 0.0
    highest_transaction = round(max((e.amount for e in expenses), default=0.0), 2)

    today = date.today()
    # "This month" is always calendar-current-month, independent of any
    # date_from/date_to filter applied to the rest of the summary — it's a
    # fixed reference point the dashboard always shows.
    all_expenses = _get_expenses(db, user_id)
    this_month_total = sum(
        e.amount for e in all_expenses
        if e.expense_date.year == today.year and e.expense_date.month == today.month
    )
    last_month_date = today.replace(day=1) - relativedelta(days=1)
    last_month_total = sum(
        e.amount for e in all_expenses
        if e.expense_date.year == last_month_date.year and e.expense_date.month == last_month_date.month
    )

    if last_month_total > 0:
        month_over_month_change = round(((this_month_total - last_month_total) / last_month_total) * 100, 1)
    else:
        month_over_month_change = None

    return SummaryResponse(
        total_expenses=round(total_expenses, 2),
        this_month_total=round(this_month_total, 2),
        transaction_count=transaction_count,
        average_expense=average_expense,
        highest_transaction=highest_transaction,
        month_over_month_change=month_over_month_change,
    )


def category_breakdown_from_expenses(expenses: list[Expense]) -> list[CategoryBreakdownItem]:
    """Pure aggregation over an already-fetched list of expenses (reused by reports,
    which filter the list themselves before aggregating)."""
    total = sum(e.amount for e in expenses)

    totals_by_category: dict[str, float] = defaultdict(float)
    counts_by_category: dict[str, int] = defaultdict(int)
    for e in expenses:
        totals_by_category[e.category] += e.amount
        counts_by_category[e.category] += 1

    items = [
        CategoryBreakdownItem(
            category=category,
            total=round(amount, 2),
            percentage=round((amount / total) * 100, 1) if total else 0.0,
            transaction_count=counts_by_category[category],
        )
        for category, amount in totals_by_category.items()
    ]
    items.sort(key=lambda i: i.total, reverse=True)
    return items


def get_category_breakdown(
    db: Session,
    user_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[CategoryBreakdownItem]:
    return category_breakdown_from_expenses(_get_expenses(db, user_id, date_from, date_to))


def get_monthly_trend(db: Session, user_id: int, months: int = 6) -> list[MonthlyTrendItem]:
    expenses = _get_expenses(db, user_id)

    totals_by_month: dict[str, float] = defaultdict(float)
    for e in expenses:
        key = e.expense_date.strftime("%Y-%m")
        totals_by_month[key] += e.amount

    today = date.today().replace(day=1)
    result = []
    for i in range(months - 1, -1, -1):
        month_date = today - relativedelta(months=i)
        key = month_date.strftime("%Y-%m")
        label = f"{month_abbr[month_date.month]} {month_date.year}"
        result.append(MonthlyTrendItem(month=label, total=round(totals_by_month.get(key, 0.0), 2)))

    return result


def get_current_month_spend_by_category(db: Session, user_id: int) -> dict[str, float]:
    """Used by budget_service to compute how much of each budget is used so far this month."""
    today = date.today()
    month_start = today.replace(day=1)
    expenses = _get_expenses(db, user_id, date_from=month_start, date_to=today)

    totals: dict[str, float] = defaultdict(float)
    for e in expenses:
        totals[e.category] += e.amount
    return totals
