"""
Workflow serialization service.

Handles conversion between Workflow objects and JSON-serializable dictionaries
for saving/loading workflows to/from .lh files.
"""

from typing import Any, Dict, Tuple

from lighthouse.domain.models.workflow import Workflow


class WorkflowSerializer:
    """
    Service for serializing and deserializing workflows.

    Converts between domain Workflow objects and JSON-compatible dictionaries,
    preserving node configurations, connections, and UI positions.
    """

    VERSION = "1.0"

    def serialize(
        self, workflow: Workflow, positions: Dict[str, Tuple[float, float]]
    ) -> Dict[str, Any]:
        """
        Serialize a workflow to a JSON-compatible dictionary.

        Args:
            workflow: The workflow to serialize
            positions: Dictionary mapping node_id -> (x, y) position

        Returns:
            Dictionary ready for JSON encoding with structure:
            {
                "version": "1.0",
                "workflow": {...},
                "nodes": [...],
                "connections": [...]
            }
        """
        return {
            "version": self.VERSION,
            "workflow": {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description or "",
            },
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "node_type": (
                        node.metadata.name if hasattr(node, "metadata") else node.node_type
                    ),
                    "state": node.state,
                    "position": {
                        "x": positions.get(node.id, (0, 0))[0],
                        "y": positions.get(node.id, (0, 0))[1],
                    },
                }
                for node in workflow.nodes.values()
            ],
            "connections": [
                {
                    "from_node_id": conn.from_node_id,
                    "to_node_id": conn.to_node_id,
                }
                for conn in workflow.connections
            ],
        }

    def deserialize(
        self, data: Dict[str, Any]
    ) -> Tuple[
        Dict[str, Any],
        list[Dict[str, Any]],
        list[Dict[str, Any]],
        Dict[str, Tuple[float, float]],
    ]:
        """
        Deserialize workflow data from a JSON-compatible dictionary.

        Returns raw data that can be used to reconstruct the workflow.
        Actual node reconstruction must be done by WorkflowFileService
        using NodeFactory to properly create nodes with metadata.

        Args:
            data: Dictionary loaded from JSON with workflow data

        Returns:
            Tuple of (workflow_metadata, nodes_data, connections_data, positions_dict)
            - workflow_metadata: Dict with id, name, description
            - nodes_data: List of node data dicts
            - connections_data: List of connection data dicts
            - positions_dict: Node positions {node_id: (x, y)}

        Raises:
            ValueError: If data is invalid or version incompatible
        """
        # Validate version
        version = data.get("version")
        if version != self.VERSION:
            raise ValueError(
                f"Unsupported workflow file version: {version}. Expected version {self.VERSION}"
            )

        # Validate required fields
        if "workflow" not in data:
            raise ValueError("Missing required field: 'workflow'")
        if "nodes" not in data:
            raise ValueError("Missing required field: 'nodes'")
        if "connections" not in data:
            raise ValueError("Missing required field: 'connections'")

        workflow_data = data["workflow"]
        nodes_data = data["nodes"]
        connections_data = data["connections"]

        # Validate workflow metadata
        if "id" not in workflow_data:
            raise ValueError("Missing required field: 'workflow.id'")
        if "name" not in workflow_data:
            raise ValueError("Missing required field: 'workflow.name'")

        # Validate and extract node data
        positions: Dict[str, Tuple[float, float]] = {}
        node_ids = set()

        for node_data in nodes_data:
            # Validate node data
            if "id" not in node_data:
                raise ValueError("Node missing required field: 'id'")
            if "name" not in node_data:
                raise ValueError(f"Node {node_data.get('id')} missing field: 'name'")
            if "node_type" not in node_data:
                raise ValueError(f"Node {node_data.get('id')} missing field: 'node_type'")
            if "state" not in node_data:
                raise ValueError(f"Node {node_data.get('id')} missing field: 'state'")

            node_ids.add(node_data["id"])

            # Extract position
            position_data = node_data.get("position", {"x": 0, "y": 0})
            positions[node_data["id"]] = (
                float(position_data.get("x", 0)),
                float(position_data.get("y", 0)),
            )

        # Validate connections
        for conn_data in connections_data:
            # Validate connection data
            if "from_node_id" not in conn_data:
                raise ValueError("Connection missing required field: 'from_node_id'")
            if "to_node_id" not in conn_data:
                raise ValueError("Connection missing required field: 'to_node_id'")

            from_node_id = conn_data["from_node_id"]
            to_node_id = conn_data["to_node_id"]

            # Validate that referenced nodes exist
            if from_node_id not in node_ids:
                raise ValueError(f"Connection references non-existent node: {from_node_id}")
            if to_node_id not in node_ids:
                raise ValueError(f"Connection references non-existent node: {to_node_id}")

        return workflow_data, nodes_data, connections_data, positions
