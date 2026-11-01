"""Unit tests for Phase 5 Property Graph Engine & Misconfiguration Analyzer."""

import pytest

from backend.app.collectors.synthetic import SyntheticEnvironmentProvider
from backend.app.core.exceptions import GraphQueryError
from backend.app.graph.enrichment import MisconfigurationAnalyzer
from backend.app.graph.ingestion import GraphIngestor
from backend.app.graph.models import (
    FindingCategory,
    GraphEdge,
    GraphNode,
    NodeType,
    RelationshipType,
)
from backend.app.graph.store import InMemoryGraphStore


def test_graph_node_and_edge_creation() -> None:
    """Verify node and edge addition and query retrieval."""
    store = InMemoryGraphStore()
    node_a = GraphNode(
        id="user:alice",
        type=NodeType.IAM_USER,
        name="alice",
        account_id="000000000000",
    )
    node_b = GraphNode(
        id="role:admin",
        type=NodeType.IAM_ROLE,
        name="admin",
        account_id="000000000000",
    )
    store.add_node(node_a)
    store.add_node(node_b)

    edge = GraphEdge(
        source_id=node_a.id,
        target_id=node_b.id,
        type=RelationshipType.ASSUMES_ROLE,
    )
    store.add_edge(edge)

    assert store.get_node(node_a.id) == node_a
    assert store.get_node(node_b.id) == node_b
    assert len(store.get_nodes_by_type(NodeType.IAM_USER)) == 1
    assert len(store.get_out_edges(node_a.id)) == 1
    assert len(store.get_in_edges(node_b.id)) == 1


def test_edge_fails_on_missing_nodes() -> None:
    """Verify adding edge with non-existent node raises GraphQueryError."""
    store = InMemoryGraphStore()
    node_a = GraphNode(id="user:bob", type=NodeType.IAM_USER, name="bob", account_id="000000000000")
    store.add_node(node_a)

    edge = GraphEdge(
        source_id="user:bob",
        target_id="role:nonexistent",
        type=RelationshipType.ASSUMES_ROLE,
    )
    with pytest.raises(GraphQueryError) as exc_info:
        store.add_edge(edge)
    assert "Target node 'role:nonexistent' does not exist" in str(exc_info.value)


def test_graph_serialization_roundtrip() -> None:
    """Verify graph exports to and imports from JSON-serializable dictionary."""
    store = InMemoryGraphStore()
    node_a = GraphNode(id="n1", type=NodeType.ACCOUNT, name="acc", account_id="000000000000")
    node_b = GraphNode(id="n2", type=NodeType.S3_BUCKET, name="bkt", account_id="000000000000")
    store.add_node(node_a)
    store.add_node(node_b)
    store.add_edge(GraphEdge(source_id="n1", target_id="n2", type=RelationshipType.CONTAINS))

    data = store.to_dict()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1

    new_store = InMemoryGraphStore()
    new_store.from_dict(data)
    assert len(new_store.get_all_nodes()) == 2
    assert len(new_store.get_all_edges()) == 1


def test_graph_ingestion_from_flawed_environment() -> None:
    """Verify graph ingestion builds expected topology and connections."""
    env_data = SyntheticEnvironmentProvider.generate_flawed_environment("000000000000")
    store = InMemoryGraphStore()
    ingestor = GraphIngestor(store)
    node_count, edge_count = ingestor.ingest(env_data)

    assert node_count >= 8
    assert edge_count >= 8

    # Verify public internet node exists
    pub_node = store.get_node("endpoint:public-internet")
    assert pub_node is not None
    assert pub_node.type == NodeType.PUBLIC_ENDPOINT

    # Verify public internet connects to EC2 and S3
    out_edges = store.get_out_edges(pub_node.id)
    exposed_targets = [
        e.target_id for e in out_edges if e.type == RelationshipType.EXPOSED_TO_INTERNET
    ]
    assert any("ec2:" in t for t in exposed_targets)
    assert any("s3:::" in t for t in exposed_targets)


def test_misconfiguration_analyzer_findings() -> None:
    """Verify misconfiguration analyzer produces accurate findings from flawed topology."""
    env_data = SyntheticEnvironmentProvider.generate_flawed_environment("000000000000")
    store = InMemoryGraphStore()
    ingestor = GraphIngestor(store)
    ingestor.ingest(env_data)

    analyzer = MisconfigurationAnalyzer(store)
    findings = analyzer.analyze(env_data)

    assert len(findings) >= 4
    categories = [f.category for f in findings]
    assert FindingCategory.WILDCARD_PERMISSIONS in categories
    assert FindingCategory.PUBLIC_EXPOSURE in categories
    assert FindingCategory.PUBLIC_STORAGE in categories
    assert FindingCategory.PRIVILEGE_ESCALATION in categories

    # Verify finding details
    privesc_finding = next(
        f for f in findings if f.category == FindingCategory.PRIVILEGE_ESCALATION
    )
    assert "Administrator" in privesc_finding.explanation
    assert privesc_finding.severity == "CRITICAL"
    assert privesc_finding.remediation is not None


def test_neo4j_graph_store_offline_graceful_fallback() -> None:
    """Verify Neo4jGraphStore handles disabled/unavailable Neo4j server gracefully."""
    from backend.app.graph.neo4j_store import Neo4jGraphStore

    neo_store = Neo4jGraphStore()
    assert neo_store.is_connected is False
    assert neo_store.get_node("any") is None
    assert neo_store.get_nodes_by_type(NodeType.ACCOUNT) == []
    assert neo_store.get_out_edges("any") == []
    assert neo_store.get_in_edges("any") == []


def test_scale_benchmark_fast_run() -> None:
    """Verify benchmark generator executes and returns metrics dictionary."""
    from backend.app.graph.scale_benchmark import run_benchmark

    metrics = run_benchmark(target_nodes=100, iterations=2)
    assert metrics["total_nodes"] >= 100
    assert "p95_latency_ms" in metrics
    assert metrics["target_met"] is True
