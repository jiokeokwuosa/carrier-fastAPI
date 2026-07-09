# Carrier API (FastAPI)

FastAPI port of the NestJS shipping rate service at `/Users/cj/Projects/carrier`.

## Features

- **UPS rate quotes** — `POST /rates/UPS` (quotes are persisted for analytics)
- **UPS OAuth token management** — client-credentials flow with Redis + DB cache
- **User authentication** — JWT access tokens (with `exp`) + refresh token rotation
- **User registration** — `POST /users/register` (public)
- **Admin dashboard** — `GET /users/stats` (JOIN + aggregation queries)
- **Alembic migrations** — versioned schema changes

## Project structure

```
carrier-fastapi/
├── app/
│   ├── main.py
│   ├── core/           # config, database, security, exceptions
│   ├── models/         # SQLAlchemy models (normalized roles, rate quotes)
│   ├── schemas/        # Pydantic request/response models
│   ├── repositories/   # database access layer (+ advanced SQL)
│   ├── services/       # business logic (+ optional Redis cache)
│   ├── carriers/       # carrier interface + UPS implementation
│   └── api/
│       ├── deps.py     # FastAPI dependencies
│       └── v1/endpoints/
├── alembic/            # database migrations
├── tests/
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd /Users/cj/Projects/carrier-fastapi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABASE_URL and UPS credentials
```

### Database migrations

```bash
alembic upgrade head    # apply all migrations
alembic revision --autogenerate -m "describe_change"  # after model changes
```

## Run

```bash
uvicorn main:app --reload --port 3000
```

Docs: http://localhost:3000/docs

## API endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | Public | Login with email/password |
| POST | `/auth/refresh` | Public | Refresh access token |
| GET | `/auth/me` | JWT | Current user profile |
| POST | `/users/register` | Public | Register new user |
| GET | `/users/stats` | Admin JWT | User & quote statistics |
| POST | `/rates/UPS` | JWT | Get UPS shipping quotes |

## Database concepts in this project

| Concept | Where to look |
|---------|---------------|
| **Normalization (3NF)** | `app/models/role.py` — roles in their own table; `user_roles` association |
| **SQLAlchemy relationships** | `User.roles`, `User.rate_quotes`, `RefreshToken.user` |
| **Indexes** | `RefreshToken.__table_args__`, `RateQuoteRecord.__table_args__` |
| **JOIN + GROUP BY + aggregations** | `app/repositories/user_stats_repository.py` |
| **Alembic migrations** | `alembic/versions/` — run `alembic upgrade head` |
| **Connection pooling** | `app/core/database.py` — `pool_size`, `pool_pre_ping`, `pool_recycle` |
| **Redis caching** | `app/services/cache_service.py` + `carrier_auth_service.py` |
| **Query optimization (eager loading)** | `selectinload` in `user_repository.py`, `joinedload` in `refresh_token_repository.py` |
| **Data modeling for analytics** | `app/models/rate_quote.py` — persisted quote history |
| **JWT with expiration** | `app/core/security.py` — `exp` and `iat` claims |

## Tests

```bash
pytest -v
```

Uses SQLite test database with mocked UPS HTTP calls.

## API conventions

- Request/response bodies use **camelCase** (Pydantic `alias` fields)
- Carrier OAuth and user JWT are separate concerns
- `POST /rates/UPS` returns `201 Created`

### Error responses

FastAPI standard `detail` format:

- **Validation errors** (`422`): `{"detail": [{"type": "...", "loc": [...], "msg": "..."}]}`
- **HTTP errors** (e.g. `401`, `409`): `{"detail": "..."}` or `{"detail": {...}}`
- **Carrier errors** (e.g. `400`, `503`): `{"detail": {"code": "...", "message": "...", "details": {...}}}`
