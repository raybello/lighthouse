"""Node domain models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from lighthouse.domain.models.field_types import FieldDefinition


class NodeType(Enum):
    """Node type categorization."""

    TRIGGER = "trigger"
    EXECUTION = "execution"


@dataclass
class NodeMetadata:
    """
    Metadata describing a node type.

    Provides information about the node's capabilities, configuration,
    and behavior without coupling to any UI framework.
    """

    node_type: NodeType
    name: str
    description: str
    version: str
    fields: list[FieldDefinition]
    has_inputs: bool = True
    has_config: bool = True
    icon: Optional[str] = None
    category: Optional[str] = None


@dataclass
class ExecutionResult:
    """
    Result of node execution.

    Encapsulates the output of a node's execute() method,
    including success/failure status, output data, and errors.
    """

    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    duration_seconds: float = 0.0
    logs: list[str] = field(default_factory=list)

    @classmethod
    def success_result(cls, data: Dict[str, Any], duration: float = 0.0) -> "ExecutionResult":
        """Create a successful execution result."""
        return cls(success=True, data=data, duration_seconds=duration)

    @classmethod
    def error_result(cls, error: str, duration: float = 0.0) -> "ExecutionResult":
        """Create a failed execution result."""
        return cls(success=False, data={}, error=error, duration_seconds=duration)


@dataclass
class Node:
    """
    Domain model for a workflow node.

    This is a pure domain object with NO UI dependencies.
    UI rendering is handled separately by INodeRenderer implementations.

    Attributes:
        id: Unique node identifier (UUID)
        name: Display name
        node_type: Type of node (for categorization)
        state: Current configuration state
        metadata: Node type metadata
        status: Execution status (PENDING, RUNNING, COMPLETED, ERROR)
    """

    id: str
    name: str
    node_type: str
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[NodeMetadata] = None
    status: str = "PENDING"
    last_output: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate node after initialization."""
        if self.metadata is None:
            raise ValueError(f"Node {self.id} must have metadata")

    def update_state(self, new_state: Dict[str, Any]) -> None:
        """
        Update node configuration state.

        Args:
            new_state: New state values to merge with existing state
        """
        self.state.update(new_state)

    def reset_status(self) -> None:
        """Reset node status to PENDING."""
        self.status = "PENDING"
        self.last_output = None

    def set_status(self, status: str) -> None:
        """
        Set node execution status.

        Args:
            status: One of PENDING, RUNNING, COMPLETED, ERROR
        """
        valid_statuses = {"PENDING", "RUNNING", "COMPLETED", "ERROR"}
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        self.status = status

    def store_output(self, output: Dict[str, Any]) -> None:
        """
        Store the last execution output.

        Args:
            output: Output data from execution
        """
        self.last_output = output

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize node to dictionary.

        Returns:
            Dictionary representation of the node
        """
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type,
            "state": self.state,
            "status": self.status,
            "last_output": self.last_output,
        }
