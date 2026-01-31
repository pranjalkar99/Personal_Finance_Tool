"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.database import create_tables
from app.routers import auth_router, expenses_router, users_router, budgets_router, recurring_router
from app.middleware.logging_middleware import RequestLoggingMiddleware

# Setup logging
JSON_LOGS = os.getenv("JSON_LOGS", "false").lower() == "true"
setup_logging(debug=settings.DEBUG, json_logs=JSON_LOGS)
logger = get_logger("main")

# Get the backend directory path
BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"   Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"   Database: {settings.DATABASE_URL[:50]}...")
    create_tables()
    logger.info("✅ Database tables created/verified")
    yield
    # Shutdown
    logger.info("👋 Shutting down application")


app = FastAPI(
    title=settings.APP_NAME,
    description="A production-ready personal finance tool for tracking expenses",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with better formatting."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Setup templates
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Include API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(expenses_router)
app.include_router(budgets_router)
app.include_router(recurring_router)


@app.get("/", include_in_schema=False)
async def index(request: Request):
    """Serve the main frontend page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }
