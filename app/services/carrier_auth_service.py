"""UPS OAuth client-credentials flow with Redis + DB-backed token cache."""

import base64
import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.core.exceptions import AuthenticationError, NetworkError, TimeoutError
from app.repositories import CarrierTokenRepository
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

_CARRIER_TOKEN_PREFIX = "carrier_token:"


class CarrierAuthService:
    """Manages UPS OAuth client-credentials tokens with layered caching.

    Lookup order: Redis (hot) → PostgreSQL (durable) → UPS API (cold).
    """

    def __init__(
        self,
        repository: CarrierTokenRepository,
        cache: CacheService,
    ):
        self.repository = repository
        self.cache = cache

    async def return_access_token(self, platform: str) -> str:
        logger.warning("Getting %s API access token...", platform)
        cache_key = f"{_CARRIER_TOKEN_PREFIX}{platform}"

        cached = await self.cache.get(cache_key)
        if cached and not self._is_expired(cached["issued_at"], cached["expires_in"]):
            return cached["access_token"]

        token = await self.repository.find_by_platform(platform)
        if token is None:
            logger.info("No token found for %s, acquiring new token...", platform)
            return await self.acquire_token(platform)

        if self._is_expired(token.issued_at, token.expires_in):
            logger.info("Current token for %s has expired, refreshing...", platform)
            return await self.acquire_token(platform)

        await self._write_cache(
            cache_key, token.issued_at, token.expires_in, token.access_token
        )
        return token.access_token

    async def acquire_token(self, platform: str) -> str:
        if platform != "UPS":
            raise AuthenticationError(
                f"Token acquisition not implemented for platform: {platform}"
            )

        if not settings.UPS_USERNAME or not settings.UPS_PASSWORD:
            raise AuthenticationError("UPS credentials not configured")

        auth_header = base64.b64encode(
            f"{settings.UPS_USERNAME}:{settings.UPS_PASSWORD}".encode()
        ).decode()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    settings.ups_oauth_url,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "x-merchant-id": settings.UPS_MERCHANT_ID,
                        "Authorization": f"Basic {auth_header}",
                    },
                    data={"grant_type": "client_credentials"},
                )
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Token acquisition timeout for {platform}") from exc
        except httpx.RequestError as exc:
            raise NetworkError(
                f"Network error during token acquisition: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise AuthenticationError(
                f"Failed to acquire token: {response.status_code} {response.reason_phrase}",
                {"response": response.text},
            )

        data = response.json()
        if data.get("status") != "approved":
            raise AuthenticationError(
                f"Token acquisition not approved: {data.get('status')}"
            )

        await self.repository.upsert(
            platform=platform,
            token_type=data["token_type"],
            issued_at=data["issued_at"],
            client_id=data["client_id"],
            access_token=data["access_token"],
            expires_in=data["expires_in"],
        )
        cache_key = f"{_CARRIER_TOKEN_PREFIX}{platform}"
        await self._write_cache(
            cache_key, data["issued_at"], data["expires_in"], data["access_token"]
        )
        logger.info("Successfully acquired token for %s", platform)
        return data["access_token"]

    async def _write_cache(
        self, key: str, issued_at: str, expires_in: str, access_token: str
    ) -> None:
        ttl = max(int(expires_in) - 60, 60)
        await self.cache.set(
            key,
            {"issued_at": issued_at, "expires_in": expires_in, "access_token": access_token},
            ttl_seconds=ttl,
        )

    @staticmethod
    def _is_expired(issued_at: str, expires_in: str) -> bool:
        expiration_time = int(issued_at) + int(expires_in) * 1000
        return CarrierAuthService._current_time_ms() >= expiration_time

    @staticmethod
    def _current_time_ms() -> int:
        import time

        return int(time.time() * 1000)
