"""
Report endpoints. Both require authentication and only ever read the
current user's expenses.

  GET /api/reports/monthly       -> the report as JSON (viewed in the browser)
  GET /api/reports/monthly/pdf   -> the same report rendered as a PDF download

Period selection: `month=YYYY-MM` (default: current month) OR a custom
`date_from` + `date_to`. `category` optionally restricts the whole report to
one category. `ai_summary=true` additionally asks the configured LLM for a
narrative summary (it degrades to "unavailable" instead of failing).
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import ReportResponse
from app.services.report_pdf import build_pdf
from app.services.report_service import ReportParamError, build_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _report_or_400(db, user, month, date_from, date_to, category, ai_summary) -> ReportResponse:
    try:
        return build_report(
            db, user_id=user.id, month=month, date_from=date_from, date_to=date_to,
            category=category, ai_summary=ai_summary,
        )
    except ReportParamError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/monthly", response_model=ReportResponse)
def monthly_report(
    month: Optional[str] = Query(default=None, description="YYYY-MM; defaults to the current month"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = Query(default=None, max_length=100),
    ai_summary: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _report_or_400(db, current_user, month, date_from, date_to, category, ai_summary)


@router.get("/monthly/pdf")
def monthly_report_pdf(
    month: Optional[str] = Query(default=None, description="YYYY-MM; defaults to the current month"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = Query(default=None, max_length=100),
    ai_summary: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = _report_or_400(db, current_user, month, date_from, date_to, category, ai_summary)
    filename = f"expense-report-{report.period_start.isoformat()}_{report.period_end.isoformat()}.pdf"
    return Response(
        content=build_pdf(report),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
