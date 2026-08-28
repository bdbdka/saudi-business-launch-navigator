"""Safe structured logging built on the Python standard library."""

import json
import logging
from datetime import UTC, datetime
from typing import ClassVar


class StructuredFormatter(logging.Formatter):
    """Render an allowlisted set of log fields as one JSON object."""

    safe_extra_fields: ClassVar[tuple[str, ...]] = (
        "event",
        "component",
        "environment",
        "error_type",
        "request_id",
        "http_method",
        "http_path",
        "status_code",
        "duration_ms",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, str] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field_name in self.safe_extra_fields:
            field_value = getattr(record, field_name, None)
            if field_value is not None:
                payload[field_name] = str(field_value)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    """Configure the root logger with one structured stdout-safe handler."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
