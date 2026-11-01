"""Optional Neo4j property graph backend using official Cypher driver."""

from typing import Any

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.graph.models import GraphEdge, GraphNode, NodeType
from backend.app.graph.store import GraphStore


class Neo4jGraphStore(GraphStore):
    """Neo4j graph store utilizing Cypher queries."""

    def __init__(self) -> None:
        self.driver: Any = None
        self._connected = False
        if settings.neo4j_enabled:
            self._init_driver()

    def _init_driver(self) -> None:
        try:
            from neo4j import GraphDatabase

            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            self._connected = True
            logger.info("Connected to Neo4j graph database.")
        except Exception as exc:
            logger.warning(f"Neo4j driver initialization failed (falling back to in-memory): {exc}")
            self.driver = None
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def add_node(self, node: GraphNode) -> None:
        if not self._connected or not self.driver:
            return
        query = (
            f"MERGE (n:{node.type.value} {{id: $id}}) "
            "SET n.name = $name, n.account_id = $account_id, n += $properties"
        )
        with self.driver.session() as session:
            session.run(
                query,
                id=node.id,
                name=node.name,
                account_id=node.account_id,
                properties=node.properties,
            )

    def add_edge(self, edge: GraphEdge) -> None:
        if not self._connected or not self.driver:
            return
        query = (
            "MATCH (a {id: $source_id}), (b {id: $target_id}) "
            f"MERGE (a)-[r:{edge.type.value} {{id: $id}}]->(b) "
            "SET r += $properties"
        )
        with self.driver.session() as session:
            session.run(
                query,
                source_id=edge.source_id,
                target_id=edge.target_id,
                id=edge.id,
                properties=edge.properties,
            )

    def get_node(self, node_id: str) -> GraphNode | None:
        if not self._connected or not self.driver:
            return None
        query = "MATCH (n {id: $id}) RETURN n.id as id, labels(n)[0] as type, n.name as name, n.account_id as account_id, properties(n) as properties"
        with self.driver.session() as session:
            result = session.run(query, id=node_id).single()
            if result:
                return GraphNode(
                    id=result["id"],
                    type=NodeType(result["type"]),
                    name=result["name"],
                    account_id=result["account_id"],
                    properties=result["properties"],
                )
        return None

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        if not self._connected or not self.driver:
            return []
        query = (
            f"MATCH (n:{node_type.value}) "
            "RETURN n.id as id, n.name as name, n.account_id as account_id, properties(n) as properties"
        )
        nodes = []
        with self.driver.session() as session:
            for record in session.run(query):
                nodes.append(
                    GraphNode(
                        id=record["id"],
                        type=node_type,
                        name=record["name"],
                        account_id=record["account_id"],
                        properties=record["properties"],
                    )
                )
        return nodes

    def get_out_edges(self, node_id: str) -> list[GraphEdge]:
        if not self._connected or not self.driver:
            return []
        query = (
            "MATCH (a {id: $id})-[r]->(b) "
            "RETURN r.id as id, a.id as source_id, b.id as target_id, type(r) as type, properties(r) as properties"
        )
        edges = []
        with self.driver.session() as session:
            for record in session.run(query, id=node_id):
                edges.append(
                    GraphEdge(
                        id=record["id"],
                        source_id=record["source_id"],
                        target_id=record["target_id"],
                        type=record["type"],
                        properties=record["properties"],
                    )
                )
        return edges

    def get_in_edges(self, node_id: str) -> list[GraphEdge]:
        if not self._connected or not self.driver:
            return []
        query = (
            "MATCH (a)-[r]->(b {id: $id}) "
            "RETURN r.id as id, a.id as source_id, b.id as target_id, type(r) as type, properties(r) as properties"
        )
        edges = []
        with self.driver.session() as session:
            for record in session.run(query, id=node_id):
                edges.append(
                    GraphEdge(
                        id=record["id"],
                        source_id=record["source_id"],
                        target_id=record["target_id"],
                        type=record["type"],
                        properties=record["properties"],
                    )
                )
        return edges

    def get_all_nodes(self) -> list[GraphNode]:
        return []

    def get_all_edges(self) -> list[GraphEdge]:
        return []

    def clear(self) -> None:
        if self._connected and self.driver:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": [], "edges": []}

    def from_dict(self, data: dict[str, Any]) -> None:
        pass
