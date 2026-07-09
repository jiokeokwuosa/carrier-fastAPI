"""Advanced SQL queries — joins, aggregations, and grouped statistics."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RateQuoteRecord, RefreshToken, Role, User, user_roles


class UserStatsRepository:
    """Demonstrates JOIN + GROUP BY + aggregate functions in SQLAlchemy 2.0 style."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)

        total_users = await self.db.scalar(select(func.count()).select_from(User)) or 0

        role_rows = (
            await self.db.execute(
                select(Role.name, func.count(user_roles.c.user_id))
                .join(user_roles, Role.id == user_roles.c.role_id)
                .group_by(Role.name)
                .order_by(Role.name)
            )
        ).all()
        users_by_role = {name: count for name, count in role_rows}

        active_tokens = (
            await self.db.scalar(
                select(func.count())
                .select_from(RefreshToken)
                .where(RefreshToken.expires_at > now)
            )
            or 0
        )

        quote_rows = (
            await self.db.execute(
                select(
                    RateQuoteRecord.carrier,
                    func.count(RateQuoteRecord.id),
                    func.avg(RateQuoteRecord.total_charges),
                )
                .group_by(RateQuoteRecord.carrier)
                .order_by(RateQuoteRecord.carrier)
            )
        ).all()

        quotes_by_carrier: List[Dict[str, Any]] = [
            {
                "carrier": carrier,
                "quote_count": count,
                "avg_total_charges": round(float(avg or 0), 2),
            }
            for carrier, count, avg in quote_rows
        ]

        total_quotes = sum(row["quote_count"] for row in quotes_by_carrier)

        return {
            "total_users": total_users,
            "users_by_role": users_by_role,
            "active_refresh_tokens": active_tokens,
            "total_rate_quotes": total_quotes,
            "quotes_by_carrier": quotes_by_carrier,
        }
