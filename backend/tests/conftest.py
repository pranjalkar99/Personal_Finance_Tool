"""Pytest fixtures for testing."""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User, Expense
from app.core.security import get_password_hash, create_access_token

# Test database URL - in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("Test123!"),
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Create an access token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def authenticated_client(client: TestClient, test_user_token: str) -> TestClient:
    """Create an authenticated test client."""
    client.headers["Authorization"] = f"Bearer {test_user_token}"
    return client


@pytest.fixture
def second_user(db: Session) -> User:
    """Create a second test user for isolation tests."""
    user = User(
        email="second@example.com",
        username="seconduser",
        hashed_password=get_password_hash("Test123!"),
        full_name="Second User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

