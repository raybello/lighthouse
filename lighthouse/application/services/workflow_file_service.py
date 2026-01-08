"""
Workflow file service for saving/loading .lh files.

Handles file I/O operations for workflow files and coordinates
between serialization and node reconstruction.
"""

import json
from pathlib import Path
from typing import Dict, Tuple

from lighthouse.application.services.node_factory import NodeFactory
from lighthouse.domain.models.workflow import Workflow
from lighthouse.domain.services.workflow_serializer import WorkflowSerializer


class WorkflowFileService:
    """
    Service for saving and loading workflows to/from .lh files.

    Coordinates between WorkflowSerializer (data format) and NodeFactory
    (node reconstruction) to provide complete save/load functionality.
    """

    def __init__(self, serializer: WorkflowSerializer, node_factory: NodeFactory):
        """
        Initialize the workflow file service.

        Args:
            serializer: WorkflowSerializer for data conversion
            node_factory: NodeFactory for reconstructing nodes with metadata
        """
        self.serializer = serializer
        self.node_factory = node_factory

    def save_to_file(
        self,
        workflow: Workflow,
        positions: Dict[str, Tuple[float, float]],
        filepath: str,
    ) -> None:
        """
        Save a workflow to a .lh file.

        Args:
            workflow: The workflow to save
            positions: Dictionary mapping node_id -> (x, y) position
            filepath: Path to save the file (must end with .lh)

        Raises:
            ValueError: If filepath doesn't end with .lh
            IOError: If file cannot be written
        """
        # Validate file extension
        if not filepath.endswith(".lh"):
            raise ValueError(f"Invalid file extension. Expected .lh, got: {filepath}")

        # Serialize workflow
        data = self.serializer.serialize(workflow, positions)

        # Write to file
        try:
            path = Path(filepath)
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise IOError(f"Failed to write file {filepath}: {e}") from e

    def load_from_file(self, filepath: str) -> Tuple[Workflow, Dict[str, Tuple[float, float]]]:
        """
        Load a workflow from a .lh file.

        Args:
            filepath: Path to the .lh file to load

        Returns:
            Tuple of (Workflow, positions_dict)
            - Workflow: Reconstructed workflow with all nodes
            - positions_dict: Node positions {node_id: (x, y)}

        Raises:
            ValueError: If filepath doesn't end with .lh or data is invalid
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        # Validate file extension
        if not filepath.endswith(".lh"):
            raise ValueError(f"Invalid file extension. Expected .lh, got: {filepath}")

        # Read and parse JSON
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {filepath}: {e}") from e
        except IOError as e:
            raise IOError(f"Failed to read file {filepath}: {e}") from e

        # Deserialize (validates and extracts data)
        workflow_meta, nodes_data, connections_data, positions = self.serializer.deserialize(data)

        # Create workflow
        workflow = Workflow(
            id=workflow_meta["id"],
            name=workflow_meta["name"],
            description=workflow_meta.get("description", ""),
        )

        # Reconstruct nodes using NodeFactory
        for node_data in nodes_data:
            try:
                # Create node with proper metadata from factory
                node = self.node_factory.create_node(
                    node_type=node_data["node_type"],
                    name=node_data["name"],
                )

                # Restore ID and state
                node.id = node_data["id"]
                node.update_state(node_data["state"])

                # Add to workflow (BaseNode for execution)
                workflow.add_node(node)

            except Exception as e:
                raise ValueError(
                    f"Failed to reconstruct node {node_data.get('id', 'unknown')} "
                    f"of type {node_data.get('node_type', 'unknown')}: {e}"
                ) from e

        # Reconstruct connections
        for conn_data in connections_data:
            workflow.add_connection(conn_data["from_node_id"], conn_data["to_node_id"])

        return workflow, positions
