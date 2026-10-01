"""
AI endpoints:
- /extract-expense: turns a document's OCR text into a structured
  suggestion the frontend pre-fills into the expense form (Phase 6).
- /insights: rule-based spending insights computed from real data —
  see app.services.insights_service for why this deliberately isn't
  LLM-generated.
- /ask: the natural-language expense Q&A assistant, scoped strictly to
  the user's own financial data — see app.services.ask_service.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import ExtractExpenseRequest, ExpenseExtractionResult, AskQuestionRequest, AskQuestionResponse
from app.schemas.insights import InsightsResponse
from app.services import ai_service, ask_service, insights_service
from app.services.document_service import get_document, DocumentNotFoundError

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/extract-expense", response_model=ExpenseExtractionResult)
def extract_expense(
    request: ExtractExpenseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        document = get_document(db, user_id=current_user.id, document_id=request.document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if document.processing_status != "completed" or not document.ocr_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This document has no extracted text to analyze yet.",
        )

    try:
        return ai_service.extract_expense(document.ocr_text)
    except ai_service.AIConfigError as e:
        # Distinct from "the AI got it wrong" (handled inside extract_expense
        # itself, returning a low-confidence result) — this is "the AI isn't
        # configured at all", which should surface clearly rather than as an
        # unhandled 500 with a stack trace.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI extraction is not available: {e}",
        )


@router.post("/insights", response_model=InsightsResponse)
def get_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # No AI provider needed — see insights_service for why these are
    # computed deterministically rather than LLM-generated. Always
    # available, even with no LLM_PROVIDER/API key configured.
    return insights_service.generate_insights(db, user_id=current_user.id)


@router.post("/ask", response_model=AskQuestionResponse)
def ask(
    request: AskQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = [turn.model_dump() for turn in request.history]
    try:
        answer = ask_service.ask_question(db, user_id=current_user.id, question=request.question, history=history)
    except ai_service.AIConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"The assistant is not available: {e}",
        )
    return AskQuestionResponse(answer=answer, disclaimer=ask_service.DISCLAIMER)
