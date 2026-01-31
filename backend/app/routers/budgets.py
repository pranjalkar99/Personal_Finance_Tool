"""Budget API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetResponse,
    BudgetStatus, BudgetOverview
)
from app.services.budget_service import BudgetService
from app.core.dependencies import CurrentUser

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post(
    "",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a budget"
)
def create_budget(
    budget_data: BudgetCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> BudgetResponse:
    """Create a new budget or update existing one for the category."""
    budget_service = BudgetService(db)
    budget = budget_service.create(current_user, budget_data)
    return budget


@router.get(
    "",
    response_model=List[BudgetResponse],
    summary="List all budgets"
)
def list_budgets(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> List[BudgetResponse]:
    """List all budgets for the authenticated user."""
    budget_service = BudgetService(db)
    return budget_service.list_budgets(current_user.id)


@router.get(
    "/overview",
    response_model=BudgetOverview,
    summary="Get budget overview with alerts"
)
def get_budget_overview(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> BudgetOverview:
    """Get overview of all budgets with current status and alerts."""
    budget_service = BudgetService(db)
    return budget_service.get_budget_overview(current_user.id)


@router.get(
    "/{budget_id}",
    response_model=BudgetStatus,
    summary="Get budget status"
)
def get_budget_status(
    budget_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> BudgetStatus:
    """Get status of a specific budget including current spending."""
    budget_service = BudgetService(db)
    budget = budget_service.get_by_id(budget_id, current_user.id)
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with id {budget_id} not found"
        )
    
    return budget_service.get_budget_status(budget)


@router.patch(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Update budget"
)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> BudgetResponse:
    """Update an existing budget."""
    budget_service = BudgetService(db)
    budget = budget_service.get_by_id(budget_id, current_user.id)
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with id {budget_id} not found"
        )
    
    return budget_service.update(budget, budget_data)


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete budget"
)
def delete_budget(
    budget_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> None:
    """Delete a budget."""
    budget_service = BudgetService(db)
    budget = budget_service.get_by_id(budget_id, current_user.id)
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget with id {budget_id} not found"
        )
    
    budget_service.delete(budget)

