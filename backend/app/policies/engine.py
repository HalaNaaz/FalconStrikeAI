"""Safety Policy Gate Engine evaluating campaigns against invariant guardrails (FR-2.5)."""

from typing import Any

from backend.app.core.logging import logger
from backend.app.planner.models import CampaignPlan
from backend.app.policies.models import (
    PolicyDecision,
    PolicyDecisionType,
    PolicyEvaluationRequest,
    PolicyRuleResult,
)
from backend.app.policies.rules import (
    AccountAllowlistRule,
    BasePolicyRule,
    BlastRadiusRule,
    KillSwitchRule,
    TechniqueAllowlistRule,
    TwoKeyAuthorizationRule,
)


class PolicyGateEngine:
    """Independent policy evaluation gate governing campaign execution authorization."""

    def __init__(self, rules: list[BasePolicyRule] | None = None) -> None:
        self.rules: list[BasePolicyRule] = rules or [
            AccountAllowlistRule(),
            TechniqueAllowlistRule(),
            BlastRadiusRule(),
            KillSwitchRule(),
            TwoKeyAuthorizationRule(),
        ]

    def evaluate_campaign(
        self,
        plan: CampaignPlan,
        target_account: str,
        context: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        """Convenience evaluation helper mapping plan and context to PolicyEvaluationRequest."""
        ctx = context or {}
        req = PolicyEvaluationRequest(
            campaign_plan=plan,
            target_account_id=target_account,
            operator_token=ctx.get("operator_token"),
            secondary_approver_token=ctx.get("secondary_approver_token"),
            request_live_execution=ctx.get("request_live_execution", False),
        )
        return self.evaluate(req)

    def evaluate(self, request: PolicyEvaluationRequest) -> PolicyDecision:
        """Evaluate a campaign plan against all registered policy rules with fail-closed semantics."""
        plan = request.campaign_plan
        account_id = request.target_account_id

        logger.info(
            f"Evaluating campaign {plan.campaign_id} for account {account_id} against {len(self.rules)} policy rules"
        )

        rule_results: list[PolicyRuleResult] = []
        rejected_rules: list[str] = []
        warnings: list[str] = []

        context: dict[str, Any] = {
            "operator_token": request.operator_token,
            "secondary_approver_token": request.secondary_approver_token,
            "request_live_execution": request.request_live_execution,
        }

        try:
            for rule in self.rules:
                res = rule.evaluate(plan, account_id, context)
                rule_results.append(res)
                if not res.passed:
                    rejected_rules.append(f"{res.rule_name}: {res.reason}")

            # Determine final policy verdict
            if rejected_rules:
                decision_type = PolicyDecisionType.REJECTED
                approved = False
                summary = (
                    f"Campaign REJECTED. Failed {len(rejected_rules)} policy check(s): "
                    + "; ".join(rejected_rules)
                )
                logger.warning(
                    f"Campaign {plan.campaign_id} REJECTED by policy gate: {summary}",
                    extra={"details": {"rejected_rules": rejected_rules}},
                )
            elif request.request_live_execution:
                # Live execution requires secondary review sign-off before actual dispatch
                decision_type = PolicyDecisionType.APPROVED_FOR_REVIEW
                approved = True
                plan.approved_by_policy = True
                summary = (
                    "Campaign APPROVED for pre-execution security review. "
                    "Two-key authorization confirmed. Live execution gate armed."
                )
                logger.info(f"Campaign {plan.campaign_id} APPROVED_FOR_REVIEW for live execution.")
            else:
                decision_type = PolicyDecisionType.APPROVED_FOR_DRY_RUN
                approved = True
                plan.approved_by_policy = True
                summary = (
                    "Campaign APPROVED FOR DRY-RUN. All safety guardrails and technique contracts satisfied. "
                    "Execution will occur in safe, non-destructive simulation mode."
                )
                logger.info(f"Campaign {plan.campaign_id} APPROVED_FOR_DRY_RUN.")

            return PolicyDecision(
                campaign_id=plan.campaign_id,
                run_id=plan.run_id,
                decision=decision_type,
                approved=approved,
                rejected_rules=rejected_rules,
                warnings=warnings,
                evaluation_summary=summary,
                rule_results=rule_results,
            )

        except Exception as exc:
            # Absolute fail-closed guarantee
            err_msg = f"Unexpected failure in policy gate: {exc}. Failing closed."
            logger.error(err_msg, exc_info=True)
            return PolicyDecision(
                campaign_id=plan.campaign_id,
                run_id=plan.run_id,
                decision=PolicyDecisionType.REJECTED,
                approved=False,
                rejected_rules=["SYSTEM_ERROR: " + err_msg],
                warnings=[],
                evaluation_summary="Policy gate failed closed due to an internal error.",
                rule_results=rule_results,
            )


# Global policy engine instance
policy_gate_engine = PolicyGateEngine()
