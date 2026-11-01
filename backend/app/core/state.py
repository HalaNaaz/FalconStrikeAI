"""Global application state container for active graph, planner, and policy engine."""

from backend.app.collectors.models import NormalizedEnvironmentData
from backend.app.collectors.synthetic import SyntheticEnvironmentProvider
from backend.app.graph.attack_path_models import AttackPath
from backend.app.graph.enrichment import MisconfigurationAnalyzer
from backend.app.graph.ingestion import GraphIngestor
from backend.app.graph.models import MisconfigurationFinding
from backend.app.graph.store import InMemoryGraphStore
from backend.app.orchestrator.execution_engine import ExecutionEngine
from backend.app.orchestrator.kill_switch import EmergencyKillSwitch, kill_switch
from backend.app.planner.models import CampaignPlan
from backend.app.planner.planner import CampaignPlanner
from backend.app.policies.engine import PolicyGateEngine, policy_gate_engine
from backend.app.policies.models import PolicyDecision
from backend.app.telemetry.collector import TelemetryCollector, telemetry_collector


class ApplicationState:
    """Singleton container managing in-memory graph store, environment data, findings, planner, policies, and orchestrator."""

    def __init__(self) -> None:
        self.graph_store: InMemoryGraphStore = InMemoryGraphStore()
        self.environment_data: NormalizedEnvironmentData | None = None
        self.findings: list[MisconfigurationFinding] = []
        self.cached_attack_paths: list[AttackPath] = []
        self.planner: CampaignPlanner = CampaignPlanner(provider_name="deterministic")
        self.policy_engine: PolicyGateEngine = policy_gate_engine
        self.cached_policy_decisions: dict[str, PolicyDecision] = {}
        self.kill_switch: EmergencyKillSwitch = kill_switch
        self.telemetry_collector: TelemetryCollector = telemetry_collector
        self.execution_engine: ExecutionEngine = ExecutionEngine(
            ks=self.kill_switch, telemetry=self.telemetry_collector
        )

        # Initialize with synthetic flawed environment by default for immediate readiness
        self.load_default_environment()

    def load_default_environment(self) -> None:
        """Load default synthetic flawed environment and build graph."""
        self.environment_data = SyntheticEnvironmentProvider.generate_flawed_environment(
            "000000000000"
        )
        ingestor = GraphIngestor(self.graph_store)
        ingestor.ingest(self.environment_data)
        analyzer = MisconfigurationAnalyzer(self.graph_store)
        self.findings = analyzer.analyze(self.environment_data)

    def update_environment(self, data: NormalizedEnvironmentData) -> None:
        """Update active environment, ingest into graph, and refresh findings."""
        self.environment_data = data
        ingestor = GraphIngestor(self.graph_store)
        ingestor.ingest(self.environment_data)
        analyzer = MisconfigurationAnalyzer(self.graph_store)
        self.findings = analyzer.analyze(self.environment_data)
        self.cached_attack_paths.clear()

    def cache_campaign(self, plan: CampaignPlan) -> None:
        """Store generated campaign plan."""
        self.planner.cached_campaigns[plan.campaign_id] = plan

    def get_campaign(self, campaign_id: str) -> CampaignPlan | None:
        """Retrieve campaign plan by ID."""
        return self.planner.get_campaign(campaign_id)


app_state = ApplicationState()
