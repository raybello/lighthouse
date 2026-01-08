"""Unit tests for Workflow domain model."""

import pytest

from lighthouse.domain.exceptions import InvalidConnectionError, NodeNotFoundError
from lighthouse.domain.models.workflow import Connection


def test_workflow_creation(empty_workflow):
    """Test creating an empty workflow."""
    assert empty_workflow.id == "workflow-1"
    assert empty_workflow.name == "Test Workflow"
    assert len(empty_workflow.nodes) == 0
    assert len(empty_workflow.connections) == 0


def test_add_node(empty_workflow, sample_node):
    """Test adding a node to workflow."""
    empty_workflow.add_node(sample_node)

    assert len(empty_workflow.nodes) == 1
    assert sample_node.id in empty_workflow.nodes
    assert empty_workflow.nodes[sample_node.id] == sample_node


def test_add_duplicate_node(empty_workflow, sample_node):
    """Test that adding duplicate node raises error."""
    empty_workflow.add_node(sample_node)

    with pytest.raises(ValueError, match="already exists"):
        empty_workflow.add_node(sample_node)


def test_remove_node(workflow_with_nodes):
    """Test removing a node from workflow."""
    initial_node_count = len(workflow_with_nodes.nodes)
    initial_conn_count = len(workflow_with_nodes.connections)

    workflow_with_nodes.remove_node("node-2")

    assert len(workflow_with_nodes.nodes) == initial_node_count - 1
    assert "node-2" not in workflow_with_nodes.nodes
    # Connections involving node-2 should be removed
    assert len(workflow_with_nodes.connections) < initial_conn_count


def test_remove_nonexistent_node(empty_workflow):
    """Test that removing non-existent node raises error."""
    with pytest.raises(NodeNotFoundError):
        empty_workflow.remove_node("nonexistent")


def test_add_connection(workflow_with_nodes):
    """Test adding a connection between nodes."""
    initial_count = len(workflow_with_nodes.connections)

    # This connection doesn't exist yet
    workflow_with_nodes.add_connection("node-1", "node-3")

    assert len(workflow_with_nodes.connections) == initial_count + 1


def test_add_connection_nonexistent_node(workflow_with_nodes):
    """Test that connecting to non-existent node raises error."""
    with pytest.raises(NodeNotFoundError):
        workflow_with_nodes.add_connection("node-1", "nonexistent")


def test_add_duplicate_connection(workflow_with_nodes):
    """Test that adding duplicate connection raises error."""
    with pytest.raises(InvalidConnectionError, match="already exists"):
        # This connection already exists (from fixture)
        workflow_with_nodes.add_connection("node-1", "node-2")


def test_remove_connection(workflow_with_nodes):
    """Test removing a connection."""
    initial_count = len(workflow_with_nodes.connections)

    workflow_with_nodes.remove_connection("node-1", "node-2")

    assert len(workflow_with_nodes.connections) == initial_count - 1


def test_get_node(workflow_with_nodes):
    """Test retrieving a node by ID."""
    node = workflow_with_nodes.get_node("node-1")

    assert node.id == "node-1"
    assert node.name == "Node 1"


def test_get_nonexistent_node(workflow_with_nodes):
    """Test that getting non-existent node raises error."""
    with pytest.raises(NodeNotFoundError):
        workflow_with_nodes.get_node("nonexistent")


def test_get_incoming_connections(workflow_with_nodes):
    """Test getting incoming connections for a node."""
    # node-2 has incoming connection from node-1
    incoming = workflow_with_nodes.get_incoming_connections("node-2")

    assert len(incoming) == 1
    assert "node-1" in incoming


def test_get_outgoing_connections(workflow_with_nodes):
    """Test getting outgoing connections for a node."""
    # node-2 has outgoing connection to node-3
    outgoing = workflow_with_nodes.get_outgoing_connections("node-2")

    assert len(outgoing) == 1
    assert "node-3" in outgoing


def test_get_topology(workflow_with_nodes):
    """Test getting workflow topology as adjacency list."""
    topology = workflow_with_nodes.get_topology()

    assert isinstance(topology, dict)
    assert "node-1" in topology
    assert "node-2" in topology
    assert "node-3" in topology

    # node-2 has node-1 as incoming
    assert "node-1" in topology["node-2"]
    # node-3 has node-2 as incoming
    assert "node-2" in topology["node-3"]


def test_reset_all_statuses(workflow_with_nodes):
    """Test resetting all node statuses."""
    # Set some nodes to different statuses
    workflow_with_nodes.get_node("node-1").set_status("COMPLETED")
    workflow_with_nodes.get_node("node-2").set_status("ERROR")

    workflow_with_nodes.reset_all_statuses()

    # All should be PENDING now
    for node in workflow_with_nodes.nodes.values():
        assert node.status == "PENDING"


def test_workflow_to_dict(workflow_with_nodes):
    """Test serializing workflow to dictionary."""
    workflow_dict = workflow_with_nodes.to_dict()

    assert workflow_dict["id"] == "workflow-1"
    assert workflow_dict["name"] == "Test Workflow"
    assert len(workflow_dict["nodes"]) == 3
    assert len(workflow_dict["connections"]) == 2


def test_connection_equality():
    """Test connection equality comparison."""
    conn1 = Connection("node-1", "node-2")
    conn2 = Connection("node-1", "node-2")
    conn3 = Connection("node-2", "node-3")

    assert conn1 == conn2
    assert conn1 != conn3

    # Test with set (requires __hash__)
    connections = {conn1, conn2, conn3}
    assert len(connections) == 2  # conn1 and conn2 are duplicates
