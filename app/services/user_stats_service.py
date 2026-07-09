"""Admin dashboard statistics built from advanced SQL queries."""

from app.repositories import UserStatsRepository
from app.schemas import UserStatsResponse


class UserStatsService:
    def __init__(self, repository: UserStatsRepository):
        self.repository = repository

    async def get_dashboard(self) -> UserStatsResponse:
        stats = await self.repository.get_dashboard_stats()
        return UserStatsResponse(**stats)
