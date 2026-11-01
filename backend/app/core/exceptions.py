"""Custom domain exceptions for Falcon Strike-AI."""

from typing import Any


class FalconStrikeError(Exception):
    """Base exception for all Falcon Strike-AI errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SafetyPolicyViolationError(FalconStrikeError):
    """Raised when an operation violates a safety guardrail or policy rule."""


class FalconSecurityException(SafetyPolicyViolationError):
    """Raised when an operation violates security boundaries or is rejected by security policies."""


class AccountNotAllowlistedError(SafetyPolicyViolationError):
    """Raised when an action targets an account ID not on the compiled allowlist (NFR-S1)."""


class AuthorizationTokenError(SafetyPolicyViolationError):
    """Raised when an operation lacks a valid signed authorization token to exit dry-run (NFR-S2)."""


class BlastRadiusExceededError(SafetyPolicyViolationError):
    """Raised when planned actions exceed configured resource touch limits or caps (NFR-S5)."""


class KillSwitchTriggeredError(FalconStrikeError):
    """Raised when an in-flight operation is halted by the emergency kill switch (NFR-S3)."""


class TeardownVerificationError(FalconStrikeError):
    """Raised when post-run environment state does not equal recorded baseline (NFR-S7)."""


class GraphQueryError(FalconStrikeError):
    """Raised when a graph traversal or attack-path computation fails."""


class TechniqueExecutionError(FalconStrikeError):
    """Raised when an emulation technique fails inside the runner."""
