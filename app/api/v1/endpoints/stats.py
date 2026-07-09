"""Admin statistics endpoints — demonstrates JOIN + aggregation queries."""

from fastapi import APIRouter, Depends

from app.api.deps import get_user_stats_service, require_admin
from app.schemas import UserPayload, UserStatsResponse
from app.services import UserStatsService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    _: UserPayload = Depends(require_admin),
    stats_service: UserStatsService = Depends(get_user_stats_service),
):
    return await stats_service.get_dashboard()
