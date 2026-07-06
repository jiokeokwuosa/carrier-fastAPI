"""Pytest fixtures — env vars must be set before app imports (see get_settings)."""

import os

# Required before importing app modules that call get_settings() at import time.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("UPS_API_BASE_URL", "https://wwwcie.ups.com")
os.environ.setdefault("UPS_USERNAME", "test_user")
os.environ.setdefault("UPS_PASSWORD", "test_pass")
os.environ.setdefault("JWT_ACCESS_SECRET", "test-secret-key")
os.environ.setdefault("JWT_ACCESS_EXPIRES", "15m")
os.environ.setdefault("JWT_REFRESH_DAYS", "7")

from app.core.config import get_settings

get_settings.cache_clear()

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine, init_db
from app.core.security import hash_password
from app.main import app
from app.models import User, UserRole

VALID_RATE_REQUEST = {
    "origin": {"addressLine": ["123 Main St"], "countryCode": "US"},
    "destination": {"addressLine": ["456 Oak Ave"], "countryCode": "US"},
    "package": {
        "dimensions": {
            "unitOfMeasurement": {"code": "IN", "description": "Inches"},
            "length": "5",
            "width": "5",
            "height": "5",
        },
        "packageWeight": {
            "unitOfMeasurement": {"code": "LBS", "description": "Pounds"},
            "weight": "1",
        },
    },
}

MOCK_UPS_RATE_RESPONSE = {
    "RateResponse": {
        "Response": {"ResponseStatus": {"Code": "1", "Description": "success"}},
        "RatedShipment": [
            {
                "Service": {"Code": "03", "Description": "Ground"},
                "BillingWeight": {
                    "UnitOfMeasurement": {"Code": "LBS", "Description": "Pounds"},
                    "Weight": "1",
                },
                "TransportationCharges": {"CurrencyCode": "USD", "MonetaryValue": "10.50"},
                "TotalCharges": {"CurrencyCode": "USD", "MonetaryValue": "12.00"},
                "TotalChargesWithTaxes": {"CurrencyCode": "USD", "MonetaryValue": "12.50"},
            }
        ],
    }
}


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()
    db.add(
        User(
            email="admin@test.com",
            password_hash=hash_password("password123"),
            roles=[UserRole.USER.value],
        )
    )
    db.commit()
    db.close()
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "password123"},
    )
    token = response.json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}
