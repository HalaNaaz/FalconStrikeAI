"""Schema limits and structural invariants for campaigns (NFR-S5)."""

# Hard limits enforcing blast-radius containment
MAX_CAMPAIGN_STAGES: int = 10
MAX_ACTIONS_PER_CAMPAIGN: int = 20
MAX_TARGET_RESOURCES: int = 5
MAX_EXECUTION_DURATION_SECONDS: int = 300

# Canonical sequence of tactics for a standard multi-stage campaign
STANDARD_TACTIC_ORDER: tuple[str, ...] = (
    "Initial Access",
    "Discovery",
    "Privilege Escalation",
    "Persistence",
    "Credential Access",
    "Defense Evasion",
    "Command and Control",
    "Exfiltration",
)

