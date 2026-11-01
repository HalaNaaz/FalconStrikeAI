"""Policy decision serialization and audit helpers."""

from typing import Any

from backend.app.policies.models import PolicyDecision


def format_decision_for_audit(decision: PolicyDecision) -> dict[str, Any]:
    """Format a policy decision for the append-only audit log."""
    return {
        "event_type": "POLICY_EVALUATION",
        "decision_id": decision.decision_id,
        "campaign_id": decision.campaign_id,
        "run_id": decision.run_id,
        "decision": decision.decision.value,
        "approved": decision.approved,
        "rejected_rules_count": len(decision.rejected_rules),
        "evaluated_at": decision.evaluated_at,
        "summary": decision.evaluation_summary,
    }

