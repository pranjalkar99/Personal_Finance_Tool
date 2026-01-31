"""Expense-related Pydantic schemas."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


# Supported currencies
SUPPORTED_CURRENCIES = ["INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD"]


class ExpenseBase(BaseModel):
    """Base expense schema with common fields."""
    
    amount: Decimal = Field(..., gt=0, description="Expense amount (must be positive)")
    category: str = Field(..., min_length=1, max_length=100, description="Expense category")
    description: str = Field(..., min_length=1, max_length=500, description="Expense description")
    date: datetime = Field(..., description="Date of the expense")
    
    # New fields
    currency: str = Field(default="INR", description="Currency code")
    tags: List[str] = Field(default_factory=list, description="Custom tags/labels")
    notes: Optional[str] = Field(None, max_length=2000, description="Additional notes")

    @field_validator('category', 'description')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @field_validator('amount')
    @classmethod
    def round_amount(cls, v: Decimal) -> Decimal:
        return round(v, 2)
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper()
        if v not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Currency must be one of: {', '.join(SUPPORTED_CURRENCIES)}")
        return v
    
    @field_validator('tags')
    @classmethod
    def clean_tags(cls, v: List[str]) -> List[str]:
        return [tag.strip().lower() for tag in v if tag.strip()][:10]  # Max 10 tags


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
    currency: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator('category', 'description')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v

    @field_validator('amount')
    @classmethod
    def round_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        return round(v, 2) if v else v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.upper()
            if v not in SUPPORTED_CURRENCIES:
                raise ValueError(f"Currency must be one of: {', '.join(SUPPORTED_CURRENCIES)}")
        return v
    
    @field_validator('tags')
    @classmethod
    def clean_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v:
            return [tag.strip().lower() for tag in v if tag.strip()][:10]
        return v


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
    
    # New fields
    currency: str = "INR"
    tags: List[str] = []
    notes: Optional[str] = None
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None


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
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    currency: Optional[str] = Field(None, description="Filter by currency")
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


class CurrencyRate(BaseModel):
    """Currency exchange rate."""
    from_currency: str
    to_currency: str
    rate: Decimal
    updated_at: datetime


class AttachmentResponse(BaseModel):
    """Response for file attachment."""
    url: str
    filename: str
    size: int
    content_type: str
