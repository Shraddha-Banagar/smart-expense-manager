from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExpenseBase(BaseModel):
    merchant: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    expense_date: date
    payment_method: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("amount")
    @classmethod
    def round_amount(cls, v: float) -> float:
        return round(v, 2)


class ExpenseCreate(ExpenseBase):
    document_id: Optional[int] = None


class ExpenseUpdate(BaseModel):
    merchant: Optional[str] = Field(default=None, min_length=1, max_length=255)
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    expense_date: Optional[date] = None
    payment_method: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=2000)


class ExpenseResponse(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    document_id: Optional[int] = None
    created_at: datetime


class PaginatedExpenses(BaseModel):
    items: list[ExpenseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
