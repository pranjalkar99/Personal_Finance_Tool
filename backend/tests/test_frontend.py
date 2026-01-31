"""Frontend integration tests - testing all pages and features."""

import pytest
from datetime import datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Expense


class TestFrontendPages:
    """Test that frontend pages load correctly."""

    def test_home_page_loads(self, client: TestClient):
        """Test that the home page (login) loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Expense Tracker" in response.text
        assert "Login" in response.text
        assert "login-form" in response.text

    def test_static_css_loads(self, client: TestClient):
        """Test that CSS file loads."""
        response = client.get("/static/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
        assert ":root" in response.text

    def test_static_js_loads(self, client: TestClient):
        """Test that JavaScript file loads."""
        response = client.get("/static/app.js")
        assert response.status_code == 200
        assert "application/javascript" in response.headers["content-type"] or "text/javascript" in response.headers["content-type"]
        assert "API_BASE_URL" in response.text

    def test_register_form_elements_present(self, client: TestClient):
        """Test that register form elements are in the HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'id="register-form"' in response.text
        assert 'id="register-email"' in response.text
        assert 'id="register-username"' in response.text
        assert 'id="register-password"' in response.text

    def test_main_app_elements_present(self, client: TestClient):
        """Test that main app elements are in the HTML."""
        response = client.get("/")
        assert response.status_code == 200
        # Summary section
        assert 'id="summary-total"' in response.text
        assert 'id="summary-month"' in response.text
        assert 'id="summary-count"' in response.text
        # Expense form
        assert 'id="expense-form"' in response.text
        assert 'id="amount"' in response.text
        assert 'id="category"' in response.text
        # Expense list
        assert 'id="expenses-table"' in response.text
        assert 'id="filter-category"' in response.text
        # Pagination
        assert 'id="pagination"' in response.text
        assert 'id="prev-page"' in response.text
        assert 'id="next-page"' in response.text

    def test_delete_modal_present(self, client: TestClient):
        """Test that delete modal is in the HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'id="delete-modal"' in response.text
        assert 'id="cancel-delete"' in response.text
        assert 'id="confirm-delete"' in response.text


class TestAuthFlow:
    """Test the authentication flow."""

    def test_register_new_user(self, client: TestClient):
        """Test user registration."""
        response = client.post("/auth/register", json={
            "email": "frontend_test@example.com",
            "username": "frontenduser",
            "password": "Test123!",
            "full_name": "Frontend Test"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "frontend_test@example.com"
        assert data["username"] == "frontenduser"

    def test_login_after_register(self, client: TestClient):
        """Test login after registration."""
        # First register
        client.post("/auth/register", json={
            "email": "logintest@example.com",
            "username": "loginuser",
            "password": "Test123!"
        })
        
        # Then login
        response = client.post("/auth/login", json={
            "username": "loginuser",
            "password": "Test123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_get_user_profile(self, authenticated_client: TestClient):
        """Test getting user profile."""
        response = authenticated_client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "username" in data


class TestExpenseFlow:
    """Test the expense management flow."""

    def test_create_expense(self, authenticated_client: TestClient):
        """Test creating an expense."""
        response = authenticated_client.post("/expenses", json={
            "amount": 100.50,
            "category": "Food & Dining",
            "description": "Test lunch",
            "date": "2026-01-31T12:00:00Z"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "Food & Dining"
        assert data["description"] == "Test lunch"

    def test_list_expenses_empty(self, authenticated_client: TestClient):
        """Test listing expenses when empty."""
        response = authenticated_client.get("/expenses")
        assert response.status_code == 200
        data = response.json()
        assert "expenses" in data
        assert "total" in data
        assert "count" in data
        assert "page" in data
        assert "total_pages" in data

    def test_list_expenses_with_data(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test listing expenses with data."""
        # Create expenses
        for i in range(5):
            expense = Expense(
                user_id=test_user.id,
                amount=Decimal("100.00") * (i + 1),
                category="Food & Dining" if i % 2 == 0 else "Shopping",
                description=f"Test expense {i}",
                date=datetime.now()
            )
            db.add(expense)
        db.commit()

        response = authenticated_client.get("/expenses")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5
        assert len(data["expenses"]) == 5

    def test_filter_by_category(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test filtering expenses by category."""
        # Create expenses with different categories
        expense1 = Expense(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            category="Food & Dining",
            description="Food expense",
            date=datetime.now()
        )
        expense2 = Expense(
            user_id=test_user.id,
            amount=Decimal("200.00"),
            category="Shopping",
            description="Shopping expense",
            date=datetime.now()
        )
        db.add_all([expense1, expense2])
        db.commit()

        # Filter by Food
        response = authenticated_client.get("/expenses?category=Food")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["expenses"][0]["category"] == "Food & Dining"

    def test_sort_expenses(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test sorting expenses."""
        expense1 = Expense(
            user_id=test_user.id,
            amount=Decimal("50.00"),
            category="Food",
            description="Cheap",
            date=datetime.now()
        )
        expense2 = Expense(
            user_id=test_user.id,
            amount=Decimal("500.00"),
            category="Food",
            description="Expensive",
            date=datetime.now()
        )
        db.add_all([expense1, expense2])
        db.commit()

        # Sort by amount descending
        response = authenticated_client.get("/expenses?sort=amount_desc")
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["expenses"][0]["amount"]) > Decimal(data["expenses"][1]["amount"])

    def test_expense_summary(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test expense summary endpoint."""
        expense = Expense(
            user_id=test_user.id,
            amount=Decimal("150.00"),
            category="Food",
            description="Test",
            date=datetime.now()
        )
        db.add(expense)
        db.commit()

        response = authenticated_client.get("/expenses/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_expenses" in data
        assert "expense_count" in data
        assert "average_expense" in data
        assert "category_breakdown" in data
        assert "monthly_totals" in data

    def test_delete_expense(
        self, authenticated_client: TestClient, db: Session, test_user: User
    ):
        """Test deleting an expense."""
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

        # Verify deleted
        response = authenticated_client.get(f"/expenses/{expense_id}")
        assert response.status_code == 404

    def test_export_csv(self, authenticated_client: TestClient):
        """Test CSV export endpoint exists and returns CSV."""
        # First create an expense
        authenticated_client.post("/expenses", json={
            "amount": 100.00,
            "category": "Food",
            "description": "Export test",
            "date": "2026-01-31T12:00:00Z"
        })
        
        response = authenticated_client.get("/expenses/export")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]


class TestHealthCheck:
    """Test health endpoint."""

    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_swagger_docs(self, client: TestClient):
        """Test Swagger UI loads."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    def test_redoc(self, client: TestClient):
        """Test ReDoc loads."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()

