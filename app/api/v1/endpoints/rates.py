"""Shipping rate quote endpoints."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_rate_service
from app.schemas import RateRequestSchema, RateResponseSchema, UserPayload
from app.services import RateService

router = APIRouter(prefix="/rates", tags=["Rates"])


@router.post(
    "/UPS",
    response_model=RateResponseSchema,
    status_code=status.HTTP_201_CREATED,  # 201 when quotes are successfully created
)
def get_ups_rates(
    body: RateRequestSchema,
    rate_service: RateService = Depends(get_rate_service),
    _: UserPayload = Depends(get_current_user),
):
    # CarrierError subclasses propagate to the global handler in app.main.
    quotes = rate_service.get_ups_rates(body)
    return RateResponseSchema(quotes=quotes, count=len(quotes))
