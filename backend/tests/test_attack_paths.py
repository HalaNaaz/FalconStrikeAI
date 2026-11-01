"""Unit tests for Phase 6 Attack Path Discovery & Ranking Engine."""

from backend.app.collectors.synthetic import SyntheticEnvironmentProvider
from backend.app.graph.enrichment import MisconfigurationAnalyzer
from backend.app.graph.ingestion import GraphIngestor
from backend.app.graph.models import (
    FindingSeverity,
    GraphEdge,
    GraphNode,
    NodeType,
    RelationshipType,
)
from backend.app.graph.path_finder import AttackPathFinder
from backend.app.graph.path_ranker import AttackPathRanker
from backend.app.graph.store import InMemoryGraphStore


def test_attack_path_discovery_flawed_environment() -> None:
    """Verify end-to-end attack path discovery identifies paths from public internet to admin role."""
    env_data = SyntheticEnvironmentProvider.generate_flawed_environment("000000000000")
    store = InMemoryGraphStore()
    ingestor = GraphIngestor(store)
    ingestor.ingest(env_data)

    analyzer = MisconfigurationAnalyzer(store)
    findings = analyzer.analyze(env_data)

    finder = AttackPathFinder(store)
    paths = finder.discover_paths(max_depth=6, findings=findings)

    assert len(paths) >= 2, "Should discover paths to both Admin Role and Public S3 Bucket"

    # Verify ranking order: highest risk score first
    for i in range(len(paths) - 1):
        assert paths[i].risk_score >= paths[i + 1].risk_score

    # Check top path leads to Crown Jewel Admin Role
    top_path = paths[0]
    assert top_path.target_resource.type == NodeType.IAM_ROLE
    assert "admin" in top_path.target_resource.name.lower()
    assert top_path.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH)
    assert top_path.hop_count >= 3
    assert len(top_path.supporting_findings) > 0
    assert "Risk Score" in top_path.ranking_explanation


def test_no_attack_paths_in_clean_environment() -> None:
    """Verify secured environment with private instances and least-privilege roles yields no external paths."""
    env_data = SyntheticEnvironmentProvider.generate_clean_environment("000000000000")
    store = InMemoryGraphStore()
    ingestor = GraphIngestor(store)
    ingestor.ingest(env_data)

    finder = AttackPathFinder(store)
    # Searching from Public Internet anchor
    paths = finder.discover_paths(entry_node_id="endpoint:public-internet", max_depth=5)

    assert len(paths) == 0, "No external attack paths should exist in clean environment"


def test_cycle_handling_does_not_infinite_loop() -> None:
    """Verify graph cycles (A assumes B, B assumes A) do not cause infinite loops or hang."""
    store = InMemoryGraphStore()
    node_entry = GraphNode(
        id="endpoint:entry",
        type=NodeType.PUBLIC_ENDPOINT,
        name="Entry",
        account_id="000000000000",
    )
    node_a = GraphNode(
        id="role:a",
        type=NodeType.IAM_ROLE,
        name="RoleA",
        account_id="000000000000",
    )
    node_b = GraphNode(
        id="role:b",
        type=NodeType.IAM_ROLE,
        name="RoleB",
        account_id="000000000000",
    )
    node_admin = GraphNode(
        id="role:admin",
        type=NodeType.IAM_ROLE,
        name="CrownAdmin",
        account_id="000000000000",
        properties={"is_admin": True},
    )

    store.add_node(node_entry)
    store.add_node(node_a)
    store.add_node(node_b)
    store.add_node(node_admin)

    # Entry -> A
    store.add_edge(
        GraphEdge(
            source_id="endpoint:entry",
            target_id="role:a",
            type=RelationshipType.EXPOSED_TO_INTERNET,
        )
    )
    # Cycle: A <-> B
    store.add_edge(
        GraphEdge(
            source_id="role:a",
            target_id="role:b",
            type=RelationshipType.ASSUMES_ROLE,
        )
    )
    store.add_edge(
        GraphEdge(
            source_id="role:b",
            target_id="role:a",
            type=RelationshipType.ASSUMES_ROLE,
        )
    )
    # B -> Admin
    store.add_edge(
        GraphEdge(
            source_id="role:b",
            target_id="role:admin",
            type=RelationshipType.ASSUMES_ROLE,
        )
    )

    finder = AttackPathFinder(store)
    paths = finder.discover_paths(entry_node_id="endpoint:entry", max_depth=6)

    assert len(paths) == 1
    assert paths[0].target_resource.id == "role:admin"
    assert paths[0].hop_count == 3  # entry -> a -> b -> admin


def test_max_depth_prunes_distant_targets() -> None:
    """Verify paths exceeding max_depth are pruned."""
    store = InMemoryGraphStore()
    nodes = [
        GraphNode(
            id=f"node:{i}",
            type=NodeType.PUBLIC_ENDPOINT if i == 0 else NodeType.IAM_ROLE,
            name=f"Node-{i}",
            account_id="000000000000",
            properties={"is_admin": (i == 5)},
        )
        for i in range(6)
    ]
    for n in nodes:
        store.add_node(n)

    # Chain 0 -> 1 -> 2 -> 3 -> 4 -> 5 (5 hops)
    store.add_edge(
        GraphEdge(
            source_id="node:0",
            target_id="node:1",
            type=RelationshipType.EXPOSED_TO_INTERNET,
        )
    )
    for i in range(1, 5):
        store.add_edge(
            GraphEdge(
                source_id=f"node:{i}",
                target_id=f"node:{i + 1}",
                type=RelationshipType.ASSUMES_ROLE,
            )
        )

    finder = AttackPathFinder(store)
    # Depth 3 should not find target at depth 5
    short_paths = finder.discover_paths(entry_node_id="node:0", max_depth=3)
    assert len(short_paths) == 0

    # Depth 5 should find it
    full_paths = finder.discover_paths(entry_node_id="node:0", max_depth=5)
    assert len(full_paths) == 1
    assert full_paths[0].target_resource.id == "node:5"


def test_ranking_scoring_model_explanation() -> None:
    """Verify scoring model adds points for public exposure, admin targets, and findings."""
    ranker = AttackPathRanker()
    entry = GraphNode(id="pub", type=NodeType.PUBLIC_ENDPOINT, name="Internet", account_id="000")
    target = GraphNode(
        id="adm",
        type=NodeType.IAM_ROLE,
        name="AdminRole",
        account_id="000",
        properties={"is_admin": True},
    )
    edge = GraphEdge(source_id="pub", target_id="adm", type=RelationshipType.EXPOSED_TO_INTERNET)

    path = ranker.rank_path(
        entry_node=entry,
        target_node=target,
        ordered_nodes=[entry, target],
        ordered_edges=[edge],
        findings=[],
    )

    # 30 (entry) + 35 (target) + 15 (direct hop <= 2) = 80
    assert path.risk_score >= 80.0
    assert path.severity == FindingSeverity.CRITICAL
    assert "+30 pts: Entry point" in path.ranking_explanation
    assert "+35 pts: Target is Cloud Administrator" in path.ranking_explanation
