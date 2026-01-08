"""Workflow domain models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from lighthouse.domain.exceptions import InvalidConnectionError, NodeNotFoundError
from lighthouse.domain.models.node import Node


@dataclass
class Connection:
    """
    Connection between two nodes in a workflow.

    Represents a directed edge in the workflow graph,
    indicating data/control flow from one node to another.
    """

    from_node_id: str
    to_node_id: str

    def __eq__(self, other):
        """Check equality based on node IDs."""
        if not isinstance(other, Connection):
            return False
        return self.from_node_id == other.from_node_id and self.to_node_id == other.to_node_id

    def __hash__(self):
        """Make connection hashable for use in sets."""
        return hash((self.from_node_id, self.to_node_id))


@dataclass
class Workflow:
    """
    Domain model for a workflow graph.

    Manages nodes and their connections with validation.
    Provides methods for graph operations like adding/removing nodes,
    creating connections, and retrieving topology information.

    Attributes:
        id: Unique workflow identifier
        name: Workflow display name
        nodes: Dictionary of node ID to Node instance
        connections: List of connections between nodes
        description: Optional workflow description
    """

    id: str
    name: str
    nodes: Dict[str, Node] = field(default_factory=dict)
    connections: List[Connection] = field(default_factory=list)
    description: Optional[str] = None

    def add_node(self, node: Node) -> None:
        """
        Add a node to the workflow.

        Args:
            node: Node to add

        Raises:
            ValueError: If node with same ID already exists
        """
        if node.id in self.nodes:
            raise ValueError(f"Node with ID {node.id} already exists in workflow")
        self.nodes[node.id] = node

    def remove_node(self, node_id: str) -> None:
        """
        Remove a node and all its connections from the workflow.

        Args:
            node_id: ID of node to remove

        Raises:
            NodeNotFoundError: If node doesn't exist
        """
        if node_id not in self.nodes:
            raise NodeNotFoundError(f"Node {node_id} not found in workflow")

        # Remove the node
        del self.nodes[node_id]

        # Remove all connections involving this node
        self.connections = [
            conn
            for conn in self.connections
            if conn.from_node_id != node_id and conn.to_node_id != node_id
        ]

    def add_connection(self, from_node: str, to_node: str) -> None:
        """
        Add a connection between two nodes.

        Args:
            from_node: Source node ID
            to_node: Target node ID

        Raises:
            NodeNotFoundError: If either node doesn't exist
            InvalidConnectionError: If connection already exists
        """
        # Validate nodes exist
        if from_node not in self.nodes:
            raise NodeNotFoundError(f"Source node {from_node} not found")
        if to_node not in self.nodes:
            raise NodeNotFoundError(f"Target node {to_node} not found")

        # Check for duplicate connection
        connection = Connection(from_node, to_node)
        if connection in self.connections:
            raise InvalidConnectionError(f"Connection from {from_node} to {to_node} already exists")

        self.connections.append(connection)

    def remove_connection(self, from_node: str, to_node: str) -> None:
        """
        Remove a connection between two nodes.

        Args:
            from_node: Source node ID
            to_node: Target node ID
        """
        connection = Connection(from_node, to_node)
        if connection in self.connections:
            self.connections.remove(connection)

    def get_node(self, node_id: str) -> Node:
        """
        Get a node by ID.

        Args:
            node_id: Node identifier

        Returns:
            Node instance

        Raises:
            NodeNotFoundError: If node doesn't exist
        """
        if node_id not in self.nodes:
            raise NodeNotFoundError(f"Node {node_id} not found")
        return self.nodes[node_id]

    def get_incoming_connections(self, node_id: str) -> List[str]:
        """
        Get list of node IDs that connect to the given node.

        Args:
            node_id: Target node ID

        Returns:
            List of source node IDs
        """
        return [conn.from_node_id for conn in self.connections if conn.to_node_id == node_id]

    def get_outgoing_connections(self, node_id: str) -> List[str]:
        """
        Get list of node IDs that the given node connects to.

        Args:
            node_id: Source node ID

        Returns:
            List of target node IDs
        """
        return [conn.to_node_id for conn in self.connections if conn.from_node_id == node_id]

    def get_topology(self) -> Dict[str, List[str]]:
        """
        Get workflow topology as adjacency list.

        Returns:
            Dictionary mapping node_id -> list of incoming node_ids
        """
        adj_list = {node_id: [] for node_id in self.nodes.keys()}
        for conn in self.connections:
            adj_list[conn.to_node_id].append(conn.from_node_id)
        return adj_list

    def reset_all_statuses(self) -> None:
        """Reset all node statuses to PENDING."""
        for node in self.nodes.values():
            node.reset_status()

    def to_dict(self) -> Dict[str, any]:
        """
        Serialize workflow to dictionary.

        Returns:
            Dictionary representation of the workflow
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "connections": [
                {"from": conn.from_node_id, "to": conn.to_node_id} for conn in self.connections
            ],
        }
