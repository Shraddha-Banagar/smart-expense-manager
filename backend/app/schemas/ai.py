from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ExtractExpenseRequest(BaseModel):
    document_id: int


class ExpenseExtractionResult(BaseModel):
    """
    The AI's best-effort reading of a receipt. Never saved directly —
    the frontend shows this to the user for review/correction before it
    becomes a real expense (see important_requirement in the spec).
    """
    merchant: Optional[str] = None
    amount: Optional[float] = None
    expense_date: Optional[date] = None
    category: str = "Other"
    payment_method: str = "Other"
    description: Optional[str] = None
    confidence: float = 0.0


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=2000)


class AskQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    # Prior turns in this conversation, for follow-up questions. Not
    # persisted server-side — the frontend keeps and resends it.
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class AskQuestionResponse(BaseModel):
    answer: str
    disclaimer: str
