"""Graph ingestion engine transforming collected cloud assets into property graph elements."""

from backend.app.collectors.models import NormalizedEnvironmentData
from backend.app.core.logging import logger
from backend.app.graph.models import GraphEdge, GraphNode, NodeType, RelationshipType
from backend.app.graph.store import GraphStore


class GraphIngestor:
    """Ingests normalized cloud asset data into a target GraphStore."""

    def __init__(self, store: GraphStore) -> None:
        self.store = store

    def ingest(self, data: NormalizedEnvironmentData) -> tuple[int, int]:
        """Ingest collected cloud data into the graph.

        Returns:
            tuple: (nodes_added_count, edges_added_count)
        """
        logger.info(
            f"Ingesting {data.total_asset_count} assets for account {data.account_id} into graph"
        )
        self.store.clear()

        # 1. Account Node
        account_node = GraphNode(
            id=f"account:{data.account_id}",
            type=NodeType.ACCOUNT,
            name=f"AWS-Account-{data.account_id}",
            account_id=data.account_id,
            properties={"source": data.source_type.value},
        )
        self.store.add_node(account_node)

        # 2. Public Internet Endpoint Node (Anchor for attack paths)
        public_internet_node = GraphNode(
            id="endpoint:public-internet",
            type=NodeType.PUBLIC_ENDPOINT,
            name="Public Internet (0.0.0.0/0)",
            account_id=data.account_id,
            properties={"description": "External unauthenticated entry point"},
        )
        self.store.add_node(public_internet_node)

        # 3. Policies Map
        policy_nodes: dict[str, GraphNode] = {}
        for pol in data.policies:
            pol_node = GraphNode(
                id=pol.arn or f"policy:{pol.policy_id}",
                type=NodeType.POLICY,
                name=pol.policy_name,
                account_id=data.account_id,
                properties={
                    "is_admin": pol.has_admin_privileges,
                    "is_inline": pol.is_inline,
                    "statements_count": len(pol.statements),
                },
            )
            self.store.add_node(pol_node)
            policy_nodes[pol_node.id] = pol_node

        # 4. IAM Users
        user_nodes: dict[str, GraphNode] = {}
        for user in data.iam_users:
            u_node = GraphNode(
                id=user.arn,
                type=NodeType.IAM_USER,
                name=user.user_name,
                account_id=data.account_id,
                properties={"user_id": user.user_id},
            )
            self.store.add_node(u_node)
            user_nodes[u_node.id] = u_node

            # Account contains User
            self.store.add_edge(
                GraphEdge(
                    source_id=account_node.id,
                    target_id=u_node.id,
                    type=RelationshipType.CONTAINS,
                )
            )

            # User -> Policy attachments
            for pol_arn in user.attached_policies:
                if pol_arn in policy_nodes:
                    self.store.add_edge(
                        GraphEdge(
                            source_id=u_node.id,
                            target_id=pol_arn,
                            type=RelationshipType.HAS_POLICY,
                        )
                    )

        # 5. IAM Roles
        role_nodes: dict[str, GraphNode] = {}
        role_name_to_arn: dict[str, str] = {}
        for role in data.iam_roles:
            r_node = GraphNode(
                id=role.arn,
                type=NodeType.IAM_ROLE,
                name=role.role_name,
                account_id=data.account_id,
                properties={
                    "role_id": role.role_id,
                    "is_instance_profile_role": role.is_instance_profile_role,
                    "trusted_principals": role.trusted_principals,
                },
            )
            self.store.add_node(r_node)
            role_nodes[r_node.id] = r_node
            role_name_to_arn[role.role_name] = role.arn

            # Account contains Role
            self.store.add_edge(
                GraphEdge(
                    source_id=account_node.id,
                    target_id=r_node.id,
                    type=RelationshipType.CONTAINS,
                )
            )

            # Role -> Policy attachments
            for pol_arn in role.attached_policies:
                if pol_arn in policy_nodes:
                    self.store.add_edge(
                        GraphEdge(
                            source_id=r_node.id,
                            target_id=pol_arn,
                            type=RelationshipType.HAS_POLICY,
                        )
                    )

        # 6. S3 Buckets
        bucket_nodes: dict[str, GraphNode] = {}
        for bucket in data.s3_buckets:
            b_node = GraphNode(
                id=bucket.arn,
                type=NodeType.S3_BUCKET,
                name=bucket.bucket_name,
                account_id=data.account_id,
                properties={
                    "is_public": bucket.is_public,
                    "public_access_block_enabled": bucket.public_access_block_enabled,
                    "criticality": "high"
                    if "confidential" in bucket.bucket_name.lower()
                    else "medium",
                },
            )
            self.store.add_node(b_node)
            bucket_nodes[b_node.id] = b_node

            # Account contains S3 Bucket
            self.store.add_edge(
                GraphEdge(
                    source_id=account_node.id,
                    target_id=b_node.id,
                    type=RelationshipType.CONTAINS,
                )
            )

            # If public, edge from Public Internet to S3 Bucket
            if bucket.is_public:
                self.store.add_edge(
                    GraphEdge(
                        source_id=public_internet_node.id,
                        target_id=b_node.id,
                        type=RelationshipType.EXPOSED_TO_INTERNET,
                        properties={"exposure_type": "public_bucket_policy"},
                    )
                )

        # 7. Role Trust & AssumeRole Edges
        for role in data.iam_roles:
            role_arn = role.arn
            for principal in role.trusted_principals:
                # If trusted principal is a role in our graph
                if principal in role_nodes:
                    self.store.add_edge(
                        GraphEdge(
                            source_id=principal,
                            target_id=role_arn,
                            type=RelationshipType.ASSUMES_ROLE,
                            properties={"mechanism": "sts:AssumeRole"},
                        )
                    )
                    self.store.add_edge(
                        GraphEdge(
                            source_id=role_arn,
                            target_id=principal,
                            type=RelationshipType.TRUSTS,
                        )
                    )

        # Also check policy statements granting sts:AssumeRole from users or roles
        for user in data.iam_users:
            for pol_arn in user.attached_policies:
                pol = next((p for p in data.policies if p.arn == pol_arn), None)
                if pol:
                    for stmt in pol.statements:
                        if stmt.effect.lower() == "allow" and any(
                            "assumerole" in a.lower() for a in stmt.actions
                        ):
                            for target_role in stmt.resources:
                                if target_role in role_nodes:
                                    self.store.add_edge(
                                        GraphEdge(
                                            source_id=user.arn,
                                            target_id=target_role,
                                            type=RelationshipType.ASSUMES_ROLE,
                                            properties={"via_policy": pol.policy_name},
                                        )
                                    )

        # 8. Security Groups
        sg_nodes: dict[str, GraphNode] = {}
        for sg in data.security_groups:
            sg_node = GraphNode(
                id=f"sg:{sg.group_id}",
                type=NodeType.SECURITY_GROUP,
                name=sg.group_name,
                account_id=data.account_id,
                properties={
                    "allows_internet_ingress": sg.allows_internet_ingress,
                    "vpc_id": sg.vpc_id,
                },
            )
            self.store.add_node(sg_node)
            sg_nodes[sg.group_id] = sg_node

            self.store.add_edge(
                GraphEdge(
                    source_id=account_node.id,
                    target_id=sg_node.id,
                    type=RelationshipType.CONTAINS,
                )
            )

        # 9. EC2 Instances & Compute Bindings
        for inst in data.ec2_instances:
            inst_node = GraphNode(
                id=f"ec2:{inst.instance_id}",
                type=NodeType.EC2_INSTANCE,
                name=f"EC2-{inst.instance_id}",
                account_id=data.account_id,
                properties={
                    "instance_type": inst.instance_type,
                    "public_ip": inst.public_ip,
                    "is_public": inst.is_publicly_exposed,
                    "associated_iam_role": inst.associated_iam_role,
                },
            )
            self.store.add_node(inst_node)

            self.store.add_edge(
                GraphEdge(
                    source_id=account_node.id,
                    target_id=inst_node.id,
                    type=RelationshipType.CONTAINS,
                )
            )

            # Security group attachments
            for sg_id in inst.security_group_ids:
                if sg_id in sg_nodes:
                    self.store.add_edge(
                        GraphEdge(
                            source_id=inst_node.id,
                            target_id=sg_nodes[sg_id].id,
                            type=RelationshipType.ATTACHED_TO,
                        )
                    )

            # Public Exposure: if instance has public IP or SG allows 0.0.0.0/0
            has_open_sg = any(
                sg_nodes[sg_id].properties.get("allows_internet_ingress")
                for sg_id in inst.security_group_ids
                if sg_id in sg_nodes
            )
            if inst.is_publicly_exposed or has_open_sg:
                self.store.add_edge(
                    GraphEdge(
                        source_id=public_internet_node.id,
                        target_id=inst_node.id,
                        type=RelationshipType.EXPOSED_TO_INTERNET,
                        properties={"public_ip": inst.public_ip},
                    )
                )

            # Compute-to-Identity Binding: EC2 -> IAM Role
            role_arn = None
            if inst.associated_iam_role and inst.associated_iam_role in role_name_to_arn:
                role_arn = role_name_to_arn[inst.associated_iam_role]
            elif inst.instance_profile_name and inst.instance_profile_name in role_name_to_arn:
                role_arn = role_name_to_arn[inst.instance_profile_name]

            if role_arn and role_arn in role_nodes:
                self.store.add_edge(
                    GraphEdge(
                        source_id=inst_node.id,
                        target_id=role_arn,
                        type=RelationshipType.RUNS_AS,
                        properties={"instance_profile": inst.instance_profile_name},
                    )
                )

        # 10. Role S3 Access Edges
        for role in data.iam_roles:
            for pol_arn in role.attached_policies:
                pol = next((p for p in data.policies if p.arn == pol_arn), None)
                if pol:
                    for stmt in pol.statements:
                        if stmt.effect.lower() == "allow":
                            for res_arn in stmt.resources:
                                base_bucket_arn = res_arn.split("/*")[0]
                                if base_bucket_arn in bucket_nodes:
                                    self.store.add_edge(
                                        GraphEdge(
                                            source_id=role.arn,
                                            target_id=base_bucket_arn,
                                            type=RelationshipType.CAN_ACCESS,
                                            properties={"actions": stmt.actions},
                                        )
                                    )

        nodes_count = len(self.store.get_all_nodes())
        edges_count = len(self.store.get_all_edges())
        logger.info(f"Ingested graph successfully: {nodes_count} nodes, {edges_count} edges")
        return nodes_count, edges_count
