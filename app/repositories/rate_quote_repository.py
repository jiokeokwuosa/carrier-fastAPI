"""Database access for persisted rate quote history."""

from decimal import Decimal
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RateQuoteRecord
from app.schemas import RateQuoteSchema, RateRequestSchema


class RateQuoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_batch(
        self,
        user_id: str,
        carrier: str,
        request: RateRequestSchema,
        quotes: List[RateQuoteSchema],
    ) -> None:
        for quote in quotes:
            record = RateQuoteRecord(
                user_id=user_id,
                carrier=carrier,
                service_code=quote.service.code,
                service_name=quote.service.description,
                total_charges=Decimal(quote.total_charges.monetary_value),
                currency=quote.total_charges.currency_code,
                origin_country=request.origin.country_code,
                destination_country=request.destination.country_code,
            )
            self.db.add(record)
        await self.db.commit()
