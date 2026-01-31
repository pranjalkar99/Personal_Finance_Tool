# Expense Tracker

A **production-ready** full-stack personal finance tool for tracking expenses. Built with FastAPI, SQLAlchemy, and vanilla JavaScript.

## Features

### Core Features
- ✅ User registration and authentication (JWT)
- ✅ Create, read, update, delete expenses
- ✅ Filter by category and date range
- ✅ Sort by date or amount
- ✅ Pagination support
- ✅ Expense summary/analytics dashboard
- ✅ Export expenses to CSV
- ✅ Idempotent API for safe retries

### Production Features
- ✅ JWT authentication with refresh tokens
- ✅ Password hashing with bcrypt
- ✅ Input validation with Pydantic
- ✅ Comprehensive test suite
- ✅ Docker & Docker Compose support
- ✅ Health check endpoint
- ✅ CORS configuration
- ✅ Environment-based configuration

## Project Structure

```
Personal_Finance_Tool/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py      # Settings management
│   │   │   ├── security.py    # JWT & password utilities
│   │   │   └── dependencies.py # FastAPI dependencies
│   │   ├── models/
│   │   │   ├── user.py        # User model
│   │   │   └── expense.py     # Expense model
│   │   ├── schemas/
│   │   │   ├── user.py        # User schemas
│   │   │   └── expense.py     # Expense schemas
│   │   ├── services/
│   │   │   ├── user_service.py    # User business logic
│   │   │   └── expense_service.py # Expense business logic
│   │   ├── routers/
│   │   │   ├── auth.py        # Auth endpoints
│   │   │   ├── users.py       # User endpoints
│   │   │   └── expenses.py    # Expense endpoints
│   │   ├── database.py
│   │   └── main.py
│   ├── templates/
│   │   └── index.html
│   ├── static/
│   │   ├── styles.css
│   │   └── app.js
│   ├── tests/
│   │   ├── conftest.py        # Test fixtures
│   │   ├── test_auth.py       # Auth tests
│   │   ├── test_expenses.py   # Expense tests
│   │   └── test_services.py   # Service tests
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pytest.ini
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
└── README.md
```

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Production
docker-compose up -d

# Development with hot-reload
docker-compose -f docker-compose.dev.yml up
```

Open http://localhost:8000

### Option 2: Local Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

Open http://localhost:8000

## Running Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Authentication

#### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Expenses (Authenticated)

#### Create Expense
```http
POST /expenses
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 150.50,
  "category": "Food & Dining",
  "description": "Lunch at restaurant",
  "date": "2026-01-31T12:00:00Z",
  "idempotency_key": "unique-key"
}
```

#### List Expenses
```http
GET /expenses?category=Food&sort=date_desc&page=1&page_size=20
Authorization: Bearer <token>
```

#### Get Summary
```http
GET /expenses/summary?year=2026
Authorization: Bearer <token>
```

#### Export CSV
```http
GET /expenses/export?start_date=2026-01-01&end_date=2026-01-31
Authorization: Bearer <token>
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Expense Tracker | Application name |
| `DEBUG` | false | Debug mode |
| `DATABASE_URL` | sqlite:///./expenses.db | Database connection URL |
| `SECRET_KEY` | (required) | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `CORS_ORIGINS` | ["*"] | Allowed CORS origins |

## Security Notes

For production deployment:
1. Generate a secure `SECRET_KEY`: `openssl rand -hex 32`
2. Use PostgreSQL instead of SQLite
3. Configure specific `CORS_ORIGINS`
4. Use HTTPS
5. Set `DEBUG=false`

## Tech Stack

- **FastAPI** - Modern async Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation
- **python-jose** - JWT handling
- **passlib** - Password hashing
- **Jinja2** - Template engine
- **Pytest** - Testing framework
- **Docker** - Containerization

## License

MIT
