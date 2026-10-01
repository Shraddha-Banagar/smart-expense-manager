"""
Budget CRUD endpoints. One budget per (user, category); spend/remaining/
percentage/status are always computed live from the current month's
expenses, never stored, so they can't go stale.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.services.budget_service import (
    create_budget,
    list_budgets,
    update_budget,
    delete_budget,
    BudgetAlreadyExistsError,
    BudgetNotFoundError,
)

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetResponse])
def get_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_budgets(db, user_id=current_user.id)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def add_budget(
    budget_in: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return create_budget(db, user_id=current_user.id, budget_in=budget_in)
    except BudgetAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{budget_id}", response_model=BudgetResponse)
def edit_budget(
    budget_id: int,
    budget_in: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_budget(db, user_id=current_user.id, budget_id=budget_id, budget_in=budget_in)
    except BudgetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        delete_budget(db, user_id=current_user.id, budget_id=budget_id)
    except BudgetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
