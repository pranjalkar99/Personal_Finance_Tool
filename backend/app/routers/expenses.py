"""Expense API routes."""

import csv
import io
from datetime import date
from decimal import Decimal
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.expense import (
    ExpenseCreate, 
    ExpenseUpdate, 
    ExpenseResponse, 
    ExpenseListResponse,
    ExpenseFilters,
    ExpenseSummary,
    AnalyticsResponse
)
from app.services.expense_service import ExpenseService
from app.core.dependencies import CurrentUser

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense"
)
def create_expense(
    expense_data: ExpenseCreate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> ExpenseResponse:
    """
    Create a new expense for the authenticated user.
    
    Supports idempotency via `idempotency_key` - if a request is retried with
    the same key, the existing expense is returned instead of creating a duplicate.
    """
    expense_service = ExpenseService(db)
    expense = expense_service.create(current_user, expense_data)
    return expense


@router.get(
    "",
    response_model=ExpenseListResponse,
    summary="List expenses"
)
def list_expenses(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date"),
    min_amount: Optional[Decimal] = Query(None, description="Minimum amount"),
    max_amount: Optional[Decimal] = Query(None, description="Maximum amount"),
    search: Optional[str] = Query(None, description="Search in description"),
    sort: Optional[Literal["date_desc", "date_asc", "amount_desc", "amount_asc"]] = Query(
        None, description="Sort order"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
) -> ExpenseListResponse:
    """
    List expenses for the authenticated user with filtering, sorting, and pagination.
    """
    filters = ExpenseFilters(
        category=category,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        sort=sort,
        page=page,
        page_size=page_size
    )
    
    expense_service = ExpenseService(db)
    expenses, total_count, total_amount = expense_service.list_expenses(
        current_user.id, filters
    )
    
    total_pages = (total_count + page_size - 1) // page_size
    
    return ExpenseListResponse(
        expenses=expenses,
        total=total_amount,
        count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/summary",
    response_model=ExpenseSummary,
    summary="Get expense summary"
)
def get_expense_summary(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None, description="Filter by year")
) -> ExpenseSummary:
    """Get expense summary and analytics for the authenticated user."""
    expense_service = ExpenseService(db)
    return expense_service.get_summary(current_user.id, year)


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Get comprehensive expense analytics"
)
def get_analytics(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    months: int = Query(12, ge=1, le=36, description="Number of months to analyze")
) -> AnalyticsResponse:
    """
    Get comprehensive expense analytics including:
    - Category breakdown with percentages
    - Monthly spending trends
    - Daily spending (last 30 days)
    - Month over month comparison
    """
    expense_service = ExpenseService(db)
    return expense_service.get_analytics(current_user.id, months)


@router.get(
    "/categories",
    response_model=list[str],
    summary="Get expense categories"
)
def get_categories(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> list[str]:
    """Get list of categories used by the authenticated user."""
    expense_service = ExpenseService(db)
    return expense_service.get_categories(current_user.id)


@router.get(
    "/export",
    summary="Export expenses to CSV"
)
def export_expenses(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None)
) -> StreamingResponse:
    """Export expenses to CSV file."""
    # Use page_size=100 but iterate through all pages
    expense_service = ExpenseService(db)
    all_expenses = []
    page = 1
    
    while True:
        filters = ExpenseFilters(
            category=category,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=100
        )
        expenses, total_count, _ = expense_service.list_expenses(current_user.id, filters)
        all_expenses.extend(expenses)
        
        if len(all_expenses) >= total_count or len(expenses) == 0:
            break
        page += 1
    
    expenses = all_expenses
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Category", "Description", "Amount"])
    
    for expense in expenses:
        writer.writerow([
            expense.date.strftime("%Y-%m-%d"),
            expense.category,
            expense.description,
            str(expense.amount)
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"}
    )


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get expense by ID"
)
def get_expense(
    expense_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> ExpenseResponse:
    """Get a single expense by ID."""
    expense_service = ExpenseService(db)
    expense = expense_service.get_by_id(expense_id, current_user.id)
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )
    
    return expense


@router.patch(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Update expense"
)
def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> ExpenseResponse:
    """Update an existing expense."""
    expense_service = ExpenseService(db)
    expense = expense_service.get_by_id(expense_id, current_user.id)
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )
    
    updated_expense = expense_service.update(expense, expense_data)
    return updated_expense


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete expense"
)
def delete_expense(
    expense_id: int,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> None:
    """Delete an expense."""
    expense_service = ExpenseService(db)
    expense = expense_service.get_by_id(expense_id, current_user.id)
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )
    
    expense_service.delete(expense)


@router.get(
    "/tags/all",
    response_model=list[str],
    summary="Get all user tags"
)
def get_all_tags(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> list[str]:
    """Get all unique tags used by the authenticated user."""
    expense_service = ExpenseService(db)
    return expense_service.get_all_tags(current_user.id)
