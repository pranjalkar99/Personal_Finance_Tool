"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User


class TestRegister:
    """Tests for user registration."""

    def test_register_success(self, client: TestClient):
        """Test successful user registration."""
        response = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "NewUser123!",
            "full_name": "New User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with existing email."""
        response = client.post("/auth/register", json={
            "email": test_user.email,
            "username": "differentuser",
            "password": "Test123!",
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """Test registration with existing username."""
        response = client.post("/auth/register", json={
            "email": "different@example.com",
            "username": test_user.username,
            "password": "Test123!",
        })
        
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password."""
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",
        })
        
        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email."""
        response = client.post("/auth/register", json={
            "email": "invalid-email",
            "username": "testuser",
            "password": "Test123!",
        })
        
        assert response.status_code == 422


class TestLogin:
    """Tests for user login."""

    def test_login_with_username(self, client: TestClient, test_user: User):
        """Test login with username."""
        response = client.post("/auth/login", json={
            "username": test_user.username,
            "password": "Test123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_email(self, client: TestClient, test_user: User):
        """Test login with email."""
        response = client.post("/auth/login", json={
            "username": test_user.email,
            "password": "Test123!"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = client.post("/auth/login", json={
            "username": test_user.username,
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "Test123!"
        })
        
        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db: Session, test_user: User):
        """Test login with inactive user."""
        test_user.is_active = False
        db.commit()
        
        response = client.post("/auth/login", json={
            "username": test_user.username,
            "password": "Test123!"
        })
        
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]


class TestTokenRefresh:
    """Tests for token refresh."""

    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test successful token refresh."""
        # First login to get tokens
        login_response = client.post("/auth/login", json={
            "username": test_user.username,
            "password": "Test123!"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh the token
        response = client.post("/auth/refresh", params={"refresh_token": refresh_token})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post("/auth/refresh", params={"refresh_token": "invalid"})
        
        assert response.status_code == 401

