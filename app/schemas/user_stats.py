"""Pydantic schemas for user statistics (admin dashboard)."""

from typing import Dict, List

from app.schemas.auth import CamelModel


class CarrierQuoteStats(CamelModel):
    carrier: str
    quote_count: int
    avg_total_charges: float


class UserStatsResponse(CamelModel):
    total_users: int
    users_by_role: Dict[str, int]
    active_refresh_tokens: int
    total_rate_quotes: int
    quotes_by_carrier: List[CarrierQuoteStats]
