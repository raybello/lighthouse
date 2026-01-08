"""Protocol defining the contract for workflow nodes."""

from typing import Protocol, Dict, Any
from lighthouse.domain.models.node import NodeMetadata, ExecutionResult


class INode(Protocol):
    """
    Protocol defining the contract for all node types.

    Nodes are pure domain objects with ZERO UI dependencies.
    All UI rendering is handled by INodeRenderer implementations.

    This protocol uses structural subtyping (PEP 544), meaning
    any class that implements these methods satisfies the protocol,
    regardless of inheritance.
    """

    @property
    def id(self) -> str:
        """
        Unique node identifier (UUID).

        Returns:
            Node ID string
        """
        ...

    @property
    def name(self) -> str:
        """
        Display name for the node.

        Returns:
            Node name string
        """
        ...

    @property
    def metadata(self) -> NodeMetadata:
        """
        Node metadata describing capabilities and configuration.

        Returns:
            NodeMetadata instance
        """
        ...

    @property
    def state(self) -> Dict[str, Any]:
        """
        Current node configuration state.

        Returns:
            Dictionary of state values
        """
        ...

    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the node's business logic.

        This is a PURE function with no side effects:
        - No logging (use ExecutionResult.logs instead)
        - No UI updates
        - No file I/O (unless that's the node's purpose)
        - Deterministic (same inputs → same outputs)

        Args:
            context: Execution context with upstream node outputs
                    Format: {node_name: {"data": {...}}}

        Returns:
            ExecutionResult with output data or error
        """
        ...

    def validate(self) -> list[str]:
        """
        Validate node configuration.

        Checks that all required fields are set and valid.
        Should NOT perform execution, just validate state.

        Returns:
            List of validation error messages (empty if valid)
        """
        ...

    def update_state(self, new_state: Dict[str, Any]) -> None:
        """
        Update node configuration state.

        Args:
            new_state: New state values to merge with existing state
        """
        ...
