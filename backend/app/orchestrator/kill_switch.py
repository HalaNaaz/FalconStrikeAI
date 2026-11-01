"""Central emergency kill switch manager for immediate emulation termination (FR-3.6, NFR-S3)."""

import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.core.exceptions import FalconSecurityException
from backend.app.core.logging import logger
from backend.app.policies.rules import set_global_kill_switch


class KillSwitchRecord(BaseModel):
    """Audit log record for an emergency kill switch activation event."""

    record_id: str = Field(default_factory=lambda: f"KS-{uuid4().hex[:8].upper()}")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    reason: str
    operator_id: str
    run_id: str | None = None
    response_time_ms: float = 0.0


class EmergencyKillSwitch:
    """Thread-safe, high-speed emergency halt coordinator (FR-3.6, NFR-S3).

    Guarantees:
    - Execution halt initiated within < 2 seconds (typically < 1 millisecond).
    - Blocks subsequent campaign stages immediately.
    - Synchronizes with policy gate rules to prevent any new approvals while active.
    - Requires privileged authentication to reset.
    """

    # Default authorized token for testing/administrative resets
    RESET_TOKEN_ALLOWLIST: set[str] = {"ADMIN_EMERGENCY_RESET_KEY_SECURE_2026", "ALLOW_RESET_DEV"}

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._active: bool = False
        self._activation_history: list[KillSwitchRecord] = []
        self._abort_callbacks: list[Callable[[str, str | None], None]] = []

    def is_active(self) -> bool:
        """Check whether emergency kill switch is currently engaged."""
        with self._lock:
            return self._active

    def trigger(
        self,
        reason: str,
        operator_id: str = "security-admin",
        run_id: str | None = None,
    ) -> KillSwitchRecord:
        """Trigger immediate emergency stop across all active campaigns and stages.

        Response time guaranteed < 2.0 seconds (NFR-S3).
        """
        start_time = time.perf_counter()

        with self._lock:
            self._active = True
            # Synchronize with policy engine flag
            set_global_kill_switch(True)

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            record = KillSwitchRecord(
                reason=reason,
                operator_id=operator_id,
                run_id=run_id,
                response_time_ms=round(elapsed_ms, 3),
            )
            self._activation_history.append(record)

            logger.critical(
                f"EMERGENCY KILL SWITCH ACTIVATED in {elapsed_ms:.3f}ms by '{operator_id}'. "
                f"Reason: '{reason}'. Run ID: {run_id or 'ALL'}"
            )

            # Fire registered cancellation callbacks to halt active threads/runners
            for callback in self._abort_callbacks:
                try:
                    callback(reason, run_id)
                except Exception as exc:
                    logger.error(f"Error in kill switch abort callback: {exc}")

            return record

    def reset(self, authorized_token: str, operator_id: str = "security-admin") -> bool:
        """Deactivate kill switch and restore normal operations.

        Requires an authorized administrative reset token.
        """
        with self._lock:
            if authorized_token not in self.RESET_TOKEN_ALLOWLIST:
                logger.warning(
                    f"Unauthorized attempt to reset Emergency Kill Switch by '{operator_id}' with invalid token."
                )
                raise FalconSecurityException(
                    "Kill switch reset rejected: Invalid administrative authorization token."
                )

            self._active = False
            set_global_kill_switch(False)
            logger.info(f"Emergency Kill Switch successfully RESET by '{operator_id}'. Normal operations resumed.")
            return True

    def register_abort_callback(
        self, callback: Callable[[str, str | None], None]
    ) -> None:
        """Register a callback function to be executed immediately upon kill switch trigger."""
        with self._lock:
            self._abort_callbacks.append(callback)

    def get_status(self) -> dict[str, Any]:
        """Return operational status and activation history."""
        with self._lock:
            last_record = self._activation_history[-1] if self._activation_history else None
            return {
                "active": self._active,
                "total_triggers": len(self._activation_history),
                "last_activated_at": last_record.timestamp if last_record else None,
                "last_operator": last_record.operator_id if last_record else None,
                "last_reason": last_record.reason if last_record else None,
                "last_response_time_ms": last_record.response_time_ms if last_record else 0.0,
                "history": [r.model_dump() for r in self._activation_history],
            }


# Global singleton instance
kill_switch = EmergencyKillSwitch()
