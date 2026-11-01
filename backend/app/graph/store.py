"""GraphStore abstraction and NetworkX in-memory implementation."""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

import networkx as nx

from backend.app.core.exceptions import GraphQueryError
from backend.app.graph.models import GraphEdge, GraphNode, NodeType


class GraphStore(ABC):
    """Abstract interface for property graph backends (NetworkX, Neo4j, etc.)."""

    @abstractmethod
    def add_node(self, node: GraphNode) -> None:
        """Add or update a node in the graph."""
        pass

    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> None:
        """Add a directed relationship between existing nodes."""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> GraphNode | None:
        """Retrieve node by ID."""
        pass

    @abstractmethod
    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """Retrieve all nodes with a given NodeType."""
        pass

    @abstractmethod
    def get_out_edges(self, node_id: str) -> list[GraphEdge]:
        """Get outgoing edges from node."""
        pass

    @abstractmethod
    def get_in_edges(self, node_id: str) -> list[GraphEdge]:
        """Get incoming edges to node."""
        pass

    @abstractmethod
    def get_all_nodes(self) -> list[GraphNode]:
        """Return all nodes."""
        pass

    @abstractmethod
    def get_all_edges(self) -> list[GraphEdge]:
        """Return all edges."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all nodes and edges."""
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Export graph to JSON-serializable dictionary."""
        pass

    @abstractmethod
    def from_dict(self, data: dict[str, Any]) -> None:
        """Ingest graph from dictionary."""
        pass


class InMemoryGraphStore(GraphStore):
    """High-performance in-memory property graph store backed by NetworkX DiGraph."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._out_edges: dict[str, list[GraphEdge]] = defaultdict(list)
        self._in_edges: dict[str, list[GraphEdge]] = defaultdict(list)
        self._type_index: dict[NodeType, set[str]] = {t: set() for t in NodeType}

    def add_node(self, node: GraphNode) -> None:
        """Add or update a node with type indexing."""
        self._nodes[node.id] = node
        self._graph.add_node(node.id, node_type=node.type.value, name=node.name)
        self._type_index[node.type].add(node.id)

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge; validates both source and target exist."""
        if edge.source_id not in self._nodes:
            raise GraphQueryError(
                f"Source node '{edge.source_id}' does not exist in graph for edge {edge.type}"
            )
        if edge.target_id not in self._nodes:
            raise GraphQueryError(
                f"Target node '{edge.target_id}' does not exist in graph for edge {edge.type}"
            )

        self._edges[edge.id] = edge
        self._out_edges[edge.source_id].append(edge)
        self._in_edges[edge.target_id].append(edge)
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge.id,
            edge_type=edge.type.value,
            properties=edge.properties,
        )

    def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        node_ids = self._type_index.get(node_type, set())
        return [self._nodes[nid] for nid in node_ids]

    def get_out_edges(self, node_id: str) -> list[GraphEdge]:
        return self._out_edges.get(node_id, [])

    def get_in_edges(self, node_id: str) -> list[GraphEdge]:
        return self._in_edges.get(node_id, [])

    def get_all_nodes(self) -> list[GraphNode]:
        return list(self._nodes.values())

    def get_all_edges(self) -> list[GraphEdge]:
        return list(self._edges.values())

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    @property
    def networkx_graph(self) -> nx.DiGraph:
        """Return the underlying NetworkX DiGraph for traversal algorithms."""
        return self._graph

    def clear(self) -> None:
        self._graph.clear()
        self._nodes.clear()
        self._edges.clear()
        self._out_edges.clear()
        self._in_edges.clear()
        self._type_index = {t: set() for t in NodeType}

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.model_dump() for n in self._nodes.values()],
            "edges": [e.model_dump() for e in self._edges.values()],
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        self.clear()
        for n_raw in data.get("nodes", []):
            self.add_node(GraphNode(**n_raw))
        for e_raw in data.get("edges", []):
            self.add_edge(GraphEdge(**e_raw))
