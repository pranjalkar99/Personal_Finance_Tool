"""User profile API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService
from app.core.dependencies import CurrentUser

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
def get_current_user_profile(
    current_user: CurrentUser
) -> UserResponse:
    """Get the currently authenticated user's profile."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile"
)
def update_current_user_profile(
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> UserResponse:
    """Update the currently authenticated user's profile."""
    user_service = UserService(db)
    
    # Check if new email is taken
    if user_data.email and user_service.is_email_taken(user_data.email, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use"
        )
    
    updated_user = user_service.update(current_user, user_data)
    return updated_user


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate current user account"
)
def deactivate_account(
    current_user: CurrentUser,
    db: Session = Depends(get_db)
) -> None:
    """Deactivate the currently authenticated user's account."""
    user_service = UserService(db)
    user_service.deactivate(current_user)

