"""Asynchronous SQLAlchemy engine lifecycle."""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from saudi_business_launch_navigator.core.config import Settings


def create_database_engine(settings: Settings) -> AsyncEngine:
    """Create a lazy async engine without opening a connection."""
    return create_async_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        hide_parameters=True,
    )


async def dispose_database_engine(engine: AsyncEngine) -> None:
    """Release every pooled database connection owned by the application."""
    await engine.dispose()
