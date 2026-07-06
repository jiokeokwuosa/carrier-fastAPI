"""Thin facade over carrier implementations (currently UPS only)."""

from typing import List

from app.schemas import RateQuoteSchema, RateRequestSchema
from app.services.ups_carrier_service import UpsCarrierService


class RateService:
    """Application-level rate quoting — delegates to carrier-specific services."""

    def __init__(self, ups_carrier_service: UpsCarrierService):
        self.ups_carrier_service = ups_carrier_service

    def get_ups_rates(self, request: RateRequestSchema) -> List[RateQuoteSchema]:
        return self.ups_carrier_service.get_rates(request)
