"""Two-key authorization verification and identity separation (NFR-S2)."""

from typing import Any

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthorizationTokenError
from backend.app.core.security import verify_authorization_token


class TwoKeyAuthorizer:
    """Enforces cryptographic two-key confirmation and distinct approver separation."""

    @staticmethod
    def verify_two_key_approval(
        operator_token: str | None,
        secondary_approver_token: str | None,
        expected_account_id: str,
        secret_key: str | None = None,
    ) -> tuple[bool, str, dict[str, Any]]:
        """Verify two distinct signed authorization tokens for live execution.

        Returns:
            tuple: (is_valid, reason, claims_dict)
        """
        secret = secret_key or settings.auth_secret_key

        if not operator_token:
            return False, "Missing primary operator authorization token.", {}
        if not secondary_approver_token:
            return (
                False,
                "Missing secondary approver (mentor/lead) authorization token. Two-key approval required.",
                {},
            )

        # 1. Verify Primary Operator Token
        try:
            op_claims = verify_authorization_token(
                token=operator_token,
                expected_account_id=expected_account_id,
                secret_key=secret,
            )
        except AuthorizationTokenError as exc:
            return False, f"Primary operator token invalid: {exc}", {}

        # 2. Verify Secondary Approver Token
        try:
            sec_claims = verify_authorization_token(
                token=secondary_approver_token,
                expected_account_id=expected_account_id,
                secret_key=secret,
            )
        except AuthorizationTokenError as exc:
            return False, f"Secondary approver token invalid: {exc}", {}

        # 3. Enforce Strict Approver Identity Separation
        op_identity = op_claims.get("sub")
        sec_identity = sec_claims.get("sub")

        if op_identity == sec_identity:
            return (
                False,
                f"Two-key separation violation: Operator and secondary approver share identical identity ('{op_identity}'). "
                "Two distinct individuals must authorize live execution.",
                {},
            )

        claims = {
            "primary_operator": op_identity,
            "primary_role": op_claims.get("role"),
            "secondary_approver": sec_identity,
            "secondary_role": sec_claims.get("role"),
            "account_id": expected_account_id,
        }

        return True, "Two-key authorization verified with distinct approver identities.", claims
