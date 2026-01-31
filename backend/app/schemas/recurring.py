"""Recurring expense Pydantic schemas."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class RecurringExpenseBase(BaseModel):
    """Base recurring expense schema."""
    amount: Decimal = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    frequency: Literal["daily", "weekly", "monthly", "yearly"]
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="0=Mon, 6=Sun")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    month_of_year: Optional[int] = Field(None, ge=1, le=12)
    start_date: date
    end_date: Optional[date] = None

    @model_validator(mode='after')
    def validate_recurrence_params(self):
        if self.frequency == "weekly" and self.day_of_week is None:
            raise ValueError("day_of_week required for weekly frequency")
        if self.frequency == "monthly" and self.day_of_month is None:
            raise ValueError("day_of_month required for monthly frequency")
        if self.frequency == "yearly":
            if self.day_of_month is None or self.month_of_year is None:
                raise ValueError("day_of_month and month_of_year required for yearly frequency")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class RecurringExpenseCreate(RecurringExpenseBase):
    """Schema for creating a recurring expense."""
    pass


class RecurringExpenseUpdate(BaseModel):
    """Schema for updating a recurring expense."""
    amount: Optional[Decimal] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None
    end_date: Optional[date] = None


class RecurringExpenseResponse(BaseModel):
    """Schema for recurring expense response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    amount: Decimal
    category: str
    description: str
    frequency: str
    day_of_week: Optional[int]
    day_of_month: Optional[int]
    month_of_year: Optional[int]
    start_date: date
    end_date: Optional[date]
    next_run_date: date
    last_run_date: Optional[date]
    is_active: bool
    times_executed: int
    created_at: datetime
    updated_at: datetime


class RecurringExpenseListResponse(BaseModel):
    """List of recurring expenses."""
    items: List[RecurringExpenseResponse]
    total: int
    active_count: int


class ProcessedRecurringResult(BaseModel):
    """Result of processing recurring expenses."""
    processed_count: int
    created_expenses: List[int]  # IDs of created expenses
    errors: List[str]

