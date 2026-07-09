"""FastAPI dependency injection — wires repositories, services, and auth."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import UserRole
from app.repositories import (
    CarrierTokenRepository,
    RateQuoteRepository,
    RefreshTokenRepository,
    UserRepository,
    UserStatsRepository,
)
from app.schemas import UserPayload
from app.services import (
    CacheService,
    CarrierAuthService,
    RateService,
    UpsCarrierService,
    UserAuthService,
    UserService,
    UserStatsService,
)

security = HTTPBearer()

_cache_service = CacheService()


async def init_cache() -> None:
    await _cache_service.connect()


async def shutdown_cache() -> None:
    await _cache_service.close()


def get_cache_service() -> CacheService:
    return _cache_service


# --- Repositories (one per request, share the same DB session) ---

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_refresh_token_repository(
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


def get_carrier_token_repository(
    db: AsyncSession = Depends(get_db),
) -> CarrierTokenRepository:
    return CarrierTokenRepository(db)


def get_rate_quote_repository(db: AsyncSession = Depends(get_db)) -> RateQuoteRepository:
    return RateQuoteRepository(db)


def get_user_stats_repository(
    db: AsyncSession = Depends(get_db),
) -> UserStatsRepository:
    return UserStatsRepository(db)


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
    return CarrierAuthService(repository, _cache_service)


def get_ups_carrier_service(
    carrier_auth_service: CarrierAuthService = Depends(get_carrier_auth_service),
) -> UpsCarrierService:
    return UpsCarrierService(carrier_auth_service)


def get_rate_service(
    ups_carrier_service: UpsCarrierService = Depends(get_ups_carrier_service),
    rate_quote_repository: RateQuoteRepository = Depends(get_rate_quote_repository),
) -> RateService:
    return RateService(ups_carrier_service, rate_quote_repository)


def get_user_stats_service(
    repository: UserStatsRepository = Depends(get_user_stats_repository),
) -> UserStatsService:
    return UserStatsService(repository)


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return UserPayload(
        id=payload["sub"],
        email=payload["email"],
        roles=payload.get("roles", []),
    )


def require_admin(
    current_user: UserPayload = Depends(get_current_user),
) -> UserPayload:
    if UserRole.ADMIN.value not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
