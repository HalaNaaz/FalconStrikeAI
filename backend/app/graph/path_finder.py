"""Attack path discovery engine with bounded graph traversal."""

from collections import deque

from backend.app.core.logging import logger
from backend.app.graph.attack_path_models import AttackPath
from backend.app.graph.models import (
    GraphEdge,
    GraphNode,
    MisconfigurationFinding,
    NodeType,
    RelationshipType,
)
from backend.app.graph.path_ranker import AttackPathRanker
from backend.app.graph.store import InMemoryGraphStore


class AttackPathFinder:
    """Discovers reachable attack paths from entry nodes to high-value targets (FR-1.6)."""

    # Permitted edge types that represent actionable privilege traversal
    ACTIONABLE_EDGES = {
        RelationshipType.EXPOSED_TO_INTERNET.value,
        RelationshipType.RUNS_AS.value,
        RelationshipType.ASSUMES_ROLE.value,
        RelationshipType.CAN_ACCESS.value,
    }

    def __init__(self, store: InMemoryGraphStore) -> None:
        self.store = store
        self.ranker = AttackPathRanker()

    def _is_high_value_target(self, node: GraphNode) -> bool:
        """Identify high-value targets (crown jewels) in the environment."""
        # 1. Any IAM Role that has admin privileges attached or is flagged admin
        if node.type == NodeType.IAM_ROLE:
            if node.properties.get("is_admin"):
                return True
            out_edges = self.store.get_out_edges(node.id)
            for e in out_edges:
                if e.type == RelationshipType.HAS_POLICY:
                    pol_node = self.store.get_node(e.target_id)
                    if pol_node and pol_node.properties.get("is_admin"):
                        return True
            # Check by role name heuristic
            if "admin" in node.name.lower():
                return True

        # 2. Confidential S3 Data Buckets
        if node.type == NodeType.S3_BUCKET:
            if "confidential" in node.name.lower() or node.properties.get("criticality") == "high":
                return True

        return False

    def _get_entry_nodes(self, explicit_entry_id: str | None = None) -> list[GraphNode]:
        """Find candidate entry points (public internet anchor or specified node)."""
        if explicit_entry_id:
            node = self.store.get_node(explicit_entry_id)
            return [node] if node else []

        # Default: Public Internet Endpoint and any external exposed resources
        endpoints = self.store.get_nodes_by_type(NodeType.PUBLIC_ENDPOINT)
        if endpoints:
            return endpoints

        # Fallback: All IAM Users
        return self.store.get_nodes_by_type(NodeType.IAM_USER)

    def discover_paths(
        self,
        entry_node_id: str | None = None,
        target_node_id: str | None = None,
        max_depth: int = 6,
        findings: list[MisconfigurationFinding] | None = None,
    ) -> list[AttackPath]:
        """Discover and rank attack paths using bounded breadth-first search.

        Avoids cycles and deduplicates paths.
        """
        findings_list = findings or []
        entry_nodes = self._get_entry_nodes(entry_node_id)
        if not entry_nodes:
            logger.warning("No valid entry nodes found in graph.")
            return []

        # Find target nodes
        if target_node_id:
            target_node = self.store.get_node(target_node_id)
            target_nodes = [target_node] if target_node else []
        else:
            all_nodes = self.store.get_all_nodes()
            target_nodes = [n for n in all_nodes if self._is_high_value_target(n)]

        if not target_nodes:
            logger.warning("No high-value target assets identified in graph.")
            return []

        target_ids = {t.id for t in target_nodes}
        discovered_paths: list[AttackPath] = []
        seen_path_signatures: set[tuple[str, ...]] = set()

        for start_node in entry_nodes:
            # Queue elements: (current_node_id, [ordered_node_ids], [ordered_edge_objects])
            queue: deque[tuple[str, list[str], list[GraphEdge]]] = deque()
            queue.append((start_node.id, [start_node.id], []))

            while queue:
                curr_id, path_node_ids, path_edges = queue.popleft()

                # Check if current node is a target (and we have traversed at least one hop)
                if curr_id in target_ids and len(path_edges) > 0:
                    signature = tuple(path_node_ids)
                    if signature not in seen_path_signatures:
                        seen_path_signatures.add(signature)

                        ordered_nodes = [self.store.get_node(nid) for nid in path_node_ids]
                        # Filter out any None nodes defensively
                        valid_nodes = [n for n in ordered_nodes if n is not None]

                        entry = valid_nodes[0]
                        target = valid_nodes[-1]

                        # Calculate score and rank path
                        scored_path = self.ranker.rank_path(
                            entry_node=entry,
                            target_node=target,
                            ordered_nodes=valid_nodes,
                            ordered_edges=path_edges,
                            findings=findings_list,
                        )
                        discovered_paths.append(scored_path)

                # Prune if max depth reached
                if len(path_edges) >= max_depth:
                    continue

                # Explore outgoing edges
                out_edges = self.store.get_out_edges(curr_id)
                for edge in out_edges:
                    # Enforce valid privilege-traversal edge types
                    if edge.type.value not in self.ACTIONABLE_EDGES:
                        continue

                    next_id = edge.target_id
                    # Cycle prevention
                    if next_id not in path_node_ids:
                        queue.append(
                            (
                                next_id,
                                [*path_node_ids, next_id],
                                [*path_edges, edge],
                            )
                        )

        # Sort paths by risk score descending
        discovered_paths.sort(key=lambda p: p.risk_score, reverse=True)
        return discovered_paths
