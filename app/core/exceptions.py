"""Domain exceptions for carrier/UPS integration.

Raised in services and handled globally in app.main (CarrierError handler).
User-auth errors use HTTPException instead.
"""

from typing import Any, Optional


class CarrierError(Exception):
    """Base for UPS/carrier failures mapped to HTTP error responses."""

    def __init__(
        self,
        message: str,
        status_code: int,
        code: str,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class AuthenticationError(CarrierError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, 401, "AUTH_ERROR", details)


class RateRequestError(CarrierError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, 400, "RATE_REQUEST_ERROR", details)


class NetworkError(CarrierError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, 503, "NETWORK_ERROR", details)


class TimeoutError(CarrierError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, 504, "TIMEOUT_ERROR", details)
