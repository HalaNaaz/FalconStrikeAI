"""Modular policy rules for campaign safety gate evaluation."""

from abc import ABC, abstractmethod
from typing import Any

from backend.app.core.config import settings
from backend.app.planner.models import CampaignPlan
from backend.app.policies.authorization import TwoKeyAuthorizer
from backend.app.policies.blast_radius import BlastRadiusEvaluator
from backend.app.policies.models import PolicyRuleResult
from backend.app.techniques.registry import technique_registry

# Global kill switch flag for testing and runtime halts (NFR-S3)
GLOBAL_KILL_SWITCH_ACTIVE: bool = False


def set_global_kill_switch(active: bool) -> None:
    """Set the state of the emergency kill switch."""
    global GLOBAL_KILL_SWITCH_ACTIVE
    GLOBAL_KILL_SWITCH_ACTIVE = active


def is_global_kill_switch_active() -> bool:
    """Return whether emergency kill switch is currently active."""
    return GLOBAL_KILL_SWITCH_ACTIVE


class BasePolicyRule(ABC):
    """Abstract base class for policy rules."""

    @property
    @abstractmethod
    def rule_name(self) -> str:
        pass

    @abstractmethod
    def evaluate(
        self,
        plan: CampaignPlan,
        target_account: str,
        context: dict[str, Any],
    ) -> PolicyRuleResult:
        pass


class AccountAllowlistRule(BasePolicyRule):
    """Rule verifying target AWS account is in the compiled allowlist (NFR-S1)."""

    @property
    def rule_name(self) -> str:
        return "ACCOUNT_ALLOWLIST_CHECK"

    def evaluate(
        self, plan: CampaignPlan, target_account: str, context: dict[str, Any]
    ) -> PolicyRuleResult:
        is_allowed = settings.is_account_allowlisted(target_account)
        if not is_allowed:
            return PolicyRuleResult(
                rule_name=self.rule_name,
                passed=False,
                reason=f"Account '{target_account}' is NOT in the compiled allowlist. Permitted: {settings.allowlisted_accounts}",
                details={
                    "target_account": target_account,
                    "allowlisted": settings.allowlisted_accounts,
                },
            )
        return PolicyRuleResult(
            rule_name=self.rule_name,
            passed=True,
            reason=f"Account '{target_account}' is allowlisted.",
            details={"target_account": target_account},
        )


class TechniqueAllowlistRule(BasePolicyRule):
    """Rule verifying all campaign techniques are registered in the approved catalog (FR-2.2)."""

    @property
    def rule_name(self) -> str:
        return "TECHNIQUE_ALLOWLIST_CHECK"

    def evaluate(
        self, plan: CampaignPlan, target_account: str, context: dict[str, Any]
    ) -> PolicyRuleResult:
        unapproved = [
            s.technique_id
            for s in plan.stages
            if not technique_registry.is_approved(s.technique_id)
        ]
        if unapproved:
            return PolicyRuleResult(
                rule_name=self.rule_name,
                passed=False,
                reason=f"Campaign contains unapproved technique IDs: {unapproved}",
                details={"unapproved_techniques": unapproved},
            )
        return PolicyRuleResult(
            rule_name=self.rule_name,
            passed=True,
            reason="All campaign techniques are present in the approved technique registry.",
            details={"techniques": plan.selected_techniques},
        )


class BlastRadiusRule(BasePolicyRule):
    """Rule verifying stage counts and resource caps (NFR-S5)."""

    @property
    def rule_name(self) -> str:
        return "BLAST_RADIUS_CAPS_CHECK"

    def evaluate(
        self, plan: CampaignPlan, target_account: str, context: dict[str, Any]
    ) -> PolicyRuleResult:
        passed, reason, details = BlastRadiusEvaluator.evaluate(plan)
        return PolicyRuleResult(
            rule_name=self.rule_name,
            passed=passed,
            reason=reason,
            details=details,
        )


class KillSwitchRule(BasePolicyRule):
    """Rule verifying global kill switch is not active (NFR-S3)."""

    @property
    def rule_name(self) -> str:
        return "KILL_SWITCH_STATUS_CHECK"

    def evaluate(
        self, plan: CampaignPlan, target_account: str, context: dict[str, Any]
    ) -> PolicyRuleResult:
        if is_global_kill_switch_active():
            return PolicyRuleResult(
                rule_name=self.rule_name,
                passed=False,
                reason="Emergency Kill Switch is ACTIVE. All campaign approvals are blocked.",
                details={"kill_switch_active": True},
            )
        return PolicyRuleResult(
            rule_name=self.rule_name,
            passed=True,
            reason="Emergency Kill Switch is inactive.",
            details={"kill_switch_active": False},
        )


class TwoKeyAuthorizationRule(BasePolicyRule):
    """Rule enforcing cryptographic two-key confirmation for live execution (NFR-S2)."""

    @property
    def rule_name(self) -> str:
        return "TWO_KEY_AUTHORIZATION_CHECK"

    def evaluate(
        self, plan: CampaignPlan, target_account: str, context: dict[str, Any]
    ) -> PolicyRuleResult:
        request_live = context.get("request_live_execution", False)

        # For dry-run, live authorization is not required
        if not request_live and settings.dry_run:
            return PolicyRuleResult(
                rule_name=self.rule_name,
                passed=True,
                reason="Dry-run execution approved. Two-key approval not required for non-destructive dry-run.",
                details={"dry_run": True},
            )

        # For live execution, two distinct tokens must be verified
        op_token = context.get("operator_token")
        sec_token = context.get("secondary_approver_token")

        passed, reason, claims = TwoKeyAuthorizer.verify_two_key_approval(
            operator_token=op_token,
            secondary_approver_token=sec_token,
            expected_account_id=target_account,
        )

        return PolicyRuleResult(
            rule_name=self.rule_name,
            passed=passed,
            reason=reason,
            details=claims,
        )
