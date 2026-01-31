"""Budget service for business logic."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.budget import Budget
from app.models.expense import Expense
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetResponse, 
    BudgetStatus, BudgetAlert, BudgetOverview
)


class BudgetService:
    """Service class for budget operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, budget_id: int, user_id: int) -> Optional[Budget]:
        """Get budget by ID for a specific user."""
        return self.db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == user_id
        ).first()

    def get_by_category(self, user_id: int, category: str) -> Optional[Budget]:
        """Get budget by category for a specific user."""
        return self.db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.category == category
        ).first()

    def create(self, user: User, budget_data: BudgetCreate) -> Budget:
        """Create a new budget."""
        # Check if budget for this category already exists
        existing = self.get_by_category(user.id, budget_data.category)
        if existing:
            # Update existing instead
            existing.monthly_limit = budget_data.monthly_limit
            existing.alert_threshold = budget_data.alert_threshold
            self.db.commit()
            self.db.refresh(existing)
            return existing

        budget = Budget(
            user_id=user.id,
            category=budget_data.category,
            monthly_limit=budget_data.monthly_limit,
            alert_threshold=budget_data.alert_threshold
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def update(self, budget: Budget, budget_data: BudgetUpdate) -> Budget:
        """Update an existing budget."""
        update_data = budget_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(budget, field, value)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def delete(self, budget: Budget) -> bool:
        """Delete a budget."""
        self.db.delete(budget)
        self.db.commit()
        return True

    def list_budgets(self, user_id: int) -> List[Budget]:
        """List all budgets for a user."""
        return self.db.query(Budget).filter(Budget.user_id == user_id).all()

    def get_category_spending(self, user_id: int, category: str, year: int, month: int) -> Decimal:
        """Get total spending for a category in a specific month."""
        result = self.db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            Expense.category == category,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).scalar()
        return Decimal(str(result)) if result else Decimal("0")

    def get_budget_status(self, budget: Budget, year: int = None, month: int = None) -> BudgetStatus:
        """Get status of a single budget including current spending."""
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        current_spending = self.get_category_spending(
            budget.user_id, budget.category, year, month
        )
        
        remaining = budget.monthly_limit - current_spending
        percentage_used = (current_spending / budget.monthly_limit * 100) if budget.monthly_limit > 0 else Decimal("0")
        
        return BudgetStatus(
            budget=BudgetResponse.model_validate(budget),
            current_spending=current_spending,
            remaining=max(remaining, Decimal("0")),
            percentage_used=round(percentage_used, 1),
            is_over_budget=current_spending > budget.monthly_limit,
            is_alert=percentage_used >= budget.alert_threshold
        )

    def get_budget_overview(self, user_id: int) -> BudgetOverview:
        """Get overview of all budgets with alerts."""
        budgets = self.list_budgets(user_id)
        now = datetime.now()
        
        budget_statuses = []
        alerts = []
        total_budgeted = Decimal("0")
        total_spent = Decimal("0")
        categories_over_budget = 0

        for budget in budgets:
            status = self.get_budget_status(budget, now.year, now.month)
            budget_statuses.append(status)
            total_budgeted += budget.monthly_limit
            total_spent += status.current_spending

            if status.is_over_budget:
                categories_over_budget += 1
                alerts.append(BudgetAlert(
                    category=budget.category,
                    monthly_limit=budget.monthly_limit,
                    current_spending=status.current_spending,
                    percentage_used=status.percentage_used,
                    message=f"Over budget! Spent ₹{status.current_spending} of ₹{budget.monthly_limit}",
                    severity="danger"
                ))
            elif status.is_alert:
                alerts.append(BudgetAlert(
                    category=budget.category,
                    monthly_limit=budget.monthly_limit,
                    current_spending=status.current_spending,
                    percentage_used=status.percentage_used,
                    message=f"Approaching limit: {status.percentage_used}% used",
                    severity="warning"
                ))

        return BudgetOverview(
            budgets=budget_statuses,
            alerts=alerts,
            total_budgeted=total_budgeted,
            total_spent=total_spent,
            categories_over_budget=categories_over_budget
        )

    def check_budget_on_expense(self, user_id: int, category: str, amount: Decimal) -> Optional[BudgetAlert]:
        """Check if adding an expense would trigger a budget alert."""
        budget = self.get_by_category(user_id, category)
        if not budget:
            return None

        now = datetime.now()
        current_spending = self.get_category_spending(user_id, category, now.year, now.month)
        new_total = current_spending + amount
        percentage = (new_total / budget.monthly_limit * 100) if budget.monthly_limit > 0 else Decimal("0")

        if new_total > budget.monthly_limit:
            return BudgetAlert(
                category=category,
                monthly_limit=budget.monthly_limit,
                current_spending=new_total,
                percentage_used=round(percentage, 1),
                message=f"This expense will exceed your {category} budget!",
                severity="danger"
            )
        elif percentage >= budget.alert_threshold:
            return BudgetAlert(
                category=category,
                monthly_limit=budget.monthly_limit,
                current_spending=new_total,
                percentage_used=round(percentage, 1),
                message=f"This expense will use {round(percentage, 1)}% of your {category} budget",
                severity="warning"
            )
        return None

