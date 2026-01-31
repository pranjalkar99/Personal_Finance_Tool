"""Recurring expense API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.recurring import (
    RecurringExpenseCreate, RecurringExpenseUpdate, RecurringExpenseResponse,
    RecurringExpenseListResponse, ProcessedRecurringResult
)
from app.services.recurring_service import RecurringExpenseService
from app.core.dependencies import CurrentUser

router = APIRouter(prefix="/recurring", tags=["recurring"])


@router.post(
    "",
    response_model=RecurringExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create recurring expense"
)
def create_recurring(
    data: RecurringExpenseCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> RecurringExpenseResponse:
    """Create a new recurring expense template."""
    service = RecurringExpenseService(db)
    return service.create(current_user, data)


@router.get(
    "",
    response_model=RecurringExpenseListResponse,
    summary="List recurring expenses"
)
def list_recurring(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> RecurringExpenseListResponse:
    """List all recurring expenses for the authenticated user."""
    service = RecurringExpenseService(db)
    return service.list_recurring(current_user.id)


@router.post(
    "/process",
    response_model=ProcessedRecurringResult,
    summary="Process due recurring expenses"
)
def process_recurring(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> ProcessedRecurringResult:
    """Process all due recurring expenses and create actual expense entries."""
    service = RecurringExpenseService(db)
    return service.process_due_recurring(current_user.id)


@router.get(
    "/{recurring_id}",
    response_model=RecurringExpenseResponse,
    summary="Get recurring expense"
)
def get_recurring(
    recurring_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> RecurringExpenseResponse:
    """Get a specific recurring expense."""
    service = RecurringExpenseService(db)
    recurring = service.get_by_id(recurring_id, current_user.id)
    
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring expense with id {recurring_id} not found"
        )
    
    return recurring


@router.patch(
    "/{recurring_id}",
    response_model=RecurringExpenseResponse,
    summary="Update recurring expense"
)
def update_recurring(
    recurring_id: int,
    data: RecurringExpenseUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> RecurringExpenseResponse:
    """Update a recurring expense."""
    service = RecurringExpenseService(db)
    recurring = service.get_by_id(recurring_id, current_user.id)
    
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring expense with id {recurring_id} not found"
        )
    
    return service.update(recurring, data)


@router.post(
    "/{recurring_id}/toggle",
    response_model=RecurringExpenseResponse,
    summary="Toggle recurring expense active status"
)
def toggle_recurring(
    recurring_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> RecurringExpenseResponse:
    """Toggle active/inactive status of a recurring expense."""
    service = RecurringExpenseService(db)
    recurring = service.get_by_id(recurring_id, current_user.id)
    
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring expense with id {recurring_id} not found"
        )
    
    return service.toggle_active(recurring)


@router.delete(
    "/{recurring_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete recurring expense"
)
def delete_recurring(
    recurring_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> None:
    """Delete a recurring expense."""
    service = RecurringExpenseService(db)
    recurring = service.get_by_id(recurring_id, current_user.id)
    
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recurring expense with id {recurring_id} not found"
        )
    
    service.delete(recurring)

