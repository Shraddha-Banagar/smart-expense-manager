from datetime import date
from typing import Optional

from pydantic import BaseModel

from app.schemas.analytics import CategoryBreakdownItem


class TopExpenseItem(BaseModel):
    id: int
    merchant: str
    amount: float
    category: str
    expense_date: date


class ReportComparison(BaseModel):
    previous_period_label: str
    previous_total: float
    current_total: float
    change_amount: float
    # None when the previous period had no spending (percent change undefined).
    change_percent: Optional[float] = None


class ReportResponse(BaseModel):
    period_start: date
    period_end: date
    period_label: str
    category_filter: Optional[str] = None

    total_expenses: float
    transaction_count: int
    average_expense: float

    category_breakdown: list[CategoryBreakdownItem]
    comparison: ReportComparison
    top_expenses: list[TopExpenseItem]

    # Deterministic, always present: assembled from the computed figures above.
    summary: str
    # Optional LLM-written narrative, only when requested (see report_service).
    ai_summary: Optional[str] = None
    ai_summary_status: str = "not_requested"  # "not_requested" | "generated" | "unavailable"

    disclaimer: str
