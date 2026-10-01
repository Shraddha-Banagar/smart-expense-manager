"""
Business logic for budgets: one budget per (user, category), with spend
computed live from the current month's expenses rather than stored —
that way it's never stale.
"""
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.services.analytics_service import get_current_month_spend_by_category

APPROACHING_THRESHOLD = 0.8  # 80% of budget


class BudgetAlreadyExistsError(Exception):
    """Raised when the user already has a budget for this category."""


class BudgetNotFoundError(Exception):
    """Raised when a budget doesn't exist or doesn't belong to the user."""


def _to_response(budget: Budget, spend_by_category: dict[str, float]) -> BudgetResponse:
    spent = round(spend_by_category.get(budget.category, 0.0), 2)
    remaining = round(budget.monthly_limit - spent, 2)
    percentage_used = round((spent / budget.monthly_limit) * 100, 1) if budget.monthly_limit else 0.0

    if spent >= budget.monthly_limit:
        status = "exceeded"
    elif percentage_used >= APPROACHING_THRESHOLD * 100:
        status = "approaching"
    else:
        status = "on_track"

    return BudgetResponse(
        id=budget.id,
        user_id=budget.user_id,
        category=budget.category,
        monthly_limit=budget.monthly_limit,
        created_at=budget.created_at,
        spent_amount=spent,
        remaining_amount=remaining,
        percentage_used=percentage_used,
        status=status,
    )


def create_budget(db: Session, user_id: int, budget_in: BudgetCreate) -> BudgetResponse:
    existing = (
        db.query(Budget)
        .filter(Budget.user_id == user_id, Budget.category == budget_in.category)
        .first()
    )
    if existing:
        raise BudgetAlreadyExistsError(
            f"A budget for '{budget_in.category}' already exists. Update it instead."
        )

    budget = Budget(user_id=user_id, category=budget_in.category, monthly_limit=budget_in.monthly_limit)
    db.add(budget)
    db.commit()
    db.refresh(budget)

    spend_by_category = get_current_month_spend_by_category(db, user_id)
    return _to_response(budget, spend_by_category)


def list_budgets(db: Session, user_id: int) -> list[BudgetResponse]:
    budgets = db.query(Budget).filter(Budget.user_id == user_id).order_by(Budget.category).all()
    spend_by_category = get_current_month_spend_by_category(db, user_id)
    return [_to_response(b, spend_by_category) for b in budgets]


def _get_budget_or_raise(db: Session, user_id: int, budget_id: int) -> Budget:
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()
    if not budget:
        raise BudgetNotFoundError("Budget not found.")
    return budget


def update_budget(db: Session, user_id: int, budget_id: int, budget_in: BudgetUpdate) -> BudgetResponse:
    budget = _get_budget_or_raise(db, user_id, budget_id)
    if budget_in.monthly_limit is not None:
        budget.monthly_limit = budget_in.monthly_limit
    db.commit()
    db.refresh(budget)

    spend_by_category = get_current_month_spend_by_category(db, user_id)
    return _to_response(budget, spend_by_category)


def delete_budget(db: Session, user_id: int, budget_id: int) -> None:
    budget = _get_budget_or_raise(db, user_id, budget_id)
    db.delete(budget)
    db.commit()
