"""
Node registry for dynamic node discovery and instantiation.

Provides a centralized registry for all available node types.
"""

from typing import Dict, List, Type

from lighthouse.nodes.base.base_node import BaseNode, ExecutionNode, TriggerNode
from lighthouse.nodes.execution.calculator_node import CalculatorNode
from lighthouse.nodes.execution.chat_model_node import ChatModelNode
from lighthouse.nodes.execution.code_node import CodeNode
from lighthouse.nodes.execution.command_node import ExecuteCommandNode
from lighthouse.nodes.execution.form_node import FormNode
from lighthouse.nodes.execution.http_node import HTTPRequestNode
from lighthouse.nodes.trigger.input_node import InputNode

# Import all node implementations
from lighthouse.nodes.trigger.manual_trigger_node import ManualTriggerNode


class NodeRegistry:
    """
    Registry for all available node types.

    Provides dynamic node discovery and instantiation without hardcoded enums.
    Nodes are registered by category for organization.
    """

    def __init__(self):
        """Initialize the node registry with all available nodes."""
        self._nodes: Dict[str, Type[BaseNode]] = {}
        self._register_default_nodes()

    def _register_default_nodes(self) -> None:
        """Register all default node types."""
        # Trigger nodes
        self.register("ManualTrigger", ManualTriggerNode)
        self.register("Input", InputNode)

        # Execution nodes
        self.register("Calculator", CalculatorNode)
        self.register("HTTPRequest", HTTPRequestNode)
        self.register("ExecuteCommand", ExecuteCommandNode)
        self.register("Code", CodeNode)
        self.register("ChatModel", ChatModelNode)
        self.register("Form", FormNode)

    def register(self, node_type: str, node_class: Type[BaseNode]) -> None:
        """
        Register a node type.

        Args:
            node_type: Unique identifier for the node type
            node_class: Node class to register
        """
        if node_type in self._nodes:
            raise ValueError(f"Node type '{node_type}' is already registered")

        if not issubclass(node_class, BaseNode):
            raise TypeError("Node class must inherit from BaseNode")

        self._nodes[node_type] = node_class

    def unregister(self, node_type: str) -> None:
        """
        Unregister a node type.

        Args:
            node_type: Node type to unregister
        """
        if node_type in self._nodes:
            del self._nodes[node_type]

    def get_node_class(self, node_type: str) -> Type[BaseNode]:
        """
        Get a node class by type.

        Args:
            node_type: Node type identifier

        Returns:
            Node class

        Raises:
            KeyError: If node type is not registered
        """
        if node_type not in self._nodes:
            raise KeyError(f"Node type '{node_type}' is not registered")

        return self._nodes[node_type]

    def get_all_node_types(self) -> List[str]:
        """
        Get list of all registered node types.

        Returns:
            List of node type identifiers
        """
        return list(self._nodes.keys())

    def get_trigger_nodes(self) -> Dict[str, Type[TriggerNode]]:
        """
        Get all registered trigger nodes.

        Returns:
            Dictionary of trigger node types and classes
        """
        return {
            node_type: node_class
            for node_type, node_class in self._nodes.items()
            if issubclass(node_class, TriggerNode)
        }

    def get_execution_nodes(self) -> Dict[str, Type[ExecutionNode]]:
        """
        Get all registered execution nodes.

        Returns:
            Dictionary of execution node types and classes
        """
        return {
            node_type: node_class
            for node_type, node_class in self._nodes.items()
            if issubclass(node_class, ExecutionNode) and node_class is not ExecutionNode
        }

    def is_registered(self, node_type: str) -> bool:
        """
        Check if a node type is registered.

        Args:
            node_type: Node type to check

        Returns:
            True if registered, False otherwise
        """
        return node_type in self._nodes

    def get_node_count(self) -> int:
        """
        Get total number of registered nodes.

        Returns:
            Number of registered node types
        """
        return len(self._nodes)


# Global registry instance
_global_registry: NodeRegistry | None = None


def get_registry() -> NodeRegistry:
    """
    Get the global node registry instance.

    Returns:
        Global NodeRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = NodeRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (useful for testing)."""
    global _global_registry
    _global_registry = None
