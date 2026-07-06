"""FastAPI dependency injection — wires repositories, services, and auth."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories import (
    CarrierTokenRepository,
    RefreshTokenRepository,
    UserRepository,
)
from app.schemas import UserPayload
from app.services import (
    CarrierAuthService,
    RateService,
    UpsCarrierService,
    UserAuthService,
    UserService,
)

security = HTTPBearer()


# --- Repositories (one per request, share the same DB session) ---

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_refresh_token_repository(db: Session = Depends(get_db)) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


def get_carrier_token_repository(db: Session = Depends(get_db)) -> CarrierTokenRepository:
    return CarrierTokenRepository(db)


# --- Services (built from repositories / other services) ---
def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)


def get_user_auth_service(
    user_service: UserService = Depends(get_user_service),
    refresh_token_repository: RefreshTokenRepository = Depends(
        get_refresh_token_repository
    ),
) -> UserAuthService:
    return UserAuthService(user_service, refresh_token_repository)


def get_carrier_auth_service(
    repository: CarrierTokenRepository = Depends(get_carrier_token_repository),
) -> CarrierAuthService:
    return CarrierAuthService(repository)


def get_ups_carrier_service(
    carrier_auth_service: CarrierAuthService = Depends(get_carrier_auth_service),
) -> UpsCarrierService:
    return UpsCarrierService(carrier_auth_service)


def get_rate_service(
    ups_carrier_service: UpsCarrierService = Depends(get_ups_carrier_service),
) -> RateService:
    return RateService(ups_carrier_service)


# --- Auth ---
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserPayload:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if payload.get("type") != "access":
        # Refresh tokens are also JWTs but must not be used as Bearer tokens.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return UserPayload(
        id=payload["sub"],
        email=payload["email"],
        roles=payload.get("roles", []),
    )
