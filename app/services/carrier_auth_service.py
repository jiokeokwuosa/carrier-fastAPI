"""UPS OAuth client-credentials flow with DB-backed token cache."""

import base64
import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.core.exceptions import AuthenticationError, NetworkError, TimeoutError
from app.repositories import CarrierTokenRepository

logger = logging.getLogger(__name__)


class CarrierAuthService:
    """Manages UPS OAuth client-credentials tokens stored in the database."""

    def __init__(self, repository: CarrierTokenRepository):
        self.repository = repository

    def return_access_token(self, platform: str) -> str:
        logger.warning("Getting %s API access token...", platform)
        token = self.repository.find_by_platform(platform)
        if token is None:
            logger.info("No token found for %s, acquiring new token...", platform)
            return self.acquire_token(platform)

        issued_at = int(token.issued_at)
        expires_in = int(token.expires_in)
        # UPS returns issued_at in milliseconds; expires_in is in seconds.
        expiration_time = issued_at + expires_in * 1000
        if self._current_time_ms() >= expiration_time:
            logger.info("Current token for %s has expired, refreshing...", platform)
            return self.acquire_token(platform)

        return token.access_token

    def acquire_token(self, platform: str) -> str:
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
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
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

        self.repository.upsert(
            platform=platform,
            token_type=data["token_type"],
            issued_at=data["issued_at"],
            client_id=data["client_id"],
            access_token=data["access_token"],
            expires_in=data["expires_in"],
        )
        logger.info("Successfully acquired token for %s", platform)
        return data["access_token"]

    @staticmethod
    def _current_time_ms() -> int:
        import time

        return int(time.time() * 1000)
