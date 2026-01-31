"""Tests for expense endpoints."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Expense


class TestCreateExpense:
    """Tests for expense creation."""

    def test_create_expense_success(self, authenticated_client: TestClient):
        """Test successful expense creation."""
        expense_data = {
            "amount": 100.50,
            "category": "Food & Dining",
            "description": "Lunch at restaurant",
            "date": "2026-01-31T12:00:00Z"
        }
        
        response = authenticated_client.post("/expenses", json=expense_data)
        
        assert response.status_code == 201
        data = response.json()
        assert Decimal(data["amount"]) == Decimal("100.50")
        assert data["category"] == "Food & Dining"
        assert data["description"] == "Lunch at restaurant"

    def test_create_expense_unauthenticated(self, client: TestClient):
        """Test expense creation without authentication."""
        expense_data = {
            "amount": 100.50,
            "category": "Food",
            "description": "Test",
            "date": "2026-01-31T12:00:00Z"
        }
        
        response = client.post("/expenses", json=expense_data)
        
        assert response.status_code == 401  # No auth header

    def test_create_expense_idempotency(self, authenticated_client: TestClient):
        """Test idempotent expense creation."""
        expense_data = {
            "amount": 100.50,
            "category": "Food",
            "description": "Test",
            "date": "2026-01-31T12:00:00Z",
            "idempotency_key": "unique-key-123"
        }
        
        # Create first expense
        response1 = authenticated_client.post("/expenses", json=expense_data)
        assert response1.status_code == 201
        expense_id = response1.json()["id"]
        
        # Create with same idempotency key
        response2 = authenticated_client.post("/expenses", json=expense_data)
        assert response2.status_code == 201
        assert response2.json()["id"] == expense_id  # Same expense returned

    def test_create_expense_invalid_amount(self, authenticated_client: TestClient):
        """Test expense creation with invalid amount."""
        expense_data = {
            "amount": -100,
            "category": "Food",
            "description": "Test",
            "date": "2026-01-31T12:00:00Z"
        }
        
        response = authenticated_client.post("/expenses", json=expense_data)
        
        assert response.status_code == 422


class TestListExpenses:
    """Tests for expense listing."""

    def test_list_expenses_empty(self, authenticated_client: TestClient):
        """Test listing expenses when none exist."""
        response = authenticated_client.get("/expenses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["expenses"] == []
        assert data["count"] == 0
        assert Decimal(data["total"]) == Decimal("0")

    def test_list_expenses_with_data(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test listing expenses with data."""
        # Create test expenses
        for i in range(3):
            expense = Expense(
                user_id=test_user.id,
                amount=Decimal("100.00") * (i + 1),
                category="Test",
                description=f"Expense {i}",
                date=datetime.now()
            )
            db.add(expense)
        db.commit()
        
        response = authenticated_client.get("/expenses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert Decimal(data["total"]) == Decimal("600.00")

    def test_list_expenses_filter_by_category(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test filtering expenses by category."""
        # Create expenses with different categories
        expense1 = Expense(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            category="Food",
            description="Food expense",
            date=datetime.now()
        )
        expense2 = Expense(
            user_id=test_user.id,
            amount=Decimal("200.00"),
            category="Transport",
            description="Transport expense",
            date=datetime.now()
        )
        db.add_all([expense1, expense2])
        db.commit()
        
        response = authenticated_client.get("/expenses?category=Food")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["expenses"][0]["category"] == "Food"

    def test_list_expenses_sort_by_date(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test sorting expenses by date."""
        now = datetime.now()
        expense1 = Expense(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            category="Test",
            description="Older",
            date=now - timedelta(days=5)
        )
        expense2 = Expense(
            user_id=test_user.id,
            amount=Decimal("200.00"),
            category="Test",
            description="Newer",
            date=now
        )
        db.add_all([expense1, expense2])
        db.commit()
        
        response = authenticated_client.get("/expenses?sort=date_desc")
        
        assert response.status_code == 200
        data = response.json()
        assert data["expenses"][0]["description"] == "Newer"
        assert data["expenses"][1]["description"] == "Older"

    def test_list_expenses_pagination(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test expense pagination."""
        # Create 15 expenses
        for i in range(15):
            expense = Expense(
                user_id=test_user.id,
                amount=Decimal("10.00"),
                category="Test",
                description=f"Expense {i}",
                date=datetime.now()
            )
            db.add(expense)
        db.commit()
        
        # Get first page
        response = authenticated_client.get("/expenses?page=1&page_size=10")
        data = response.json()
        assert len(data["expenses"]) == 10
        assert data["count"] == 15
        assert data["page"] == 1
        assert data["total_pages"] == 2
        
        # Get second page
        response = authenticated_client.get("/expenses?page=2&page_size=10")
        data = response.json()
        assert len(data["expenses"]) == 5

    def test_list_expenses_user_isolation(
        self, authenticated_client: TestClient, db: Session, test_user: User, second_user: User
    ):
        """Test that users can only see their own expenses."""
        # Create expense for test_user
        expense1 = Expense(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            category="Test",
            description="Test user expense",
            date=datetime.now()
        )
        # Create expense for second_user
        expense2 = Expense(
            user_id=second_user.id,
            amount=Decimal("200.00"),
            category="Test",
            description="Second user expense",
            date=datetime.now()
        )
        db.add_all([expense1, expense2])
        db.commit()
        
        response = authenticated_client.get("/expenses")
        
        data = response.json()
        assert data["count"] == 1
        assert data["expenses"][0]["description"] == "Test user expense"


class TestUpdateExpense:
    """Tests for expense updates."""

    def test_update_expense_success(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test successful expense update."""
        expense = Expense(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            category="Food",
            description="Original",
            date=datetime.now()
        )
        db.add(expense)
        db.commit()
        
        response = authenticated_client.patch(
            f"/expenses/{expense.id}",
            json={"amount": 150.00, "description": "Updated"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["amount"]) == Decimal("150.00")
        assert data["description"] == "Updated"
        assert data["category"] == "Food"  # Unchanged

    def test_update_expense_not_found(self, authenticated_client: TestClient):
        """Test updating non-existent expense."""
        response = authenticated_client.patch(
            "/expenses/99999",
            json={"amount": 150.00}
        )
        
        assert response.status_code == 404


class TestDeleteExpense:
    """Tests for expense deletion."""

    def test_delete_expense_success(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test successful expense deletion."""
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
        
        response = authenticated_client.delete(f"/expenses/{expense_id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = authenticated_client.get(f"/expenses/{expense_id}")
        assert get_response.status_code == 404

    def test_delete_expense_not_found(self, authenticated_client: TestClient):
        """Test deleting non-existent expense."""
        response = authenticated_client.delete("/expenses/99999")
        
        assert response.status_code == 404


class TestExpenseSummary:
    """Tests for expense summary."""

    def test_get_summary(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test expense summary."""
        now = datetime.now()
        expenses = [
            Expense(
                user_id=test_user.id,
                amount=Decimal("100.00"),
                category="Food",
                description="Food 1",
                date=now
            ),
            Expense(
                user_id=test_user.id,
                amount=Decimal("200.00"),
                category="Food",
                description="Food 2",
                date=now
            ),
            Expense(
                user_id=test_user.id,
                amount=Decimal("300.00"),
                category="Transport",
                description="Transport",
                date=now
            ),
        ]
        db.add_all(expenses)
        db.commit()
        
        response = authenticated_client.get("/expenses/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_expenses"]) == Decimal("600.00")
        assert data["expense_count"] == 3
        assert Decimal(data["average_expense"]) == Decimal("200.00")
        assert Decimal(data["category_breakdown"]["Food"]) == Decimal("300.00")
        assert Decimal(data["category_breakdown"]["Transport"]) == Decimal("300.00")

