"""Unit tests for structured logging and RFC-3339 timestamps."""

import json
import logging
from datetime import datetime

from backend.app.core.logging import RFC3339JsonFormatter, current_run_id


def test_rfc3339_json_formatter() -> None:
    """Verify structured logger emits conformant JSON with UTC RFC-3339 timestamps (NFR-A1)."""
    formatter = RFC3339JsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Emulation technique started",
        args=(),
        exc_info=None,
    )
    record.technique_id = "T1078"
    record.actor = "AgenticPlanner"

    output = formatter.format(record)
    data = json.loads(output)

    assert data["level"] == "INFO"
    assert data["message"] == "Emulation technique started"
    assert data["technique_id"] == "T1078"
    assert data["actor"] == "AgenticPlanner"
    assert "timestamp" in data

    # Verify timestamp format parses as valid ISO-8601 / RFC-3339
    parsed_dt = datetime.fromisoformat(data["timestamp"])
    assert parsed_dt.tzinfo is not None, "Timestamp must include timezone info (UTC)"


def test_current_run_id_threading() -> None:
    """Verify campaign run_id is dynamically included in log records (NFR-A3)."""
    formatter = RFC3339JsonFormatter()
    token = current_run_id.set("campaign-run-uuid-12345")
    try:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname=__file__,
            lineno=20,
            msg="Kill switch check",
            args=(),
            exc_info=None,
        )
        data = json.loads(formatter.format(record))
        assert data["run_id"] == "campaign-run-uuid-12345"
    finally:
        current_run_id.reset(token)
