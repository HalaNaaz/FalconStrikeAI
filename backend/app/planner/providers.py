"""Planner providers: deterministic offline engine and optional LLM integrations."""

import os
from abc import ABC, abstractmethod

from backend.app.core.logging import logger
from backend.app.graph.attack_path_models import AttackPath
from backend.app.graph.models import MisconfigurationFinding
from backend.app.planner.models import CampaignPlan, CampaignStage
from backend.app.techniques.models import AttackTactic, TechniqueRiskLevel
from backend.app.techniques.registry import technique_registry


class PlannerProvider(ABC):
    """Abstract base class for campaign planning engines."""

    @abstractmethod
    def plan(
        self,
        path: AttackPath,
        findings: list[MisconfigurationFinding],
        run_id: str,
    ) -> CampaignPlan:
        """Generate a structured campaign plan from an attack path."""
        pass


class DeterministicPlannerProvider(PlannerProvider):
    """Offline, deterministic heuristic planning engine (FR-2.1, FR-2.2).

    Constructs grounded, multi-stage campaigns from attack path topology and findings
    without requiring external LLM API keys or network access.
    """

    def plan(
        self,
        path: AttackPath,
        findings: list[MisconfigurationFinding],
        run_id: str,
    ) -> CampaignPlan:
        logger.info(
            f"Generating deterministic campaign for attack path {path.path_id} (hops={path.hop_count})"
        )

        stages: list[CampaignStage] = []
        selected_techniques: list[str] = []
        target_resources: list[str] = []

        # Stage 1: Initial Foothold & Network Recon
        entry_node = path.entry_point
        target_resources.append(entry_node.id)

        stages.append(
            CampaignStage(
                stage_name="Initial Access & Foothold Validation",
                tactic=AttackTactic.INITIAL_ACCESS,
                technique_id="T1078",
                technique_name="Valid Accounts",
                target_resource_id=entry_node.id,
                action_parameters={
                    "source_ip": "198.51.100.42",
                    "auth_mechanism": "sts:AssumeRole",
                },
                expected_observation="CloudTrail sts:AssumeRole event recorded with anomalous source IP.",
                estimated_risk=TechniqueRiskLevel.LOW,
            )
        )
        selected_techniques.append("T1078")

        # Stage 2: Account & Infrastructure Discovery
        stages.append(
            CampaignStage(
                stage_name="Account & Exposure Enumeration",
                tactic=AttackTactic.DISCOVERY,
                technique_id="T1526",
                technique_name="Cloud Service Discovery",
                target_resource_id=entry_node.id,
                action_parameters={"scan_type": "read_only_describe"},
                expected_observation="Burst of read-only EC2/IAM describe calls in CloudTrail.",
                estimated_risk=TechniqueRiskLevel.LOW,
                dependencies=[stages[0].stage_id],
            )
        )
        selected_techniques.append("T1526")

        # Stage 3+: Intermediate hops traversal (Privilege Escalation / Lateral Movement)
        prev_stage_id = stages[-1].stage_id
        for _i, edge in enumerate(path.ordered_relationships):
            curr_target_id = edge.target_id
            if curr_target_id not in target_resources:
                target_resources.append(curr_target_id)

            # If edge represents role chaining / assumption
            if edge.type.value in ("ASSUMES_ROLE", "RUNS_AS"):
                if "T1098" not in selected_techniques:
                    stages.append(
                        CampaignStage(
                            stage_name=f"Lateral Movement to Role {curr_target_id.split('/')[-1]}",
                            tactic=AttackTactic.PRIVILEGE_ESCALATION,
                            technique_id="T1098",
                            technique_name="Account Manipulation",
                            target_resource_id=curr_target_id,
                            action_parameters={"pivot_source": edge.source_id},
                            expected_observation="STS AssumeRole chaining logged across internal roles.",
                            estimated_risk=TechniqueRiskLevel.MEDIUM,
                            dependencies=[prev_stage_id],
                        )
                    )
                    selected_techniques.append("T1098")
                    prev_stage_id = stages[-1].stage_id

            # If edge reaches S3 bucket
            elif (
                edge.type.value in ("CAN_ACCESS", "EXPOSED_TO_INTERNET") and "s3" in curr_target_id
            ):
                if "T1552" not in selected_techniques:
                    stages.append(
                        CampaignStage(
                            stage_name=f"Credential & Object Discovery on Bucket {curr_target_id.split(':::')[-1]}",
                            tactic=AttackTactic.CREDENTIAL_ACCESS,
                            technique_id="T1552",
                            technique_name="Unsecured Credentials",
                            target_resource_id=curr_target_id,
                            action_parameters={"marker_lookup": "falcon-marker.txt"},
                            expected_observation="S3 GetObject API call querying planted benign marker object.",
                            estimated_risk=TechniqueRiskLevel.LOW,
                            dependencies=[prev_stage_id],
                        )
                    )
                    selected_techniques.append("T1552")
                    prev_stage_id = stages[-1].stage_id

        # Stage Final: Command & Control Signalling (Benign beacon to lab sink)
        stages.append(
            CampaignStage(
                stage_name="C2 Detection Validation Signalling",
                tactic=AttackTactic.COMMAND_AND_CONTROL,
                technique_id="T1071",
                technique_name="Application Layer Protocol",
                target_resource_id=entry_node.id,
                action_parameters={"sink_port": 8443, "interval_sec": 5, "jitter_pct": 20},
                expected_observation="Jittered HTTPS connection pattern to lab sink with inert marker tokens.",
                estimated_risk=TechniqueRiskLevel.LOW,
                dependencies=[prev_stage_id],
            )
        )
        selected_techniques.append("T1071")

        # Aggregate expected IOCs and Telemetry from technique contracts
        all_iocs = []
        all_telemetry = []
        for tid in selected_techniques:
            contract = technique_registry.get(tid)
            if contract:
                all_iocs.extend(contract.expected_iocs)
                all_telemetry.extend(contract.expected_telemetry)

        objective = (
            f"Validate detection coverage along attack path targeting {path.target_resource.name}"
        )
        rationale = (
            f"Campaign targets crown jewel {path.target_resource.id} ({path.target_resource.type.value}) "
            f"via {path.hop_count} hops from {path.entry_point.id}. Sequenced through initial access, "
            f"privilege escalation, and benign C2 beaconing to trigger SOC detection rules."
        )

        return CampaignPlan(
            run_id=run_id,
            source_attack_path_id=path.path_id,
            objective=objective,
            target_resources=target_resources,
            stages=stages,
            selected_techniques=selected_techniques,
            expected_iocs=all_iocs,
            expected_telemetry=all_telemetry,
            risk_summary="Emulation is bounded to read-only queries, role assumptions, and local C2 beaconing.",
            planner_provider="deterministic",
            planning_rationale=rationale,
            approved_by_policy=False,
        )


class GeminiPlannerProvider(PlannerProvider):
    """Google Gemini GenAI planner with strict validation and deterministic fallback (FR-2.1)."""

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        self.model_name = model_name
        self.fallback = DeterministicPlannerProvider()

    def plan(
        self,
        path: AttackPath,
        findings: list[MisconfigurationFinding],
        run_id: str,
    ) -> CampaignPlan:
        from backend.app.core.config import settings

        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("FALCON_GEMINI_API_KEY")
            or getattr(settings, "gemini_api_key", None)
        )
        if not api_key:
            logger.info(
                "No Gemini API key detected in environment. Using deterministic planner fallback."
            )
            plan = self.fallback.plan(path, findings, run_id)
            plan.planner_provider = "gemini_fallback_deterministic"
            return plan

        # When credentials are provided, attempt live GenAI call
        try:
            logger.info(f"Invoking Google Gemini ({self.model_name}) for attack path {path.path_id}...")
            from google import genai
            from google.genai import types

            from backend.app.planner.prompts import SYSTEM_PLANNER_PROMPT, USER_PLANNER_PROMPT_TEMPLATE

            # Format hops from ordered relationships
            if hasattr(path, "ordered_relationships") and path.ordered_relationships:
                hop_text = "\n".join(
                    f"  Hop {i}: {e.source_id} -> {e.type.value if hasattr(e.type, 'value') else e.type} -> {e.target_id}"
                    for i, e in enumerate(path.ordered_relationships, start=1)
                )
            elif hasattr(path, "hops") and path.hops:
                hop_text = "\n".join(
                    f"  Hop {i}: {h.get('source_id', 'Unknown')} -> {h.get('relationship', 'PIVOT')} -> {h.get('target_id', 'Unknown')}"
                    for i, h in enumerate(path.hops, start=1)
                )
            else:
                target_rel = getattr(path, "target_resource", getattr(path, "target_crown_jewel", None))
                target_str = target_rel.id if target_rel else "target"
                hop_text = f"  Direct pivot: {path.entry_point.id} -> {target_str}"

            target_node = getattr(path, "target_resource", getattr(path, "target_crown_jewel", None))
            target_id = target_node.id if target_node else "target-crown-jewel"
            target_type = target_node.type.value if target_node and hasattr(target_node.type, "value") else "RESOURCE"

            findings_text = "\n".join(
                f"- {getattr(f, 'rule_name', getattr(f, 'category', 'EXPOSURE'))} ({f.severity.value if hasattr(f.severity, 'value') else f.severity}): {getattr(f, 'description', getattr(f, 'explanation', 'Misconfiguration'))} on {getattr(f, 'target_node_id', getattr(f, 'resource_id', 'asset'))}"
                for f in findings[:5]
            ) or "None identified"

            severity_val = path.severity.value if hasattr(path.severity, "value") else str(path.severity)
            user_prompt = USER_PLANNER_PROMPT_TEMPLATE.format(
                path_id=path.path_id,
                risk_score=round(path.risk_score, 1),
                severity=severity_val,
                entry_id=path.entry_point.id,
                entry_type=path.entry_point.type.value if hasattr(path.entry_point.type, "value") else str(path.entry_point.type),
                target_id=target_id,
                target_type=target_type,
                hop_sequence=hop_text,
                findings_summary=findings_text,
            )

            client = genai.Client(api_key=api_key)
            model_to_use = self.model_name
            try:
                response = client.models.generate_content(
                    model=model_to_use,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PLANNER_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
            except Exception as api_err:
                err_str = str(api_err)
                if "404" in err_str or "not available" in err_str.lower() or "not_found" in err_str.lower():
                    logger.info(f"Model {model_to_use} unavailable; falling back to gemini-flash-latest...")
                    model_to_use = "gemini-flash-latest"
                    response = client.models.generate_content(
                        model=model_to_use,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PLANNER_PROMPT,
                            response_mime_type="application/json",
                            temperature=0.2,
                        ),
                    )
                else:
                    raise api_err

            if response and response.text:
                import json

                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = raw_text.strip("`")
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:].strip()

                parsed_data = json.loads(raw_text)
                parsed_data["run_id"] = run_id
                parsed_data["source_attack_path_id"] = path.path_id
                parsed_data["planner_provider"] = "gemini"
                parsed_data["approved_by_policy"] = False
                plan = CampaignPlan(**parsed_data)
                logger.info(f"Gemini planning succeeded with {len(plan.stages)} stages using {model_to_use}.")
                return plan
            raise RuntimeError("Gemini API returned an empty response")

        except Exception as exc:
            logger.warning(
                f"Gemini API planning failed: {exc}. Falling back to deterministic planner."
            )
            plan = self.fallback.plan(path, findings, run_id)
            plan.planner_provider = "gemini_fallback_deterministic"
            return plan


def get_planner_provider(provider_name: str = "deterministic") -> PlannerProvider:
    """Factory creating the requested planner provider."""
    name = provider_name.lower().strip()
    if name == "gemini":
        return GeminiPlannerProvider()
    return DeterministicPlannerProvider()
