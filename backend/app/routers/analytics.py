"""
Analytics endpoints powering the Dashboard and Analytics pages.
All results are scoped to the authenticated user.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.analytics import SummaryResponse, CategoryBreakdownItem, MonthlyTrendItem
from app.services.analytics_service import (
    get_summary,
    get_category_breakdown,
    get_monthly_trend,
    resolve_date_range,
    VALID_RANGES,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _resolve_range_or_400(range_: str, date_from: Optional[date], date_to: Optional[date]):
    if range_ not in VALID_RANGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid range '{range_}'. Valid options: {', '.join(sorted(VALID_RANGES))}.",
        )
    if range_ == "custom" and not (date_from and date_to):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from and date_to are required when range=custom.",
        )
    return resolve_date_range(range_, date_from, date_to)


@router.get("/summary", response_model=SummaryResponse)
def summary(
    range: str = Query(default="all_time"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resolved_from, resolved_to = _resolve_range_or_400(range, date_from, date_to)
    return get_summary(db, user_id=current_user.id, date_from=resolved_from, date_to=resolved_to)


@router.get("/categories", response_model=list[CategoryBreakdownItem])
def categories(
    range: str = Query(default="all_time"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resolved_from, resolved_to = _resolve_range_or_400(range, date_from, date_to)
    return get_category_breakdown(db, user_id=current_user.id, date_from=resolved_from, date_to=resolved_to)


@router.get("/monthly", response_model=list[MonthlyTrendItem])
def monthly(
    months: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_monthly_trend(db, user_id=current_user.id, months=months)
