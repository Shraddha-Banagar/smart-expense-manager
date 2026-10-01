from datetime import date
from typing import Optional

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_expenses: float
    this_month_total: float
    transaction_count: int
    average_expense: float
    highest_transaction: float
    month_over_month_change: Optional[float] = None  # percent change, None if no prior-month data


class CategoryBreakdownItem(BaseModel):
    category: str
    total: float
    percentage: float
    transaction_count: int


class MonthlyTrendItem(BaseModel):
    month: str  # "YYYY-MM"
    total: float


class DateRangeInfo(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
