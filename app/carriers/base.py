"""Abstract carrier interface — extend for FedEx, DHL, etc."""

from abc import ABC, abstractmethod
from typing import List

from app.schemas import RateQuoteSchema, RateRequestSchema


class Carrier(ABC):
    @abstractmethod
    def get_platform(self) -> str:
        pass

    @abstractmethod
    async def get_rates(self, request: RateRequestSchema) -> List[RateQuoteSchema]:
        pass
