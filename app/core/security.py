"""Password hashing and JWT / refresh-token utilities."""

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(payload: Dict[str, Any]) -> str:
    return jwt.encode(payload, settings.JWT_ACCESS_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=[ALGORITHM])


def generate_refresh_token() -> str:
    # Opaque random token returned to the client (not a JWT).
    return secrets.token_hex(32)


def hash_refresh_token(token: str) -> str:
    # Only the hash is stored in the database so a DB leak cannot replay tokens.
    return hashlib.sha256(token.encode()).hexdigest()


def parse_expires_to_seconds(expires: str) -> int:
    # Parses values like "15m", "1h", "30s" from JWT_ACCESS_EXPIRES.
    match = re.match(r"^(\d+)([smh])$", expires)
    if not match:
        return 900  # default 15 minutes
    value = int(match.group(1))
    unit = match.group(2)
    if unit == "s":
        return value
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    return 900


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_DAYS)
