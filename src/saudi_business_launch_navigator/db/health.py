"""Database availability checks used only for readiness."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


async def database_is_available(engine: AsyncEngine) -> bool:
    """Return true only when PostgreSQL successfully evaluates SELECT 1."""
    try:
        async with engine.connect() as connection:
            result = await connection.scalar(text("SELECT 1"))
    except Exception as exc:
        logger.warning(
            "Database readiness probe failed",
            extra={
                "event": "database_readiness_failed",
                "component": "database",
                "error_type": type(exc).__name__,
            },
        )
        return False
    return bool(result == 1)
