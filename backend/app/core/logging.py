"""Structured logging foundation for Falcon Strike-AI with RFC-3339 timestamps."""

import contextvars
import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# Context variable to thread campaign run_id across all log calls (NFR-A3)
current_run_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_run_id", default=None
)


class RFC3339JsonFormatter(logging.Formatter):
    """Custom JSON formatter producing conformant structured records with RFC-3339 timestamps."""

    def format(self, record: logging.LogRecord) -> str:
        # Create standard UTC RFC-3339 timestamp
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat()

        log_payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": current_run_id.get(),
            "environment": getattr(record, "environment", "development"),
        }

        # Include structured extra attributes if provided
        if hasattr(record, "details") and isinstance(record.details, dict):
            log_payload["details"] = record.details

        if hasattr(record, "technique_id"):
            log_payload["technique_id"] = record.technique_id

        if hasattr(record, "actor"):
            log_payload["actor"] = record.actor

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure root logger with structured JSON formatting."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(RFC3339JsonFormatter())
    root_logger.addHandler(stream_handler)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)

    logger = logging.getLogger("falcon_strike")
    logger.setLevel(level)
    return logger


# Initial default logger
logger = setup_logging()
