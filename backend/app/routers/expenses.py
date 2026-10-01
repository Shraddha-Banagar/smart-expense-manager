"""
Expense CRUD endpoints. Every route requires authentication and every
query/mutation is scoped to the current user (see app.dependencies.get_current_user).
"""
import math
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, PaginatedExpenses
from app.services.expense_service import (
    create_expense,
    get_expense,
    list_expenses,
    update_expense,
    delete_expense,
    ExpenseNotFoundError,
)

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.get("", response_model=PaginatedExpenses)
def get_expenses(
    search: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = Query(default="expense_date", pattern="^(amount|expense_date|created_at|merchant)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = list_expenses(
        db,
        user_id=current_user.id,
        search=search,
        category=category,
        payment_method=payment_method,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total else 0
    return PaginatedExpenses(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def add_expense(
    expense_in: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_expense(db, user_id=current_user.id, expense_in=expense_in)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_single_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_expense(db, user_id=current_user.id, expense_id=expense_id)
    except ExpenseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")


@router.put("/{expense_id}", response_model=ExpenseResponse)
def edit_expense(
    expense_id: int,
    expense_in: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_expense(db, user_id=current_user.id, expense_id=expense_id, expense_in=expense_in)
    except ExpenseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        delete_expense(db, user_id=current_user.id, expense_id=expense_id)
    except ExpenseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
