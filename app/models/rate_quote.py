"""Persisted shipping rate quotes — enables historical queries and aggregations."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class RateQuoteRecord(Base):
    """One row per carrier service quote returned to a user."""

    __tablename__ = "rate_quotes"
    __table_args__ = (
        Index("ix_rate_quotes_user_id", "user_id"),
        Index("ix_rate_quotes_carrier", "carrier"),
        Index("ix_rate_quotes_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    carrier: Mapped[str] = mapped_column(String(20), nullable=False)
    service_code: Mapped[str] = mapped_column(String(10), nullable=False)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_charges: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    origin_country: Mapped[str] = mapped_column(String(2), nullable=False)
    destination_country: Mapped[str] = mapped_column(String(2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="rate_quotes")
