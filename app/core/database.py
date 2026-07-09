"""SQLAlchemy async engine, session factory, and database lifecycle helpers."""

from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_engine_kwargs: dict = {}

if not settings.async_database_url.startswith("sqlite"):
    # Connection pooling — QueuePool is the default for PostgreSQL/CockroachDB.
    # pool_pre_ping: verify connections before checkout (avoids stale connections).
    # pool_recycle: recycle connections after N seconds (prevents DB-side timeouts).
    _engine_kwargs.update(
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )

engine = create_async_engine(settings.async_database_url, **_engine_kwargs)
SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async database session (FastAPI dependency)."""
    async with SessionLocal() as db:
        yield db


async def seed_roles(db: AsyncSession) -> None:
    """Insert default roles if they don't exist (idempotent)."""
    from app.models import Role, UserRole

    for role_enum in UserRole:
        result = await db.execute(select(Role).where(Role.name == role_enum.value))
        if result.scalar_one_or_none() is None:
            db.add(Role(name=role_enum.value))
    await db.commit()


async def init_db() -> None:
    """Create tables and seed reference data (used in tests and local dev)."""
    import app.models  # noqa: F401 — registers all models with Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        await seed_roles(db)
