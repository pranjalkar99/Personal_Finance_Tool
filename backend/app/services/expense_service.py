"""Expense service for business logic."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, extract

from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate, ExpenseUpdate, ExpenseFilters, ExpenseSummary,
    AnalyticsResponse, CategoryData, MonthlyData, DailyData
)


class ExpenseService:
    """Service class for expense operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, expense_id: int, user_id: int) -> Optional[Expense]:
        """Get expense by ID for a specific user."""
        return self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == user_id
        ).first()

    def get_by_idempotency_key(self, key: str, user_id: int) -> Optional[Expense]:
        """Get expense by idempotency key for a specific user."""
        return self.db.query(Expense).filter(
            Expense.idempotency_key == key,
            Expense.user_id == user_id
        ).first()

    def create(self, user: User, expense_data: ExpenseCreate) -> Expense:
        """Create a new expense for a user."""
        # Check for idempotency
        if expense_data.idempotency_key:
            existing = self.get_by_idempotency_key(expense_data.idempotency_key, user.id)
            if existing:
                return existing

        expense = Expense(
            user_id=user.id,
            amount=expense_data.amount,
            category=expense_data.category,
            description=expense_data.description,
            date=expense_data.date,
            idempotency_key=expense_data.idempotency_key
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def update(self, expense: Expense, expense_data: ExpenseUpdate) -> Expense:
        """Update an existing expense."""
        update_data = expense_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(expense, field, value)
        
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def delete(self, expense: Expense) -> bool:
        """Delete an expense."""
        self.db.delete(expense)
        self.db.commit()
        return True

    def list_expenses(
        self, 
        user_id: int, 
        filters: ExpenseFilters
    ) -> Tuple[List[Expense], int, Decimal]:
        """
        List expenses with filtering, sorting, and pagination.
        Returns: (expenses, total_count, total_amount)
        """
        query = self.db.query(Expense).filter(Expense.user_id == user_id)

        # Apply filters
        if filters.category:
            query = query.filter(Expense.category.ilike(f"%{filters.category}%"))
        
        if filters.start_date:
            query = query.filter(Expense.date >= datetime.combine(filters.start_date, datetime.min.time()))
        
        if filters.end_date:
            query = query.filter(Expense.date <= datetime.combine(filters.end_date, datetime.max.time()))
        
        if filters.min_amount is not None:
            query = query.filter(Expense.amount >= filters.min_amount)
        
        if filters.max_amount is not None:
            query = query.filter(Expense.amount <= filters.max_amount)
        
        # Search in description
        if filters.search:
            query = query.filter(Expense.description.ilike(f"%{filters.search}%"))

        # Get total count and sum before pagination
        total_count = query.count()
        total_amount = self.db.query(func.sum(Expense.amount)).filter(
            Expense.id.in_([e.id for e in query.all()])
        ).scalar() or Decimal("0")

        # Apply sorting
        sort_mapping = {
            "date_desc": desc(Expense.date),
            "date_asc": asc(Expense.date),
            "amount_desc": desc(Expense.amount),
            "amount_asc": asc(Expense.amount),
        }
        
        if filters.sort and filters.sort in sort_mapping:
            query = query.order_by(sort_mapping[filters.sort], desc(Expense.created_at))
        else:
            query = query.order_by(desc(Expense.created_at))

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        expenses = query.offset(offset).limit(filters.page_size).all()

        return expenses, total_count, total_amount

    def get_summary(self, user_id: int, year: Optional[int] = None) -> ExpenseSummary:
        """Get expense summary/analytics for a user."""
        query = self.db.query(Expense).filter(Expense.user_id == user_id)
        
        if year:
            query = query.filter(extract('year', Expense.date) == year)

        expenses = query.all()
        
        if not expenses:
            return ExpenseSummary(
                total_expenses=Decimal("0"),
                expense_count=0,
                average_expense=Decimal("0"),
                category_breakdown={},
                monthly_totals={}
            )

        total = sum(Decimal(str(e.amount)) for e in expenses)
        count = len(expenses)
        average = total / count if count > 0 else Decimal("0")

        # Category breakdown
        category_totals: dict[str, Decimal] = defaultdict(Decimal)
        for expense in expenses:
            category_totals[expense.category] += Decimal(str(expense.amount))

        # Monthly totals
        monthly_totals: dict[str, Decimal] = defaultdict(Decimal)
        for expense in expenses:
            month_key = expense.date.strftime("%Y-%m")
            monthly_totals[month_key] += Decimal(str(expense.amount))

        return ExpenseSummary(
            total_expenses=total,
            expense_count=count,
            average_expense=round(average, 2),
            category_breakdown=dict(category_totals),
            monthly_totals=dict(sorted(monthly_totals.items()))
        )

    def get_analytics(self, user_id: int, months: int = 12) -> AnalyticsResponse:
        """Get comprehensive analytics for a user."""
        # Get expenses for the time period
        start_date = datetime.now() - timedelta(days=months * 30)
        expenses = self.db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date
        ).all()

        if not expenses:
            return AnalyticsResponse(
                total_expenses=Decimal("0"),
                expense_count=0,
                average_expense=Decimal("0"),
                highest_expense=Decimal("0"),
                lowest_expense=Decimal("0"),
                categories=[],
                monthly_data=[],
                daily_data=[],
                current_month_total=Decimal("0"),
                previous_month_total=Decimal("0"),
                month_over_month_change=Decimal("0"),
                top_category=None,
                top_category_amount=Decimal("0")
            )

        # Basic stats
        amounts = [Decimal(str(e.amount)) for e in expenses]
        total = sum(amounts)
        count = len(expenses)
        average = total / count if count > 0 else Decimal("0")
        highest = max(amounts)
        lowest = min(amounts)

        # Category breakdown with percentages
        category_totals: dict[str, dict] = defaultdict(lambda: {"total": Decimal("0"), "count": 0})
        for expense in expenses:
            category_totals[expense.category]["total"] += Decimal(str(expense.amount))
            category_totals[expense.category]["count"] += 1

        categories = []
        for cat, data in sorted(category_totals.items(), key=lambda x: x[1]["total"], reverse=True):
            percentage = (data["total"] / total * 100) if total > 0 else Decimal("0")
            categories.append(CategoryData(
                category=cat,
                total=data["total"],
                count=data["count"],
                percentage=round(percentage, 1)
            ))

        # Monthly data
        monthly_totals: dict[str, dict] = defaultdict(lambda: {"total": Decimal("0"), "count": 0})
        for expense in expenses:
            month_key = expense.date.strftime("%Y-%m")
            monthly_totals[month_key]["total"] += Decimal(str(expense.amount))
            monthly_totals[month_key]["count"] += 1

        monthly_data = [
            MonthlyData(month=month, total=data["total"], count=data["count"])
            for month, data in sorted(monthly_totals.items())
        ]

        # Daily data (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        daily_totals: dict[str, dict] = defaultdict(lambda: {"total": Decimal("0"), "count": 0})
        for expense in expenses:
            if expense.date >= thirty_days_ago:
                day_key = expense.date.strftime("%Y-%m-%d")
                daily_totals[day_key]["total"] += Decimal(str(expense.amount))
                daily_totals[day_key]["count"] += 1

        # Fill in missing days with zeros
        daily_data = []
        for i in range(30):
            day = (datetime.now() - timedelta(days=29-i)).strftime("%Y-%m-%d")
            if day in daily_totals:
                daily_data.append(DailyData(
                    date=day,
                    total=daily_totals[day]["total"],
                    count=daily_totals[day]["count"]
                ))
            else:
                daily_data.append(DailyData(date=day, total=Decimal("0"), count=0))

        # Month over month comparison
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        previous_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        
        current_month_total = monthly_totals.get(current_month, {"total": Decimal("0")})["total"]
        previous_month_total = monthly_totals.get(previous_month, {"total": Decimal("0")})["total"]
        
        if previous_month_total > 0:
            mom_change = ((current_month_total - previous_month_total) / previous_month_total * 100)
        else:
            mom_change = Decimal("100") if current_month_total > 0 else Decimal("0")

        # Top category
        top_category = categories[0].category if categories else None
        top_category_amount = categories[0].total if categories else Decimal("0")

        return AnalyticsResponse(
            total_expenses=total,
            expense_count=count,
            average_expense=round(average, 2),
            highest_expense=highest,
            lowest_expense=lowest,
            categories=categories,
            monthly_data=monthly_data,
            daily_data=daily_data,
            current_month_total=current_month_total,
            previous_month_total=previous_month_total,
            month_over_month_change=round(mom_change, 1),
            top_category=top_category,
            top_category_amount=top_category_amount
        )

    def get_categories(self, user_id: int) -> List[str]:
        """Get list of categories used by a user."""
        categories = self.db.query(Expense.category).filter(
            Expense.user_id == user_id
        ).distinct().all()
        return sorted([c[0] for c in categories])
