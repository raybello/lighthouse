"""
Base node abstraction for workflow nodes.

This is a pure domain class with ZERO UI dependencies.
All UI rendering is handled separately by INodeRenderer implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid

from lighthouse.domain.models.node import Node, NodeMetadata, ExecutionResult
from lighthouse.domain.protocols.node_protocol import INode


class BaseNode(ABC):
    """
    Abstract base class for all workflow nodes.

    This is a PURE domain object with no UI dependencies.
    Nodes contain only business logic - execution, validation, and state management.
    All UI concerns are handled by separate renderer implementations.

    Attributes:
        id: Unique node identifier (8-char UUID suffix)
        name: Display name
        _state: Internal node configuration state
        metadata: Node type metadata and field definitions
    """

    def __init__(
        self,
        name: str,
        node_id: Optional[str] = None,
        initial_state: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a base node.

        Args:
            name: Display name for the node
            node_id: Optional node ID (generates if not provided)
            initial_state: Optional initial state dictionary
        """
        # Generate or use provided ID (8 chars for compatibility)
        self.id = node_id or str(uuid.uuid4())[-8:]
        self.name = name
        self._state: Dict[str, Any] = initial_state or {}
        self._status = "PENDING"
        self._last_output: Optional[Dict[str, Any]] = None

        # Initialize state with field defaults if not provided
        if not initial_state:
            self._state = self._get_default_state()

    @property
    @abstractmethod
    def metadata(self) -> NodeMetadata:
        """
        Get node metadata describing type, fields, and capabilities.

        Returns:
            NodeMetadata instance
        """
        pass

    @property
    def state(self) -> Dict[str, Any]:
        """
        Get current node state.

        Returns:
            State dictionary
        """
        return self._state.copy()

    @state.setter
    def state(self, value: Dict[str, Any]) -> None:
        """
        Set node state.

        Args:
            value: New state dictionary
        """
        self._state = value

    @property
    def status(self) -> str:
        """
        Get current execution status.

        Returns:
            Status string (PENDING, RUNNING, COMPLETED, ERROR)
        """
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        """
        Set execution status.

        Args:
            value: New status string
        """
        self._status = value

    def update_state(self, new_state: Dict[str, Any]) -> None:
        """
        Update node state with new values.

        Args:
            new_state: Dictionary of state updates
        """
        self._state.update(new_state)

    def get_state_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return self._state.get(key, default)

    def set_state_value(self, key: str, value: Any) -> None:
        """
        Set a specific state value.

        Args:
            key: State key
            value: Value to set
        """
        self._state[key] = value

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the node's business logic.

        This is the core method that each node type must implement.
        It should be a PURE function with no side effects (no logging,
        no UI updates, no file I/O unless that's the node's purpose).

        Args:
            context: Execution context with upstream node outputs
                    Format: {node_name: {"data": {...}}}

        Returns:
            ExecutionResult with output data or error
        """
        pass

    def validate(self) -> List[str]:
        """
        Validate node configuration.

        Default implementation validates required fields based on metadata.
        Override to add custom validation logic.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        for field_def in self.metadata.fields:
            value = self._state.get(field_def.name)

            # Use FieldDefinition's validate_value method
            is_valid, error_msg = field_def.validate_value(value)
            if not is_valid:
                errors.append(error_msg)

        return errors

    def reset(self) -> None:
        """Reset node to initial state."""
        self._state = self._get_default_state()
        self._status = "PENDING"
        self._last_output = None

    def _get_default_state(self) -> Dict[str, Any]:
        """
        Get default state from field definitions.

        Returns:
            Dictionary of default field values
        """
        default_state = {}
        for field_def in self.metadata.fields:
            default_state[field_def.name] = field_def.default_value
        return default_state

    def to_domain_node(self) -> Node:
        """
        Convert to domain Node model.

        Returns:
            Node domain model instance
        """
        return Node(
            id=self.id,
            name=self.name,
            node_type=self.metadata.name,
            state=self.state,
            metadata=self.metadata,
            status=self._status,
            last_output=self._last_output,
        )

    def __repr__(self) -> str:
        """String representation of node."""
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"


class TriggerNode(BaseNode):
    """
    Base class for trigger nodes (nodes with no inputs).

    Trigger nodes initiate workflow execution and typically
    have no incoming connections.
    """

    pass


class ExecutionNode(BaseNode):
    """
    Base class for execution nodes (nodes that process data).

    Execution nodes typically have inputs and perform some
    transformation or action on data.
    """

    pass
