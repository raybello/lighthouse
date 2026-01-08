"""Unit tests for NodeRegistry."""

import pytest

from lighthouse.nodes.base.base_node import ExecutionNode, TriggerNode
from lighthouse.nodes.execution.calculator_node import CalculatorNode
from lighthouse.nodes.registry import NodeRegistry, get_registry, reset_registry


class DummyNode(ExecutionNode):
    """Dummy node for testing."""

    pass


@pytest.fixture
def registry():
    """Create a fresh registry for testing."""
    reset_registry()
    return NodeRegistry()


class TestRegistryInitialization:
    """Tests for registry initialization."""

    def test_registry_creation(self, registry):
        """Test creating a registry."""
        assert registry is not None

    def test_registry_has_default_nodes(self, registry):
        """Test that registry comes with default nodes."""
        assert registry.get_node_count() == 8
        assert registry.is_registered("Calculator")
        assert registry.is_registered("ManualTrigger")

    def test_global_registry_singleton(self):
        """Test that global registry is a singleton."""
        reset_registry()
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2


class TestNodeRegistration:
    """Tests for node registration."""

    def test_register_new_node(self, registry):
        """Test registering a new node type."""
        initial_count = registry.get_node_count()

        registry.register("Dummy", DummyNode)

        assert registry.get_node_count() == initial_count + 1
        assert registry.is_registered("Dummy")

    def test_register_duplicate_raises_error(self, registry):
        """Test that registering duplicate type raises error."""
        with pytest.raises(ValueError) as exc_info:
            registry.register("Calculator", CalculatorNode)

        assert "already registered" in str(exc_info.value)

    def test_register_non_node_class_raises_error(self, registry):
        """Test that registering non-node class raises error."""

        class NotANode:
            pass

        with pytest.raises(TypeError) as exc_info:
            registry.register("NotNode", NotANode)

        assert "must inherit from BaseNode" in str(exc_info.value)


class TestNodeUnregistration:
    """Tests for node unregistration."""

    def test_unregister_existing_node(self, registry):
        """Test unregistering an existing node."""
        registry.register("Dummy", DummyNode)
        initial_count = registry.get_node_count()

        registry.unregister("Dummy")

        assert registry.get_node_count() == initial_count - 1
        assert not registry.is_registered("Dummy")

    def test_unregister_nonexistent_node_is_safe(self, registry):
        """Test that unregistering nonexistent node doesn't error."""
        # Should not raise an error
        registry.unregister("NonexistentNode")


class TestNodeRetrieval:
    """Tests for node retrieval."""

    def test_get_node_class(self, registry):
        """Test getting a node class."""
        node_class = registry.get_node_class("Calculator")

        assert node_class is CalculatorNode

    def test_get_nonexistent_node_raises_error(self, registry):
        """Test that getting nonexistent node raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            registry.get_node_class("NonexistentNode")

        assert "not registered" in str(exc_info.value)

    def test_get_all_node_types(self, registry):
        """Test getting all node types."""
        node_types = registry.get_all_node_types()

        assert len(node_types) == 8
        assert "Calculator" in node_types
        assert "ManualTrigger" in node_types


class TestTriggerNodeRetrieval:
    """Tests for trigger node retrieval."""

    def test_get_trigger_nodes(self, registry):
        """Test getting trigger nodes."""
        trigger_nodes = registry.get_trigger_nodes()

        assert "ManualTrigger" in trigger_nodes
        assert "Input" in trigger_nodes
        assert "Calculator" not in trigger_nodes

    def test_trigger_nodes_are_trigger_subclasses(self, registry):
        """Test that all trigger nodes are TriggerNode subclasses."""
        trigger_nodes = registry.get_trigger_nodes()

        for node_class in trigger_nodes.values():
            assert issubclass(node_class, TriggerNode)


class TestExecutionNodeRetrieval:
    """Tests for execution node retrieval."""

    def test_get_execution_nodes(self, registry):
        """Test getting execution nodes."""
        execution_nodes = registry.get_execution_nodes()

        assert "Calculator" in execution_nodes
        assert "HTTPRequest" in execution_nodes
        assert "ChatModel" in execution_nodes
        assert "ManualTrigger" not in execution_nodes

    def test_execution_nodes_are_execution_subclasses(self, registry):
        """Test that all execution nodes are ExecutionNode subclasses."""
        execution_nodes = registry.get_execution_nodes()

        for node_class in execution_nodes.values():
            assert issubclass(node_class, ExecutionNode)
            # Ensure it's not the base ExecutionNode class itself
            assert node_class is not ExecutionNode


class TestNodeClassification:
    """Tests for node classification."""

    def test_is_registered(self, registry):
        """Test checking if node is registered."""
        assert registry.is_registered("Calculator") is True
        assert registry.is_registered("ManualTrigger") is True
        assert registry.is_registered("NonexistentNode") is False

    def test_get_node_count(self, registry):
        """Test getting node count."""
        assert registry.get_node_count() == 8

        registry.register("Dummy", DummyNode)
        assert registry.get_node_count() == 9

        registry.unregister("Dummy")
        assert registry.get_node_count() == 8


class TestRegistryIsolation:
    """Tests for registry isolation."""

    def test_multiple_registries_are_independent(self):
        """Test that multiple registry instances are independent."""
        registry1 = NodeRegistry()
        registry2 = NodeRegistry()

        # Unregister from one
        registry1.unregister("Calculator")

        # Other should be unaffected
        assert registry1.is_registered("Calculator") is False
        assert registry2.is_registered("Calculator") is True

    def test_reset_global_registry(self):
        """Test resetting global registry."""
        # Get initial registry
        registry1 = get_registry()
        initial_id = id(registry1)

        # Reset
        reset_registry()

        # Get new registry
        registry2 = get_registry()
        new_id = id(registry2)

        # Should be different instances
        assert initial_id != new_id


class TestDefaultNodes:
    """Tests for default node registrations."""

    def test_all_default_nodes_registered(self, registry):
        """Test that all expected default nodes are registered."""
        expected_nodes = [
            "ManualTrigger",
            "Input",
            "Calculator",
            "HTTPRequest",
            "ExecuteCommand",
            "Code",
            "ChatModel",
            "Form",
        ]

        for node_type in expected_nodes:
            assert registry.is_registered(node_type), f"{node_type} should be registered"

    def test_trigger_nodes_count(self, registry):
        """Test number of trigger nodes."""
        trigger_nodes = registry.get_trigger_nodes()
        assert len(trigger_nodes) == 2

    def test_execution_nodes_count(self, registry):
        """Test number of execution nodes."""
        execution_nodes = registry.get_execution_nodes()
        assert len(execution_nodes) == 6
