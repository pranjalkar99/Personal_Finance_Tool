"""User service for business logic."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service class for user operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username.lower()).first()

    def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Get user by username or email."""
        identifier = identifier.lower()
        return self.db.query(User).filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

    def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            email=user_data.email.lower(),
            username=user_data.username.lower(),
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, user_data: UserUpdate) -> User:
        """Update user profile."""
        update_data = user_data.model_dump(exclude_unset=True)
        
        if 'email' in update_data:
            update_data['email'] = update_data['email'].lower()
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username/email and password."""
        user = self.get_by_username_or_email(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_email_taken(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if email is already taken."""
        query = self.db.query(User).filter(User.email == email.lower())
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None

    def is_username_taken(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if username is already taken."""
        query = self.db.query(User).filter(User.username == username.lower())
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.first() is not None

    def deactivate(self, user: User) -> User:
        """Deactivate user account."""
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user

