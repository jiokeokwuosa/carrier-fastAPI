"""Thin facade over carrier implementations (currently UPS only)."""

from typing import List

from app.repositories import RateQuoteRepository
from app.schemas import RateQuoteSchema, RateRequestSchema
from app.services.ups_carrier_service import UpsCarrierService


class RateService:
    """Application-level rate quoting — delegates to carrier-specific services."""

    def __init__(
        self,
        ups_carrier_service: UpsCarrierService,
        rate_quote_repository: RateQuoteRepository,
    ):
        self.ups_carrier_service = ups_carrier_service
        self.rate_quote_repository = rate_quote_repository

    async def get_ups_rates(
        self, request: RateRequestSchema, user_id: str
    ) -> List[RateQuoteSchema]:
        quotes = await self.ups_carrier_service.get_rates(request)
        await self.rate_quote_repository.create_batch(user_id, "UPS", request, quotes)
        return quotes
