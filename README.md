# Carrier API (FastAPI)

FastAPI port of the NestJS shipping rate service at `/Users/cj/Projects/carrier`.

## Features

- **UPS rate quotes** — `POST /rates/UPS`
- **UPS OAuth token management** — client-credentials flow with DB-backed token cache
- **User authentication** — JWT access tokens + refresh token rotation
- **User registration** — `POST /users/register` (public)

## Project structure

```
carrier-fastapi/
├── app/
│   ├── main.py
│   ├── core/           # config, database, security, exceptions
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic request/response models
│   ├── repositories/   # database access layer
│   ├── services/       # business logic
│   ├── carriers/       # carrier interface + UPS implementation
│   └── api/
│       ├── deps.py     # FastAPI dependencies
│       └── v1/endpoints/
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
| POST | `/rates/UPS` | JWT | Get UPS shipping quotes |

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
