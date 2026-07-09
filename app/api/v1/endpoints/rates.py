"""Shipping rate quote endpoints."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_rate_service
from app.schemas import RateRequestSchema, RateResponseSchema, UserPayload
from app.services import RateService

router = APIRouter(prefix="/rates", tags=["Rates"])


@router.post(
    "/UPS",
    response_model=RateResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def get_ups_rates(
    body: RateRequestSchema,
    rate_service: RateService = Depends(get_rate_service),
    current_user: UserPayload = Depends(get_current_user),
):
    quotes = await rate_service.get_ups_rates(body, current_user.id)
    return RateResponseSchema(quotes=quotes, count=len(quotes))
