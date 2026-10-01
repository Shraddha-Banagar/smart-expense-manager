"""
Business logic for expense CRUD, including search/filter/sort/pagination.
All queries are scoped to the requesting user so no one can read or modify
another user's expenses.
"""
from datetime import date
from typing import Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate

SORTABLE_FIELDS = {
    "amount": Expense.amount,
    "expense_date": Expense.expense_date,
    "created_at": Expense.created_at,
    "merchant": Expense.merchant,
}


class ExpenseNotFoundError(Exception):
    """Raised when an expense doesn't exist or doesn't belong to the user."""


def create_expense(db: Session, user_id: int, expense_in: ExpenseCreate) -> Expense:
    expense = Expense(user_id=user_id, **expense_in.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def get_expense(db: Session, user_id: int, expense_id: int) -> Expense:
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.user_id == user_id)
        .first()
    )
    if not expense:
        raise ExpenseNotFoundError("Expense not found.")
    return expense


def list_expenses(
    db: Session,
    user_id: int,
    search: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = "expense_date",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Expense], int]:
    query = db.query(Expense).filter(Expense.user_id == user_id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            Expense.merchant.ilike(like) | Expense.description.ilike(like)
        )
    if category:
        query = query.filter(Expense.category == category)
    if payment_method:
        query = query.filter(Expense.payment_method == payment_method)
    if date_from:
        query = query.filter(Expense.expense_date >= date_from)
    if date_to:
        query = query.filter(Expense.expense_date <= date_to)

    total = query.count()

    sort_column = SORTABLE_FIELDS.get(sort_by, Expense.expense_date)
    order_fn = asc if sort_order == "asc" else desc
    query = query.order_by(order_fn(sort_column))

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return items, total


def update_expense(db: Session, user_id: int, expense_id: int, expense_in: ExpenseUpdate) -> Expense:
    expense = get_expense(db, user_id, expense_id)
    update_data = expense_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, user_id: int, expense_id: int) -> None:
    expense = get_expense(db, user_id, expense_id)
    db.delete(expense)
    db.commit()
