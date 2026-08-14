# BachNest Backend — Modular Monolith MVP Foundation

BachNest is a trusted, two-sided rental lifecycle management platform designed for the Bangladesh bachelor rental market. It bridges the trust gap between bachelors and property owners through verified identity (KYC), structured inventory management, PostGIS radius search, digital agreements, monthly invoicing, maintenance complaint ticketing, and real-time emergency SOS.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database & ORM**: PostgreSQL 16 + PostGIS, SQLAlchemy 2.x (Async), Alembic migrations
- **Cache & Message Broker**: Redis 7
- **Background Worker**: Celery
- **Security**: Argon2id password hashing, JWT (Access & Refresh tokens), Role-Based Access Control (RBAC)
- **Geospatial**: GeoAlchemy2 & Shapely (SRID 4326)
- **Containerization**: Docker & Docker Compose

---

## 📂 Project Architecture

```text
backend/
├── app/
│   ├── main.py                         # FastAPI App & Lifespan Configuration
│   ├── api/
│   │   ├── deps.py                     # DB, Redis, Auth & RBAC Dependencies
│   │   └── v1/
│   │       ├── router.py               # Aggregated V1 API Router
│   │       └── endpoints/              # Endpoint Handlers
│   │           ├── health.py           # /health, /health/db, /health/redis
│   │           ├── auth.py             # Register, Login, Refresh, Logout
│   │           ├── users.py            # User profiles
│   │           ├── kyc.py              # KYC submissions & status
│   │           ├── properties.py       # Property listings & management
│   │           ├── rooms.py            # Room and seat inventory
│   │           ├── search.py           # Property & Map radius search
│   │           ├── bookings.py         # Booking workflow & owner approvals
│   │           ├── tenancies.py        # Active rental agreements & notice
│   │           ├── billing.py          # Invoices & utility breakdown
│   │           ├── payments.py         # Payment checkout & webhook
│   │           ├── complaints.py       # Maintenance ticketing & SLA
│   │           ├── emergency.py        # SOS emergency alerts
│   │           └── admin.py            # Moderation & stats
│   │
│   ├── core/
│   │   ├── config.py                   # Pydantic BaseSettings (.env loader)
│   │   ├── constants.py                # Enums, roles, statuses & SLA constants
│   │   ├── exceptions.py               # Typed exceptions & uniform JSON error handlers
│   │   ├── logging.py                  # Structured logging
│   │   └── security.py                 # Argon2id hashing & JWT encode/decode
│   │
│   ├── db/
│   │   ├── base.py                     # DeclarativeBase, UUIDPrimaryKeyMixin, TimestampMixin
│   │   └── session.py                  # Async SQLAlchemy Engine & Session Factory
│   │
│   ├── models/                         # 17 Domain SQLAlchemy Models
│   │   ├── user.py                     # User entity
│   │   ├── kyc.py                      # UserKYC, RoommatePreference, EmergencyContact
│   │   ├── property.py                 # Property entity
│   │   ├── room.py                     # Room, RoomSeat, PropertyMedia
│   │   ├── booking.py                  # Booking, Tenancy
│   │   ├── invoice.py                  # Invoice, Payment
│   │   ├── complaint.py                # Complaint, Notice, NoticeRead
│   │   └── emergency.py                # EmergencyAlert, Review, Notification, AuditLog
│   │
│   ├── schemas/                        # Pydantic Request/Response Models
│   │   ├── common.py                   # Standard API Envelope & Pagination
│   │   ├── auth.py
│   │   ├── kyc.py
│   │   ├── property.py
│   │   └── booking.py
│   │
│   ├── integrations/                   # External adapters & mock providers
│   │   ├── storage/local_storage.py
│   │   ├── payments/mock_gateway.py
│   │   ├── sms/mock_sms.py
│   │   └── kyc/mock_kyc.py
│   │
│   ├── websockets/
│   │   └── connection_manager.py       # Real-time WebSocket connection manager
│   │
│   └── workers/
│       └── celery_app.py               # Celery worker configuration
│
├── alembic/                            # Database migrations
│   ├── env.py
│   └── script.py.mako
│
├── tests/                              # Automated Pytest Suite
│   ├── conftest.py
│   └── unit/
│       ├── test_health.py
│       └── test_security.py
│
├── .env.example                        # Configuration template
├── Dockerfile                          # Production-ready container image
├── docker-compose.yml                  # Postgres (PostGIS) + Redis + API + Celery
├── requirements.txt                    # Project dependencies
└── pyproject.toml                      # Pytest configuration
```

---

## 🚀 Getting Started

### 1. Local Environment Setup

Activate your virtual environment and install dependencies:

```powershell
# In PowerShell:
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env` file (copied from `.env.example`):

```powershell
Copy-Item .env.example .env
```

### 3. Running the Server Locally

```powershell
uvicorn app.main:app --reload --port 8000
```

- **Swagger UI Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Interactive Docs**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## 🐳 Running with Docker Compose

To spin up the entire stack (FastAPI, PostgreSQL with PostGIS, Redis, and Celery Worker):

```bash
docker-compose up --build
```

---

## 🧪 Running Automated Tests

```powershell
pytest -v
```

---

## 🔒 Standard API Response Format

All responses follow the unified format:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Validation failed",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "field": "phone",
        "message": "Phone number must be a valid Bangladesh number"
      }
    ]
  }
}
```
