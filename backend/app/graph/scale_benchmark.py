"""Synthetic scale benchmark generator for testing 10,000+ node graph performance (NFR-P1, NFR-P2)."""

import json
import time
from pathlib import Path
from typing import Any

from backend.app.core.logging import logger
from backend.app.graph.models import GraphEdge, GraphNode, NodeType, RelationshipType
from backend.app.graph.path_finder import AttackPathFinder
from backend.app.graph.store import InMemoryGraphStore


def generate_scale_graph(target_nodes: int = 10000) -> tuple[InMemoryGraphStore, float]:
    """Generate a realistic synthetic cloud property graph with >= target_nodes."""
    start_time = time.perf_counter()
    store = InMemoryGraphStore()
    account_id = "000000000000"

    # 1. Anchor Public Internet Node
    public_internet = GraphNode(
        id="endpoint:public-internet",
        type=NodeType.PUBLIC_ENDPOINT,
        name="Public Internet Anchor",
        account_id=account_id,
    )
    store.add_node(public_internet)

    # 2. Add Crown Jewel Target Admin Roles
    admin_roles: list[GraphNode] = []
    for i in range(10):
        admin_role = GraphNode(
            id=f"arn:aws:iam::{account_id}:role/CrownJewelAdminRole-{i}",
            type=NodeType.IAM_ROLE,
            name=f"CrownJewelAdminRole-{i}",
            account_id=account_id,
            properties={"is_admin": True},
        )
        store.add_node(admin_role)
        admin_roles.append(admin_role)

    # 3. Add Intermediate Resources (EC2 instances, Roles, Policies, Buckets, SGs)
    # Calculate counts to reach target_nodes
    remaining = target_nodes - 11
    ec2_count = int(remaining * 0.35)
    role_count = int(remaining * 0.25)
    policy_count = int(remaining * 0.20)
    bucket_count = int(remaining * 0.10)
    sg_count = remaining - (ec2_count + role_count + policy_count + bucket_count)

    # Create EC2 nodes
    ec2_nodes: list[GraphNode] = []
    for i in range(ec2_count):
        node = GraphNode(
            id=f"ec2:i-bench-{i:06d}",
            type=NodeType.EC2_INSTANCE,
            name=f"Instance-{i}",
            account_id=account_id,
            properties={"is_public": (i % 20 == 0)},
        )
        store.add_node(node)
        ec2_nodes.append(node)

        # Expose a subset to the public internet
        if i % 20 == 0:
            store.add_edge(
                GraphEdge(
                    source_id=public_internet.id,
                    target_id=node.id,
                    type=RelationshipType.EXPOSED_TO_INTERNET,
                )
            )

    # Create IAM Role nodes
    role_nodes: list[GraphNode] = []
    for i in range(role_count):
        node = GraphNode(
            id=f"arn:aws:iam::{account_id}:role/BenchRole-{i:06d}",
            type=NodeType.IAM_ROLE,
            name=f"BenchRole-{i}",
            account_id=account_id,
            properties={"is_admin": False},
        )
        store.add_node(node)
        role_nodes.append(node)

    # Connect some EC2 instances to Roles (RUNS_AS)
    for i, ec2 in enumerate(ec2_nodes):
        target_role = role_nodes[i % len(role_nodes)]
        store.add_edge(
            GraphEdge(
                source_id=ec2.id,
                target_id=target_role.id,
                type=RelationshipType.RUNS_AS,
            )
        )

    # Create Policy nodes
    policy_nodes: list[GraphNode] = []
    for i in range(policy_count):
        node = GraphNode(
            id=f"arn:aws:iam::{account_id}:policy/BenchPolicy-{i:06d}",
            type=NodeType.POLICY,
            name=f"BenchPolicy-{i}",
            account_id=account_id,
            properties={"is_admin": (i == 0)},
        )
        store.add_node(node)
        policy_nodes.append(node)

        # Attach to some roles
        role = role_nodes[i % len(role_nodes)]
        store.add_edge(
            GraphEdge(
                source_id=role.id,
                target_id=node.id,
                type=RelationshipType.HAS_POLICY,
            )
        )

    # Create S3 Buckets
    bucket_nodes: list[GraphNode] = []
    for i in range(bucket_count):
        node = GraphNode(
            id=f"arn:aws:s3:::bench-bucket-{i:06d}",
            type=NodeType.S3_BUCKET,
            name=f"bench-bucket-{i}",
            account_id=account_id,
            properties={"is_public": (i % 50 == 0)},
        )
        store.add_node(node)
        bucket_nodes.append(node)

    # Create Security Groups
    for i in range(sg_count):
        node = GraphNode(
            id=f"sg:sg-bench-{i:06d}",
            type=NodeType.SECURITY_GROUP,
            name=f"bench-sg-{i}",
            account_id=account_id,
        )
        store.add_node(node)

    # Plant controlled attack path edges connecting a public EC2 instance to an Admin role via role chaining
    # E.g. Public EC2 -> Role 0 -> Role 1 -> Crown Jewel Admin Role 0
    store.add_edge(
        GraphEdge(
            source_id=role_nodes[0].id,
            target_id=role_nodes[1].id,
            type=RelationshipType.ASSUMES_ROLE,
        )
    )
    store.add_edge(
        GraphEdge(
            source_id=role_nodes[1].id,
            target_id=admin_roles[0].id,
            type=RelationshipType.ASSUMES_ROLE,
        )
    )

    build_time = (time.perf_counter() - start_time) * 1000.0
    return store, build_time


def run_benchmark(
    target_nodes: int = 10000,
    iterations: int = 50,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Execute the scale benchmark and record p50 and p95 path traversal latencies."""
    logger.info(f"Generating synthetic scale graph with {target_nodes}+ nodes...")
    store, build_time_ms = generate_scale_graph(target_nodes=target_nodes)

    total_nodes = len(store.get_all_nodes())
    total_edges = len(store.get_all_edges())
    logger.info(
        f"Scale graph constructed: {total_nodes} nodes, {total_edges} edges in {build_time_ms:.2f}ms"
    )

    finder = AttackPathFinder(store)

    latencies_ms: list[float] = []

    logger.info(f"Executing {iterations} attack path discovery queries...")
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = finder.discover_paths(max_depth=5)
        query_duration = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(query_duration)

    latencies_ms.sort()
    p50 = latencies_ms[int(len(latencies_ms) * 0.50)]
    p90 = latencies_ms[int(len(latencies_ms) * 0.90)]
    p95 = latencies_ms[int(len(latencies_ms) * 0.95)]
    p99 = latencies_ms[int(len(latencies_ms) * 0.99)]
    avg_latency = sum(latencies_ms) / len(latencies_ms)

    result = {
        "benchmark_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "construction_time_ms": round(build_time_ms, 2),
        "iterations": iterations,
        "min_latency_ms": round(min(latencies_ms), 2),
        "avg_latency_ms": round(avg_latency, 2),
        "p50_latency_ms": round(p50, 2),
        "p90_latency_ms": round(p90, 2),
        "p95_latency_ms": round(p95, 2),
        "p99_latency_ms": round(p99, 2),
        "target_p95_ms": 1000.0,
        "target_met": p95 < 1000.0,
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Benchmark results written to {output_path}")

    return result


if __name__ == "__main__":
    out_file = Path("artifacts/coverage/graph_benchmark.json")
    res = run_benchmark(target_nodes=10000, iterations=50, output_path=out_file)
    print(json.dumps(res, indent=2))
