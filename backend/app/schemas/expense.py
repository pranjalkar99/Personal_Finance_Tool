"""Expense-related Pydantic schemas."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ExpenseBase(BaseModel):
    """Base expense schema with common fields."""
    
    amount: Decimal = Field(..., gt=0, description="Expense amount (must be positive)")
    category: str = Field(..., min_length=1, max_length=100, description="Expense category")
    description: str = Field(..., min_length=1, max_length=500, description="Expense description")
    date: datetime = Field(..., description="Date of the expense")

    @field_validator('category', 'description')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @field_validator('amount')
    @classmethod
    def round_amount(cls, v: Decimal) -> Decimal:
        return round(v, 2)


class ExpenseCreate(ExpenseBase):
    """Schema for creating a new expense."""
    
    idempotency_key: Optional[str] = Field(
        None, 
        max_length=64, 
        description="Unique key to prevent duplicate submissions"
    )


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense."""
    
    amount: Optional[Decimal] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    date: Optional[datetime] = None

    @field_validator('category', 'description')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @field_validator('amount')
    @classmethod
    def round_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        return round(v, 2) if v else v


class ExpenseResponse(BaseModel):
    """Schema for expense response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    amount: Decimal
    category: str
    description: str
    date: datetime
    created_at: datetime
    updated_at: datetime


class ExpenseListResponse(BaseModel):
    """Schema for list of expenses with metadata."""
    
    expenses: List[ExpenseResponse]
    total: Decimal = Field(..., description="Total amount of all expenses in the list")
    count: int = Field(..., description="Number of expenses in the list")
    page: int = Field(default=1)
    page_size: int = Field(default=50)
    total_pages: int = Field(default=1)


class ExpenseFilters(BaseModel):
    """Schema for expense filtering options."""
    
    category: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    search: Optional[str] = Field(None, description="Search in description")
    sort: Optional[Literal["date_desc", "date_asc", "amount_desc", "amount_asc"]] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class ExpenseSummary(BaseModel):
    """Schema for expense summary/analytics."""
    
    total_expenses: Decimal
    expense_count: int
    average_expense: Decimal
    category_breakdown: dict[str, Decimal]
    monthly_totals: dict[str, Decimal]


class CategoryData(BaseModel):
    """Category analytics data."""
    category: str
    total: Decimal
    count: int
    percentage: Decimal


class MonthlyData(BaseModel):
    """Monthly analytics data."""
    month: str
    total: Decimal
    count: int


class DailyData(BaseModel):
    """Daily analytics data."""
    date: str
    total: Decimal
    count: int


class AnalyticsResponse(BaseModel):
    """Comprehensive analytics response."""
    
    # Summary
    total_expenses: Decimal
    expense_count: int
    average_expense: Decimal
    highest_expense: Decimal
    lowest_expense: Decimal
    
    # Category breakdown
    categories: List[CategoryData]
    
    # Time series
    monthly_data: List[MonthlyData]
    daily_data: List[DailyData]  # Last 30 days
    
    # Trends
    current_month_total: Decimal
    previous_month_total: Decimal
    month_over_month_change: Decimal  # Percentage change
    
    # Top categories
    top_category: Optional[str]
    top_category_amount: Decimal
