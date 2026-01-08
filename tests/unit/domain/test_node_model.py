"""Unit tests for Node domain model."""

import pytest
from lighthouse.domain.models.node import Node, ExecutionResult


def test_node_creation(sample_node, sample_node_metadata):
    """Test creating a node with metadata."""
    assert sample_node.id == "test-node-123"
    assert sample_node.name == "Test Node"
    assert sample_node.node_type == "TestNode"
    assert sample_node.status == "PENDING"
    assert sample_node.metadata == sample_node_metadata


def test_node_requires_metadata():
    """Test that node creation fails without metadata."""
    with pytest.raises(ValueError, match="must have metadata"):
        Node(
            id="test-123",
            name="Test",
            node_type="Test",
            metadata=None
        )


def test_node_update_state(sample_node):
    """Test updating node state."""
    sample_node.update_state({"new_field": "new value"})
    assert sample_node.state["new_field"] == "new value"
    assert sample_node.state["test_field"] == "test value"  # Original preserved


def test_node_set_status(sample_node):
    """Test setting node execution status."""
    sample_node.set_status("RUNNING")
    assert sample_node.status == "RUNNING"

    sample_node.set_status("COMPLETED")
    assert sample_node.status == "COMPLETED"


def test_node_set_invalid_status(sample_node):
    """Test that invalid status raises error."""
    with pytest.raises(ValueError, match="Invalid status"):
        sample_node.set_status("INVALID_STATUS")


def test_node_reset_status(sample_node):
    """Test resetting node status."""
    sample_node.set_status("COMPLETED")
    sample_node.store_output({"result": "test"})

    sample_node.reset_status()

    assert sample_node.status == "PENDING"
    assert sample_node.last_output is None


def test_node_store_output(sample_node):
    """Test storing execution output."""
    output = {"data": {"result": 123}}
    sample_node.store_output(output)

    assert sample_node.last_output == output


def test_node_to_dict(sample_node):
    """Test serializing node to dictionary."""
    node_dict = sample_node.to_dict()

    assert node_dict["id"] == "test-node-123"
    assert node_dict["name"] == "Test Node"
    assert node_dict["node_type"] == "TestNode"
    assert node_dict["status"] == "PENDING"
    assert "state" in node_dict


def test_execution_result_success():
    """Test creating successful execution result."""
    result = ExecutionResult.success_result(
        data={"output": "value"},
        duration=1.5
    )

    assert result.success is True
    assert result.data == {"output": "value"}
    assert result.duration_seconds == 1.5
    assert result.error is None


def test_execution_result_error():
    """Test creating error execution result."""
    result = ExecutionResult.error_result(
        error="Something went wrong",
        duration=0.5
    )

    assert result.success is False
    assert result.data == {}
    assert result.error == "Something went wrong"
    assert result.duration_seconds == 0.5
