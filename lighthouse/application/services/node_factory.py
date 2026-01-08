"""
Node factory for creating node instances.

Provides centralized node creation with dependency injection support.
"""

from typing import Optional

from lighthouse.nodes.base.base_node import BaseNode
from lighthouse.nodes.registry import NodeRegistry, get_registry


class NodeFactory:
    """
    Factory for creating node instances.

    Handles node instantiation using the registry and supports
    custom node names and configurations.
    """

    def __init__(self, registry: Optional[NodeRegistry] = None):
        """
        Initialize the node factory.

        Args:
            registry: Node registry to use (defaults to global registry)
        """
        self.registry = registry or get_registry()

    def create_node(self, node_type: str, name: Optional[str] = None) -> BaseNode:
        """
        Create a node instance by type.

        Args:
            node_type: Type of node to create (e.g., "Calculator", "HTTPRequest")
            name: Optional custom name for the node (defaults to node type)

        Returns:
            New node instance

        Raises:
            KeyError: If node type is not registered
        """
        node_class = self.registry.get_node_class(node_type)

        # Use custom name if provided, otherwise use node type
        node_name = name or node_type

        # Create node instance
        return node_class(name=node_name)

    def create_trigger_node(self, node_type: str, name: Optional[str] = None) -> BaseNode:
        """
        Create a trigger node instance.

        Args:
            node_type: Type of trigger node to create
            name: Optional custom name for the node

        Returns:
            New trigger node instance

        Raises:
            KeyError: If node type is not a registered trigger node
        """
        trigger_nodes = self.registry.get_trigger_nodes()

        if node_type not in trigger_nodes:
            raise KeyError(f"'{node_type}' is not a registered trigger node")

        return self.create_node(node_type, name)

    def create_execution_node(self, node_type: str, name: Optional[str] = None) -> BaseNode:
        """
        Create an execution node instance.

        Args:
            node_type: Type of execution node to create
            name: Optional custom name for the node

        Returns:
            New execution node instance

        Raises:
            KeyError: If node type is not a registered execution node
        """
        execution_nodes = self.registry.get_execution_nodes()

        if node_type not in execution_nodes:
            raise KeyError(f"'{node_type}' is not a registered execution node")

        return self.create_node(node_type, name)

    def get_available_node_types(self) -> list[str]:
        """
        Get list of all available node types.

        Returns:
            List of node type identifiers
        """
        return self.registry.get_all_node_types()

    def get_available_trigger_types(self) -> list[str]:
        """
        Get list of available trigger node types.

        Returns:
            List of trigger node type identifiers
        """
        return list(self.registry.get_trigger_nodes().keys())

    def get_available_execution_types(self) -> list[str]:
        """
        Get list of available execution node types.

        Returns:
            List of execution node type identifiers
        """
        return list(self.registry.get_execution_nodes().keys())
