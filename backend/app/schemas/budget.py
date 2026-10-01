from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    monthly_limit: float = Field(..., gt=0)


class BudgetUpdate(BaseModel):
    monthly_limit: Optional[float] = Field(default=None, gt=0)


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    category: str
    monthly_limit: float
    created_at: datetime

    # Computed for the current month — not stored, derived at read time
    # from the user's expenses so it's always up to date.
    spent_amount: float = 0.0
    remaining_amount: float = 0.0
    percentage_used: float = 0.0
    status: str = "on_track"  # "on_track" | "approaching" | "exceeded"
