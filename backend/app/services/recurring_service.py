"""Recurring expense service for business logic."""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.recurring import RecurringExpense
from app.models.expense import Expense
from app.models.user import User
from app.schemas.recurring import (
    RecurringExpenseCreate, RecurringExpenseUpdate, 
    RecurringExpenseListResponse, ProcessedRecurringResult
)


class RecurringExpenseService:
    """Service class for recurring expense operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, recurring_id: int, user_id: int) -> Optional[RecurringExpense]:
        """Get recurring expense by ID for a specific user."""
        return self.db.query(RecurringExpense).filter(
            RecurringExpense.id == recurring_id,
            RecurringExpense.user_id == user_id
        ).first()

    def calculate_next_run_date(
        self, 
        frequency: str, 
        current_date: date,
        day_of_week: Optional[int] = None,
        day_of_month: Optional[int] = None,
        month_of_year: Optional[int] = None
    ) -> date:
        """Calculate the next run date based on frequency."""
        if frequency == "daily":
            return current_date + timedelta(days=1)
        
        elif frequency == "weekly":
            days_ahead = day_of_week - current_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return current_date + timedelta(days=days_ahead)
        
        elif frequency == "monthly":
            next_month = current_date + relativedelta(months=1)
            # Handle months with fewer days
            day = min(day_of_month, 28) if next_month.month == 2 else min(day_of_month, 30)
            try:
                return next_month.replace(day=day)
            except ValueError:
                return next_month.replace(day=28)
        
        elif frequency == "yearly":
            next_year = current_date.year + 1
            try:
                return date(next_year, month_of_year, day_of_month)
            except ValueError:
                return date(next_year, month_of_year, 28)
        
        return current_date + timedelta(days=1)

    def create(self, user: User, data: RecurringExpenseCreate) -> RecurringExpense:
        """Create a new recurring expense."""
        # Calculate initial next_run_date
        today = date.today()
        if data.start_date > today:
            next_run = data.start_date
        else:
            next_run = self.calculate_next_run_date(
                data.frequency, today,
                data.day_of_week, data.day_of_month, data.month_of_year
            )

        recurring = RecurringExpense(
            user_id=user.id,
            amount=data.amount,
            category=data.category,
            description=data.description,
            frequency=data.frequency,
            day_of_week=data.day_of_week,
            day_of_month=data.day_of_month,
            month_of_year=data.month_of_year,
            start_date=data.start_date,
            end_date=data.end_date,
            next_run_date=next_run,
            is_active=True
        )
        self.db.add(recurring)
        self.db.commit()
        self.db.refresh(recurring)
        return recurring

    def update(self, recurring: RecurringExpense, data: RecurringExpenseUpdate) -> RecurringExpense:
        """Update a recurring expense."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(recurring, field, value)
        self.db.commit()
        self.db.refresh(recurring)
        return recurring

    def delete(self, recurring: RecurringExpense) -> bool:
        """Delete a recurring expense."""
        self.db.delete(recurring)
        self.db.commit()
        return True

    def list_recurring(self, user_id: int) -> RecurringExpenseListResponse:
        """List all recurring expenses for a user."""
        items = self.db.query(RecurringExpense).filter(
            RecurringExpense.user_id == user_id
        ).order_by(RecurringExpense.next_run_date).all()
        
        active_count = sum(1 for item in items if item.is_active)
        
        return RecurringExpenseListResponse(
            items=items,
            total=len(items),
            active_count=active_count
        )

    def process_due_recurring(self, user_id: int) -> ProcessedRecurringResult:
        """Process all due recurring expenses for a user and create actual expenses."""
        today = date.today()
        due_recurring = self.db.query(RecurringExpense).filter(
            RecurringExpense.user_id == user_id,
            RecurringExpense.is_active == True,
            RecurringExpense.next_run_date <= today
        ).all()

        created_expenses = []
        errors = []

        for recurring in due_recurring:
            try:
                # Check if end_date has passed
                if recurring.end_date and recurring.end_date < today:
                    recurring.is_active = False
                    continue

                # Create the expense
                expense = Expense(
                    user_id=user_id,
                    amount=recurring.amount,
                    category=recurring.category,
                    description=f"[Recurring] {recurring.description}",
                    date=datetime.combine(today, datetime.min.time())
                )
                self.db.add(expense)
                
                # Update recurring expense
                recurring.last_run_date = today
                recurring.times_executed += 1
                recurring.next_run_date = self.calculate_next_run_date(
                    recurring.frequency, today,
                    recurring.day_of_week, recurring.day_of_month, recurring.month_of_year
                )
                
                self.db.flush()
                created_expenses.append(expense.id)
                
            except Exception as e:
                errors.append(f"Failed to process recurring {recurring.id}: {str(e)}")

        self.db.commit()
        
        return ProcessedRecurringResult(
            processed_count=len(created_expenses),
            created_expenses=created_expenses,
            errors=errors
        )

    def toggle_active(self, recurring: RecurringExpense) -> RecurringExpense:
        """Toggle active status of a recurring expense."""
        recurring.is_active = not recurring.is_active
        if recurring.is_active:
            # Recalculate next run date when reactivating
            recurring.next_run_date = self.calculate_next_run_date(
                recurring.frequency, date.today(),
                recurring.day_of_week, recurring.day_of_month, recurring.month_of_year
            )
        self.db.commit()
        self.db.refresh(recurring)
        return recurring

