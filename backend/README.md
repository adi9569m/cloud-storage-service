# Cloud Storage Service - Backend API

FastAPI-powered RESTful backend API for the Cloud Storage Service.

## Directory Structure

```
backend/
├── app/
│   ├── core/               # Configuration, security constants, and database session setup
│   │   ├── __init__.py
│   │   ├── config.py       # Pydantic Settings loaded from environment
│   │   └── database.py     # SQLAlchemy 2.0 engine, Base, and session factory
│   │
│   ├── models/             # SQLAlchemy 2.0 ORM Declarative Models
│   │   ├── __init__.py     # Re-exports all models
│   │   ├── base.py         # TimestampMixin and UUID Base setup
│   │   ├── user.py         # User entity
│   │   ├── folder.py       # Folder entity (recursive hierarchy)
│   │   ├── file.py         # File metadata entity
│   │   ├── file_version.py # File versions entity
│   │   ├── share.py        # Granular user-to-user share entity
│   │   ├── link_share.py   # Public token link share entity
│   │   ├── star.py         # Starred/favorite files & folders
│   │   └── activity.py     # Audit activity log entity
│   │
│   ├── schemas/            # Pydantic validation schemas
│   │   └── __init__.py
│   │
│   ├── routes/             # FastAPI APIRouters
│   │   └── __init__.py
│   │
│   ├── services/           # Business logic & external integrations
│   │   └── __init__.py
│   │
│   ├── utils/              # Helper functions
│   │   └── __init__.py
│   │
│   ├── __init__.py
│   └── main.py             # FastAPI entrypoint with CORS and health check
│
├── requirements.txt        # Backend dependencies
├── .env.example            # Environment configuration template
└── README.md               # Backend documentation
```

---

## Local Setup & Development

### 1. Create and Activate Virtual Environment
```bash
python -m venv .venv

# On Windows:
.venv\Scripts\Activate.ps1

# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your PostgreSQL/Supabase credentials
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. API Documentation
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)
