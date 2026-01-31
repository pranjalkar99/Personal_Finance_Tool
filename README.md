# 💰 Expense Tracker

A **production-ready** full-stack personal finance tool for tracking expenses. Built with FastAPI, SQLAlchemy, and vanilla JavaScript.

## 🌐 Live Demo

**[https://personal-finance-tool-hhhs.vercel.app](https://personal-finance-tool-hhhs.vercel.app)**

```
Demo Account:
Username: verceltest
Password: TestPass123!
```

## ✨ Features

### Core Features
- ✅ User registration and authentication (JWT)
- ✅ Create, read, update, delete expenses
- ✅ Filter by category and date range
- ✅ Sort by date or amount
- ✅ Pagination support
- ✅ Full-text search
- ✅ Expense summary/analytics dashboard
- ✅ Export expenses to CSV
- ✅ Import expenses from CSV
- ✅ Idempotent API for safe retries

### Advanced Features
- ✅ **Budget Limits & Alerts** - Set monthly spending limits per category
- ✅ **Recurring Expenses** - Auto-generate daily/weekly/monthly/yearly expenses
- ✅ **Multiple Currencies** - Support for INR, USD, EUR, GBP, JPY
- ✅ **Tags/Labels** - Organize expenses with custom tags
- ✅ **Notes** - Add detailed notes to expenses
- ✅ **Attachments** - Store receipt URLs
- ✅ **Dark/Light Theme** - User preference toggle
- ✅ **Interactive Charts** - Spending analytics with Chart.js

### Production Features
- ✅ JWT authentication with refresh tokens
- ✅ Password hashing with bcrypt
- ✅ Input validation with Pydantic
- ✅ Comprehensive test suite
- ✅ Docker & Docker Compose support
- ✅ Vercel deployment ready
- ✅ PostgreSQL support
- ✅ Health check endpoint
- ✅ Structured logging
- ✅ CORS configuration

## 🏗️ Project Structure

```
Personal_Finance_Tool/
├── backend/
│   ├── api/
│   │   └── index.py           # Vercel serverless entry
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py      # Settings management
│   │   │   ├── security.py    # JWT & password utilities
│   │   │   ├── dependencies.py # FastAPI dependencies
│   │   │   └── logging_config.py # Logging setup
│   │   ├── middleware/
│   │   │   └── logging_middleware.py
│   │   ├── models/
│   │   │   ├── user.py        # User model
│   │   │   ├── expense.py     # Expense model
│   │   │   ├── budget.py      # Budget model
│   │   │   └── recurring.py   # Recurring expense model
│   │   ├── schemas/
│   │   │   ├── user.py        # User schemas
│   │   │   ├── expense.py     # Expense schemas
│   │   │   ├── budget.py      # Budget schemas
│   │   │   └── recurring.py   # Recurring schemas
│   │   ├── services/
│   │   │   ├── user_service.py
│   │   │   ├── expense_service.py
│   │   │   ├── budget_service.py
│   │   │   ├── recurring_service.py
│   │   │   ├── currency_service.py
│   │   │   └── import_service.py
│   │   ├── routers/
│   │   │   ├── auth.py        # Auth endpoints
│   │   │   ├── users.py       # User endpoints
│   │   │   ├── expenses.py    # Expense endpoints
│   │   │   ├── budgets.py     # Budget endpoints
│   │   │   └── recurring.py   # Recurring endpoints
│   │   ├── database.py
│   │   └── main.py
│   ├── templates/
│   │   └── index.html         # Frontend UI
│   ├── static/
│   │   ├── styles.css
│   │   └── app.js
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_expenses.py
│   │   └── test_services.py
│   └── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── vercel.json
├── DEPLOYMENT.md
└── README.md
```

## 🚀 Quick Start

### Option 1: Vercel (Recommended for Production)

1. Fork this repository
2. Go to [vercel.com](https://vercel.com) and import the repo
3. Add environment variables:
   - `DATABASE_URL` - PostgreSQL connection string (use [Neon](https://neon.tech) for free)
   - `SECRET_KEY` - Run `openssl rand -hex 32`
   - `DEBUG` - `false`
4. Deploy!

### Option 2: Docker

```bash
# Production
docker-compose up -d

# Development with hot-reload
docker-compose -f docker-compose.dev.yml up
```

Open http://localhost:8000

### Option 3: Local Development

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

## 🧪 Running Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## 📚 API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

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

### Expenses

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
  "currency": "INR",
  "tags": ["lunch", "work"],
  "notes": "Business lunch",
  "idempotency_key": "unique-key-123"
}
```

#### List Expenses with Search
```http
GET /expenses?search=lunch&category=Food&sort=date_desc&page=1&page_size=20
Authorization: Bearer <token>
```

#### Export CSV
```http
GET /expenses/export?start_date=2026-01-01&end_date=2026-01-31
Authorization: Bearer <token>
```

### Budgets

#### Create Budget
```http
POST /budgets
Authorization: Bearer <token>
Content-Type: application/json

{
  "category": "Food & Dining",
  "monthly_limit": 5000,
  "alert_threshold": 80
}
```

### Recurring Expenses

#### Create Recurring
```http
POST /recurring
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 500,
  "category": "Bills & Utilities",
  "description": "Internet bill",
  "frequency": "monthly",
  "day_of_month": 1,
  "start_date": "2026-02-01"
}
```

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Expense Tracker | Application name |
| `DEBUG` | false | Debug mode (enables /docs) |
| `DATABASE_URL` | sqlite:///./expenses.db | Database connection |
| `SECRET_KEY` | (required) | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `CORS_ORIGINS` | ["*"] | Allowed CORS origins |
| `JSON_LOGS` | false | Enable JSON logging |

## 🔒 Security Notes

For production deployment:
1. Generate a secure `SECRET_KEY`: `openssl rand -hex 32`
2. Use PostgreSQL instead of SQLite
3. Configure specific `CORS_ORIGINS`
4. Use HTTPS
5. Set `DEBUG=false`

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **Auth** | python-jose (JWT), passlib (bcrypt) |
| **Frontend** | Vanilla JS, Jinja2, Chart.js |
| **Database** | PostgreSQL / SQLite |
| **Deployment** | Docker, Vercel |
| **Testing** | Pytest, HTTPX |

## 📊 Features Breakdown

### Analytics Dashboard
- Total spending overview
- Month-over-month comparison
- Spending by category (pie chart)
- Monthly spending trend (line chart)
- Daily spending heatmap
- Category breakdown table

### Budget Management
- Set monthly limits per category
- Configurable alert thresholds
- Visual progress indicators
- Overspending warnings

### Recurring Expenses
- Daily, weekly, monthly, yearly frequencies
- Auto-generation of expenses
- Track execution history
- Enable/disable toggles

## 📄 License

MIT

---

**Built with ❤️ using FastAPI & Jinja2**
