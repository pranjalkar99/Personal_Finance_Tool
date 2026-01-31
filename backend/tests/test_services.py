"""Tests for service layer."""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models import User, Expense
from app.services.user_service import UserService
from app.services.expense_service import ExpenseService
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseFilters


class TestUserService:
    """Tests for UserService."""

    def test_create_user(self, db: Session):
        """Test user creation."""
        service = UserService(db)
        user_data = UserCreate(
            email="service@test.com",
            username="servicetest",
            password="Test123!",
            full_name="Service Test"
        )
        
        user = service.create(user_data)
        
        assert user.id is not None
        assert user.email == "service@test.com"
        assert user.username == "servicetest"
        assert user.hashed_password != "Test123!"  # Password should be hashed

    def test_authenticate_success(self, db: Session, test_user: User):
        """Test successful authentication."""
        service = UserService(db)
        
        user = service.authenticate(test_user.username, "Test123!")
        
        assert user is not None
        assert user.id == test_user.id

    def test_authenticate_wrong_password(self, db: Session, test_user: User):
        """Test authentication with wrong password."""
        service = UserService(db)
        
        user = service.authenticate(test_user.username, "WrongPassword!")
        
        assert user is None

    def test_get_by_email(self, db: Session, test_user: User):
        """Test getting user by email."""
        service = UserService(db)
        
        user = service.get_by_email(test_user.email)
        
        assert user is not None
        assert user.id == test_user.id

    def test_is_email_taken(self, db: Session, test_user: User):
        """Test email taken check."""
        service = UserService(db)
        
        assert service.is_email_taken(test_user.email) is True
        assert service.is_email_taken("new@email.com") is False
        assert service.is_email_taken(test_user.email, test_user.id) is False


class TestExpenseService:
    """Tests for ExpenseService."""

    def test_create_expense(self, db: Session, test_user: User):
        """Test expense creation."""
        service = ExpenseService(db)
        expense_data = ExpenseCreate(
            amount=Decimal("100.50"),
            category="Food",
            description="Test expense",
            date=datetime.now()
        )
        
        expense = service.create(test_user, expense_data)
        
        assert expense.id is not None
        assert expense.user_id == test_user.id
        assert expense.amount == Decimal("100.50")

    def test_create_expense_idempotent(self, db: Session, test_user: User):
        """Test idempotent expense creation."""
        service = ExpenseService(db)
        expense_data = ExpenseCreate(
            amount=Decimal("100.50"),
            category="Food",
            description="Test expense",
            date=datetime.now(),
            idempotency_key="test-key-123"
        )
        
        expense1 = service.create(test_user, expense_data)
        expense2 = service.create(test_user, expense_data)
        
        assert expense1.id == expense2.id

    def test_update_expense(self, db: Session, test_user: User):
        """Test expense update."""
        service = ExpenseService(db)
        
        # Create expense
        expense = Expense(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            category="Food",
            description="Original",
            date=datetime.now()
        )
        db.add(expense)
        db.commit()
        
        # Update expense
        update_data = ExpenseUpdate(amount=Decimal("150.00"))
        updated = service.update(expense, update_data)
        
        assert updated.amount == Decimal("150.00")
        assert updated.description == "Original"  # Unchanged

    def test_delete_expense(self, db: Session, test_user: User):
        """Test expense deletion."""
        service = ExpenseService(db)
        
        expense = Expense(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            category="Food",
            description="To delete",
            date=datetime.now()
        )
        db.add(expense)
        db.commit()
        expense_id = expense.id
        
        result = service.delete(expense)
        
        assert result is True
        assert service.get_by_id(expense_id, test_user.id) is None

    def test_list_expenses_with_filters(self, db: Session, test_user: User):
        """Test listing expenses with filters."""
        service = ExpenseService(db)
        
        # Create test expenses
        expense1 = Expense(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            category="Food",
            description="Food expense",
            date=datetime(2026, 1, 15)
        )
        expense2 = Expense(
            user_id=test_user.id,
            amount=Decimal("200.00"),
            category="Transport",
            description="Transport expense",
            date=datetime(2026, 1, 20)
        )
        db.add_all([expense1, expense2])
        db.commit()
        
        # Filter by category
        filters = ExpenseFilters(category="Food")
        expenses, count, total = service.list_expenses(test_user.id, filters)
        
        assert count == 1
        assert expenses[0].category == "Food"
        assert total == Decimal("100.00")

    def test_get_summary(self, db: Session, test_user: User):
        """Test expense summary."""
        service = ExpenseService(db)
        
        expenses = [
            Expense(
                user_id=test_user.id,
                amount=Decimal("100.00"),
                category="Food",
                description="Food 1",
                date=datetime(2026, 1, 15)
            ),
            Expense(
                user_id=test_user.id,
                amount=Decimal("200.00"),
                category="Transport",
                description="Transport",
                date=datetime(2026, 1, 20)
            ),
        ]
        db.add_all(expenses)
        db.commit()
        
        summary = service.get_summary(test_user.id)
        
        assert summary.total_expenses == Decimal("300.00")
        assert summary.expense_count == 2
        assert summary.average_expense == Decimal("150.00")
        assert "Food" in summary.category_breakdown
        assert "Transport" in summary.category_breakdown

