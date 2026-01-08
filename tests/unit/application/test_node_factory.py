"""Unit tests for NodeFactory."""

import pytest
from lighthouse.application.services.node_factory import NodeFactory
from lighthouse.nodes.registry import NodeRegistry, reset_registry
from lighthouse.nodes.base.base_node import BaseNode, ExecutionNode, TriggerNode
from lighthouse.nodes.execution.calculator_node import CalculatorNode
from lighthouse.nodes.trigger.manual_trigger_node import ManualTriggerNode


@pytest.fixture
def registry():
    """Create a fresh registry for testing."""
    reset_registry()
    return NodeRegistry()


@pytest.fixture
def factory(registry):
    """Create a node factory with test registry."""
    return NodeFactory(registry=registry)


class TestNodeFactoryInitialization:
    """Tests for factory initialization."""

    def test_factory_creation(self, factory):
        """Test creating a factory."""
        assert factory is not None
        assert factory.registry is not None

    def test_factory_with_custom_registry(self):
        """Test factory with custom registry."""
        custom_registry = NodeRegistry()
        factory = NodeFactory(registry=custom_registry)

        assert factory.registry is custom_registry

    def test_factory_uses_global_registry_by_default(self):
        """Test that factory uses global registry when none provided."""
        factory = NodeFactory()
        assert factory.registry is not None


class TestNodeCreation:
    """Tests for node creation."""

    def test_create_calculator_node(self, factory):
        """Test creating a calculator node."""
        node = factory.create_node("Calculator")

        assert isinstance(node, CalculatorNode)
        assert node.name == "Calculator"

    def test_create_node_with_custom_name(self, factory):
        """Test creating node with custom name."""
        node = factory.create_node("Calculator", name="MyCalculator")

        assert isinstance(node, CalculatorNode)
        assert node.name == "MyCalculator"

    def test_create_http_request_node(self, factory):
        """Test creating HTTP request node."""
        node = factory.create_node("HTTPRequest")

        assert node is not None
        assert node.name == "HTTPRequest"

    def test_create_manual_trigger_node(self, factory):
        """Test creating manual trigger node."""
        node = factory.create_node("ManualTrigger")

        assert isinstance(node, ManualTriggerNode)
        assert node.name == "ManualTrigger"

    def test_create_all_registered_nodes(self, factory):
        """Test that all registered node types can be created."""
        node_types = factory.get_available_node_types()

        for node_type in node_types:
            node = factory.create_node(node_type)
            assert node is not None
            assert isinstance(node, BaseNode)

    def test_create_nonexistent_node_raises_error(self, factory):
        """Test that creating nonexistent node raises KeyError."""
        with pytest.raises(KeyError):
            factory.create_node("NonexistentNode")


class TestTriggerNodeCreation:
    """Tests for trigger node creation."""

    def test_create_trigger_node(self, factory):
        """Test creating trigger node via dedicated method."""
        node = factory.create_trigger_node("ManualTrigger")

        assert isinstance(node, TriggerNode)
        assert node.name == "ManualTrigger"

    def test_create_trigger_node_with_custom_name(self, factory):
        """Test creating trigger node with custom name."""
        node = factory.create_trigger_node("Input", name="CustomInput")

        assert isinstance(node, TriggerNode)
        assert node.name == "CustomInput"

    def test_create_execution_node_as_trigger_fails(self, factory):
        """Test that execution nodes cannot be created as trigger nodes."""
        with pytest.raises(KeyError) as exc_info:
            factory.create_trigger_node("Calculator")

        assert "not a registered trigger node" in str(exc_info.value)

    def test_get_available_trigger_types(self, factory):
        """Test getting list of trigger types."""
        trigger_types = factory.get_available_trigger_types()

        assert "ManualTrigger" in trigger_types
        assert "Input" in trigger_types
        assert "Calculator" not in trigger_types


class TestExecutionNodeCreation:
    """Tests for execution node creation."""

    def test_create_execution_node(self, factory):
        """Test creating execution node via dedicated method."""
        node = factory.create_execution_node("Calculator")

        assert isinstance(node, ExecutionNode)
        assert node.name == "Calculator"

    def test_create_execution_node_with_custom_name(self, factory):
        """Test creating execution node with custom name."""
        node = factory.create_execution_node("HTTPRequest", name="MyAPI")

        assert isinstance(node, ExecutionNode)
        assert node.name == "MyAPI"

    def test_create_trigger_node_as_execution_fails(self, factory):
        """Test that trigger nodes cannot be created as execution nodes."""
        with pytest.raises(KeyError) as exc_info:
            factory.create_execution_node("ManualTrigger")

        assert "not a registered execution node" in str(exc_info.value)

    def test_get_available_execution_types(self, factory):
        """Test getting list of execution types."""
        execution_types = factory.get_available_execution_types()

        assert "Calculator" in execution_types
        assert "HTTPRequest" in execution_types
        assert "ChatModel" in execution_types
        assert "ManualTrigger" not in execution_types


class TestNodeTypeDiscovery:
    """Tests for node type discovery."""

    def test_get_all_node_types(self, factory):
        """Test getting all available node types."""
        all_types = factory.get_available_node_types()

        # Should have 8 nodes total
        assert len(all_types) == 8

        # Should include both trigger and execution nodes
        assert "ManualTrigger" in all_types
        assert "Input" in all_types
        assert "Calculator" in all_types
        assert "HTTPRequest" in all_types
        assert "ExecuteCommand" in all_types
        assert "Code" in all_types
        assert "ChatModel" in all_types
        assert "Form" in all_types

    def test_trigger_and_execution_types_are_distinct(self, factory):
        """Test that trigger and execution types don't overlap."""
        trigger_types = set(factory.get_available_trigger_types())
        execution_types = set(factory.get_available_execution_types())

        # No overlap
        assert len(trigger_types & execution_types) == 0

        # Union equals all types
        all_types = set(factory.get_available_node_types())
        assert trigger_types | execution_types == all_types


class TestNodeInstances:
    """Tests for node instance properties."""

    def test_created_nodes_have_unique_ids(self, factory):
        """Test that each created node has a unique ID."""
        node1 = factory.create_node("Calculator", name="Calc1")
        node2 = factory.create_node("Calculator", name="Calc2")

        assert node1.id != node2.id

    def test_created_nodes_are_independent(self, factory):
        """Test that created nodes are independent instances."""
        node1 = factory.create_node("Calculator")
        node2 = factory.create_node("Calculator")

        # Modify one node's state
        node1.set_state_value("field_a", "100")

        # Other node should be unaffected
        assert node2.get_state_value("field_a") != "100"

    def test_node_metadata_is_accessible(self, factory):
        """Test that created nodes have accessible metadata."""
        node = factory.create_node("Calculator")

        metadata = node.metadata
        assert metadata is not None
        assert metadata.name == "Calculator"
        assert len(metadata.fields) > 0
