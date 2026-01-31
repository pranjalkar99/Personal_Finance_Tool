"""Budget-related Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BudgetBase(BaseModel):
    """Base budget schema."""
    category: str = Field(..., min_length=1, max_length=100)
    monthly_limit: Decimal = Field(..., gt=0, description="Monthly budget limit")
    alert_threshold: int = Field(default=80, ge=50, le=100, description="Alert at this % of limit")


class BudgetCreate(BudgetBase):
    """Schema for creating a budget."""
    pass


class BudgetUpdate(BaseModel):
    """Schema for updating a budget."""
    monthly_limit: Optional[Decimal] = Field(None, gt=0)
    alert_threshold: Optional[int] = Field(None, ge=50, le=100)


class BudgetResponse(BudgetBase):
    """Schema for budget response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class BudgetStatus(BaseModel):
    """Budget status with current spending."""
    budget: BudgetResponse
    current_spending: Decimal
    remaining: Decimal
    percentage_used: Decimal
    is_over_budget: bool
    is_alert: bool  # True if spending >= alert_threshold


class BudgetAlert(BaseModel):
    """Budget alert notification."""
    category: str
    monthly_limit: Decimal
    current_spending: Decimal
    percentage_used: Decimal
    message: str
    severity: str  # "warning" (approaching), "danger" (over budget)


class BudgetOverview(BaseModel):
    """Overview of all budgets with status."""
    budgets: List[BudgetStatus]
    alerts: List[BudgetAlert]
    total_budgeted: Decimal
    total_spent: Decimal
    categories_over_budget: int

