"""Pytest fixtures for Lighthouse tests."""

import pytest

from lighthouse.domain.models.field_types import FieldDefinition, FieldType
from lighthouse.domain.models.node import Node, NodeMetadata, NodeType
from lighthouse.domain.models.workflow import Workflow


@pytest.fixture
def sample_node_metadata():
    """Create sample node metadata for testing."""
    return NodeMetadata(
        node_type=NodeType.EXECUTION,
        name="TestNode",
        description="A test node for unit testing",
        version="1.0.0",
        fields=[
            FieldDefinition(
                name="test_field",
                label="Test Field",
                field_type=FieldType.STRING,
                default_value="default",
            )
        ],
        has_inputs=True,
        has_config=True,
    )


@pytest.fixture
def sample_node(sample_node_metadata):
    """Create a sample node for testing."""
    return Node(
        id="test-node-123",
        name="Test Node",
        node_type="TestNode",
        state={"test_field": "test value"},
        metadata=sample_node_metadata,
    )


@pytest.fixture
def empty_workflow():
    """Create an empty workflow for testing."""
    return Workflow(id="workflow-1", name="Test Workflow", description="A workflow for testing")


@pytest.fixture
def workflow_with_nodes(empty_workflow, sample_node_metadata):
    """Create a workflow with some test nodes."""
    node1 = Node(
        id="node-1", name="Node 1", node_type="TestNode", state={}, metadata=sample_node_metadata
    )
    node2 = Node(
        id="node-2", name="Node 2", node_type="TestNode", state={}, metadata=sample_node_metadata
    )
    node3 = Node(
        id="node-3", name="Node 3", node_type="TestNode", state={}, metadata=sample_node_metadata
    )

    empty_workflow.add_node(node1)
    empty_workflow.add_node(node2)
    empty_workflow.add_node(node3)

    # Create connections: node1 -> node2 -> node3
    empty_workflow.add_connection("node-1", "node-2")
    empty_workflow.add_connection("node-2", "node-3")

    return empty_workflow


@pytest.fixture
def sample_context():
    """Create a sample execution context for testing."""
    return {
        "Input": {"data": {"name": "Test User", "age": 25, "active": True}},
        "Calculator": {"data": {"result": 42}},
    }
