"""API routers."""

from app.routers.auth import router as auth_router
from app.routers.expenses import router as expenses_router
from app.routers.users import router as users_router
from app.routers.budgets import router as budgets_router

__all__ = ["auth_router", "expenses_router", "users_router", "budgets_router"]
