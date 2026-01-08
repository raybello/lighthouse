"""Unit tests for TopologyService."""

import pytest
from lighthouse.domain.services.topology_service import TopologyService
from lighthouse.domain.models.workflow import Workflow
from lighthouse.domain.models.node import Node, NodeMetadata, NodeType
from lighthouse.domain.models.field_types import FieldDefinition, FieldType
from lighthouse.domain.exceptions import CycleDetectedError


@pytest.fixture
def topology_service():
    """Create a TopologyService instance."""
    return TopologyService()


@pytest.fixture
def node_metadata():
    """Create sample node metadata."""
    return NodeMetadata(
        node_type=NodeType.EXECUTION,
        name="TestNode",
        description="Test node",
        version="1.0.0",
        fields=[
            FieldDefinition(
                name="test", label="Test", field_type=FieldType.STRING, default_value=""
            )
        ],
    )


def create_node(node_id: str, name: str, metadata: NodeMetadata) -> Node:
    """Helper to create a node."""
    return Node(id=node_id, name=name, node_type="TestNode", state={}, metadata=metadata)


class TestBasicTopologicalSort:
    """Tests for basic topological sorting."""

    def test_empty_workflow(self, topology_service):
        """Test sorting empty workflow."""
        workflow = Workflow(id="test", name="Empty")
        result = topology_service.topological_sort(workflow)
        assert result == []

    def test_single_node(self, topology_service, node_metadata):
        """Test sorting workflow with single node."""
        workflow = Workflow(id="test", name="Single")
        node = create_node("node1", "Node 1", node_metadata)
        workflow.add_node(node)

        result = topology_service.topological_sort(workflow)
        assert result == ["node1"]

    def test_linear_chain(self, topology_service, node_metadata):
        """Test sorting linear chain: A → B → C."""
        workflow = Workflow(id="test", name="Linear")

        for i in range(1, 4):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node2", "node3")

        result = topology_service.topological_sort(workflow)
        assert result == ["node1", "node2", "node3"]

    def test_branching_workflow(self, topology_service, node_metadata):
        """Test sorting branching workflow: A → B, A → C."""
        workflow = Workflow(id="test", name="Branch")

        for i in range(1, 4):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node1", "node3")

        result = topology_service.topological_sort(workflow)

        # node1 must come first
        assert result[0] == "node1"
        # node2 and node3 can be in any order
        assert set(result[1:]) == {"node2", "node3"}

    def test_diamond_dependency(self, topology_service, node_metadata):
        """Test sorting diamond: A → B, A → C, B → D, C → D."""
        workflow = Workflow(id="test", name="Diamond")

        for i in range(1, 5):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node1", "node3")
        workflow.add_connection("node2", "node4")
        workflow.add_connection("node3", "node4")

        result = topology_service.topological_sort(workflow)

        # node1 must be first, node4 must be last
        assert result[0] == "node1"
        assert result[3] == "node4"
        # node2 and node3 must be in the middle
        assert set(result[1:3]) == {"node2", "node3"}


class TestCycleDetection:
    """Tests for cycle detection."""

    def test_detect_simple_cycle(self, topology_service, node_metadata):
        """Test detecting simple cycle: A → B → A."""
        workflow = Workflow(id="test", name="Cycle")

        node1 = create_node("node1", "Node 1", node_metadata)
        node2 = create_node("node2", "Node 2", node_metadata)
        workflow.add_node(node1)
        workflow.add_node(node2)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node2", "node1")

        with pytest.raises(CycleDetectedError, match="Cycle detected"):
            topology_service.topological_sort(workflow)

    def test_detect_cycle_method(self, topology_service, node_metadata):
        """Test detect_cycle method returns True for cycles."""
        workflow = Workflow(id="test", name="Cycle")

        node1 = create_node("node1", "Node 1", node_metadata)
        node2 = create_node("node2", "Node 2", node_metadata)
        workflow.add_node(node1)
        workflow.add_node(node2)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node2", "node1")

        assert topology_service.detect_cycle(workflow) is True

    def test_no_cycle_in_dag(self, topology_service, node_metadata):
        """Test that DAG returns False for cycle detection."""
        workflow = Workflow(id="test", name="DAG")

        for i in range(1, 4):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node2", "node3")

        assert topology_service.detect_cycle(workflow) is False

    def test_detect_self_loop(self, topology_service, node_metadata):
        """Test detecting self-loop cycle: A → A."""
        workflow = Workflow(id="test", name="SelfLoop")
        node = create_node("node1", "Node 1", node_metadata)
        workflow.add_node(node)
        workflow.add_connection("node1", "node1")

        with pytest.raises(CycleDetectedError):
            topology_service.topological_sort(workflow)


class TestDependencyAnalysis:
    """Tests for dependency finding."""

    def test_find_dependencies_linear(self, topology_service, node_metadata):
        """Test finding dependencies in linear chain."""
        workflow = Workflow(id="test", name="Linear")

        for i in range(1, 5):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node2", "node3")
        workflow.add_connection("node3", "node4")

        deps = topology_service.find_dependencies(workflow, "node4")
        assert set(deps) == {"node1", "node2", "node3"}

    def test_find_dependencies_no_deps(self, topology_service, node_metadata):
        """Test finding dependencies for root node."""
        workflow = Workflow(id="test", name="Root")
        node = create_node("node1", "Node 1", node_metadata)
        workflow.add_node(node)

        deps = topology_service.find_dependencies(workflow, "node1")
        assert deps == []

    def test_find_dependencies_diamond(self, topology_service, node_metadata):
        """Test finding dependencies in diamond graph."""
        workflow = Workflow(id="test", name="Diamond")

        for i in range(1, 5):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node1", "node3")
        workflow.add_connection("node2", "node4")
        workflow.add_connection("node3", "node4")

        deps = topology_service.find_dependencies(workflow, "node4")
        assert set(deps) == {"node1", "node2", "node3"}

    def test_find_dependents(self, topology_service, node_metadata):
        """Test finding downstream dependents."""
        workflow = Workflow(id="test", name="Dependents")

        for i in range(1, 5):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node1", "node3")
        workflow.add_connection("node2", "node4")

        dependents = topology_service.find_dependents(workflow, "node1")
        assert set(dependents) == {"node2", "node3", "node4"}

    def test_find_dependents_leaf_node(self, topology_service, node_metadata):
        """Test finding dependents for leaf node."""
        workflow = Workflow(id="test", name="Leaf")

        for i in range(1, 3):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")

        dependents = topology_service.find_dependents(workflow, "node2")
        assert dependents == []


class TestReachability:
    """Tests for reachability checks."""

    def test_is_reachable_direct(self, topology_service, node_metadata):
        """Test reachability with direct connection."""
        workflow = Workflow(id="test", name="Direct")

        node1 = create_node("node1", "Node 1", node_metadata)
        node2 = create_node("node2", "Node 2", node_metadata)
        workflow.add_node(node1)
        workflow.add_node(node2)
        workflow.add_connection("node1", "node2")

        assert topology_service.is_reachable(workflow, "node1", "node2") is True
        assert topology_service.is_reachable(workflow, "node2", "node1") is False

    def test_is_reachable_indirect(self, topology_service, node_metadata):
        """Test reachability with indirect path."""
        workflow = Workflow(id="test", name="Indirect")

        for i in range(1, 4):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node2", "node3")

        assert topology_service.is_reachable(workflow, "node1", "node3") is True

    def test_is_reachable_same_node(self, topology_service, node_metadata):
        """Test reachability from node to itself."""
        workflow = Workflow(id="test", name="Same")
        node = create_node("node1", "Node 1", node_metadata)
        workflow.add_node(node)

        assert topology_service.is_reachable(workflow, "node1", "node1") is True

    def test_is_reachable_not_connected(self, topology_service, node_metadata):
        """Test reachability with no path."""
        workflow = Workflow(id="test", name="Disconnected")

        node1 = create_node("node1", "Node 1", node_metadata)
        node2 = create_node("node2", "Node 2", node_metadata)
        workflow.add_node(node1)
        workflow.add_node(node2)

        assert topology_service.is_reachable(workflow, "node1", "node2") is False


class TestExecutionLevels:
    """Tests for execution level grouping."""

    def test_execution_levels_linear(self, topology_service, node_metadata):
        """Test execution levels for linear chain."""
        workflow = Workflow(id="test", name="Linear")

        for i in range(1, 4):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node2", "node3")

        levels = topology_service.get_execution_levels(workflow)

        assert len(levels) == 3
        assert levels[0] == ["node1"]
        assert levels[1] == ["node2"]
        assert levels[2] == ["node3"]

    def test_execution_levels_parallel(self, topology_service, node_metadata):
        """Test execution levels with parallel branches."""
        workflow = Workflow(id="test", name="Parallel")

        for i in range(1, 4):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node1", "node3")

        levels = topology_service.get_execution_levels(workflow)

        assert len(levels) == 2
        assert levels[0] == ["node1"]
        assert set(levels[1]) == {"node2", "node3"}

    def test_execution_levels_with_cycle(self, topology_service, node_metadata):
        """Test that execution levels raises error for cycles."""
        workflow = Workflow(id="test", name="Cycle")

        node1 = create_node("node1", "Node 1", node_metadata)
        node2 = create_node("node2", "Node 2", node_metadata)
        workflow.add_node(node1)
        workflow.add_node(node2)
        workflow.add_connection("node1", "node2")
        workflow.add_connection("node2", "node1")

        with pytest.raises(CycleDetectedError):
            topology_service.get_execution_levels(workflow)


class TestConnectionValidation:
    """Tests for connection validation."""

    def test_validate_connection_valid(self, topology_service, node_metadata):
        """Test validating a valid connection."""
        workflow = Workflow(id="test", name="Valid")

        node1 = create_node("node1", "Node 1", node_metadata)
        node2 = create_node("node2", "Node 2", node_metadata)
        workflow.add_node(node1)
        workflow.add_node(node2)

        is_valid, error = topology_service.validate_connection(workflow, "node1", "node2")
        assert is_valid is True
        assert error == ""

    def test_validate_connection_self_loop(self, topology_service, node_metadata):
        """Test validating self-loop connection."""
        workflow = Workflow(id="test", name="SelfLoop")
        node = create_node("node1", "Node 1", node_metadata)
        workflow.add_node(node)

        is_valid, error = topology_service.validate_connection(workflow, "node1", "node1")
        assert is_valid is False
        assert "self-loop" in error.lower()

    def test_validate_connection_creates_cycle(self, topology_service, node_metadata):
        """Test validating connection that would create cycle."""
        workflow = Workflow(id="test", name="WouldCycle")

        for i in range(1, 4):
            node = create_node(f"node{i}", f"Node {i}", node_metadata)
            workflow.add_node(node)

        workflow.add_connection("node1", "node2")
        workflow.add_connection("node2", "node3")

        # Adding node3 → node1 would create a cycle
        is_valid, error = topology_service.validate_connection(workflow, "node3", "node1")
        assert is_valid is False
        assert "cycle" in error.lower()

    def test_validate_connection_nonexistent_node(self, topology_service, node_metadata):
        """Test validating connection with non-existent node."""
        workflow = Workflow(id="test", name="Missing")
        node = create_node("node1", "Node 1", node_metadata)
        workflow.add_node(node)

        is_valid, error = topology_service.validate_connection(workflow, "node1", "nonexistent")
        assert is_valid is False
        assert "not found" in error.lower()
