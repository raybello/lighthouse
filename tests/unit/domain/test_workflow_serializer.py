"""
Unit tests for WorkflowSerializer.

Tests serialization and deserialization of workflows to/from JSON format.
"""

import pytest

from lighthouse.domain.services.workflow_serializer import WorkflowSerializer


class TestWorkflowSerializer:
    """Test suite for WorkflowSerializer."""

    @pytest.fixture
    def serializer(self):
        """Create a WorkflowSerializer instance."""
        return WorkflowSerializer()

    @pytest.fixture
    def sample_workflow_dict(self):
        """Create sample workflow data as dict."""
        return {
            "version": "1.0",
            "workflow": {"id": "test-workflow", "name": "Test Workflow", "description": "A test"},
            "nodes": [
                {
                    "id": "node1",
                    "name": "Input",
                    "node_type": "Input",
                    "state": {"properties": '[{"name":"age","value":"30"}]'},
                    "position": {"x": 100.0, "y": 150.0},
                },
                {
                    "id": "node2",
                    "name": "Calculator",
                    "node_type": "Calculator",
                    "state": {
                        "field_a": '{{$node["Input"].data.age}}',
                        "field_b": "2",
                        "operation": "*",
                    },
                    "position": {"x": 400.0, "y": 150.0},
                },
            ],
            "connections": [{"from_node_id": "node1", "to_node_id": "node2"}],
        }

    def test_deserialize_valid_data(self, serializer, sample_workflow_dict):
        """Test deserializing valid workflow data."""
        workflow_meta, nodes_data, connections_data, positions = serializer.deserialize(
            sample_workflow_dict
        )

        # Verify workflow metadata
        assert workflow_meta["id"] == "test-workflow"
        assert workflow_meta["name"] == "Test Workflow"
        assert workflow_meta["description"] == "A test"

        # Verify nodes data
        assert len(nodes_data) == 2
        node1_data = next(n for n in nodes_data if n["id"] == "node1")
        assert node1_data["name"] == "Input"
        assert node1_data["node_type"] == "Input"
        assert node1_data["state"]["properties"] == '[{"name":"age","value":"30"}]'

        node2_data = next(n for n in nodes_data if n["id"] == "node2")
        assert node2_data["name"] == "Calculator"
        assert node2_data["state"]["field_a"] == '{{$node["Input"].data.age}}'

        # Verify connections data
        assert len(connections_data) == 1
        assert connections_data[0]["from_node_id"] == "node1"
        assert connections_data[0]["to_node_id"] == "node2"

        # Verify positions
        assert positions["node1"] == (100.0, 150.0)
        assert positions["node2"] == (400.0, 150.0)

    def test_deserialize_missing_version(self, serializer):
        """Test deserializing data without version field."""
        data = {
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [],
            "connections": [],
        }

        with pytest.raises(ValueError, match="Unsupported workflow file version"):
            serializer.deserialize(data)

    def test_deserialize_wrong_version(self, serializer):
        """Test deserializing data with incompatible version."""
        data = {
            "version": "2.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [],
            "connections": [],
        }

        with pytest.raises(ValueError, match="Unsupported workflow file version: 2.0"):
            serializer.deserialize(data)

    def test_deserialize_missing_workflow_field(self, serializer):
        """Test deserializing data without workflow field."""
        data = {"version": "1.0", "nodes": [], "connections": []}

        with pytest.raises(ValueError, match="Missing required field: 'workflow'"):
            serializer.deserialize(data)

    def test_deserialize_missing_nodes_field(self, serializer):
        """Test deserializing data without nodes field."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "connections": [],
        }

        with pytest.raises(ValueError, match="Missing required field: 'nodes'"):
            serializer.deserialize(data)

    def test_deserialize_missing_connections_field(self, serializer):
        """Test deserializing data without connections field."""
        data = {"version": "1.0", "workflow": {"id": "test", "name": "Test"}, "nodes": []}

        with pytest.raises(ValueError, match="Missing required field: 'connections'"):
            serializer.deserialize(data)

    def test_deserialize_missing_workflow_id(self, serializer):
        """Test deserializing data with missing workflow.id."""
        data = {
            "version": "1.0",
            "workflow": {"name": "Test"},
            "nodes": [],
            "connections": [],
        }

        with pytest.raises(ValueError, match="Missing required field: 'workflow.id'"):
            serializer.deserialize(data)

    def test_deserialize_missing_workflow_name(self, serializer):
        """Test deserializing data with missing workflow.name."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test"},
            "nodes": [],
            "connections": [],
        }

        with pytest.raises(ValueError, match="Missing required field: 'workflow.name'"):
            serializer.deserialize(data)

    def test_deserialize_missing_node_id(self, serializer):
        """Test deserializing data with node missing id field."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [{"name": "Node", "node_type": "Input", "state": {}}],
            "connections": [],
        }

        with pytest.raises(ValueError, match="Node missing required field: 'id'"):
            serializer.deserialize(data)

    def test_deserialize_missing_node_name(self, serializer):
        """Test deserializing data with node missing name field."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [{"id": "node1", "node_type": "Input", "state": {}}],
            "connections": [],
        }

        with pytest.raises(ValueError, match="Node node1 missing field: 'name'"):
            serializer.deserialize(data)

    def test_deserialize_missing_node_type(self, serializer):
        """Test deserializing data with node missing node_type field."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [{"id": "node1", "name": "Node", "state": {}}],
            "connections": [],
        }

        with pytest.raises(ValueError, match="Node node1 missing field: 'node_type'"):
            serializer.deserialize(data)

    def test_deserialize_missing_node_state(self, serializer):
        """Test deserializing data with node missing state field."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [{"id": "node1", "name": "Node", "node_type": "Input"}],
            "connections": [],
        }

        with pytest.raises(ValueError, match="Node node1 missing field: 'state'"):
            serializer.deserialize(data)

    def test_deserialize_invalid_connection_from_node(self, serializer):
        """Test deserializing data with connection referencing non-existent from_node."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [
                {
                    "id": "node1",
                    "name": "Node1",
                    "node_type": "Input",
                    "state": {},
                    "position": {"x": 0, "y": 0},
                }
            ],
            "connections": [{"from_node_id": "nonexistent", "to_node_id": "node1"}],
        }

        with pytest.raises(
            ValueError, match="Connection references non-existent node: nonexistent"
        ):
            serializer.deserialize(data)

    def test_deserialize_invalid_connection_to_node(self, serializer):
        """Test deserializing data with connection referencing non-existent to_node."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [
                {
                    "id": "node1",
                    "name": "Node1",
                    "node_type": "Input",
                    "state": {},
                    "position": {"x": 0, "y": 0},
                }
            ],
            "connections": [{"from_node_id": "node1", "to_node_id": "nonexistent"}],
        }

        with pytest.raises(
            ValueError, match="Connection references non-existent node: nonexistent"
        ):
            serializer.deserialize(data)

    def test_deserialize_missing_connection_from_node_id(self, serializer):
        """Test deserializing data with connection missing from_node_id."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [],
            "connections": [{"to_node_id": "node1"}],
        }

        with pytest.raises(ValueError, match="Connection missing required field: 'from_node_id'"):
            serializer.deserialize(data)

    def test_deserialize_missing_connection_to_node_id(self, serializer):
        """Test deserializing data with connection missing to_node_id."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [],
            "connections": [{"from_node_id": "node1"}],
        }

        with pytest.raises(ValueError, match="Connection missing required field: 'to_node_id'"):
            serializer.deserialize(data)

    def test_deserialize_default_positions(self, serializer):
        """Test deserializing nodes without position data."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [{"id": "node1", "name": "Node", "node_type": "Input", "state": {}}],
            "connections": [],
        }

        _, _, _, positions = serializer.deserialize(data)

        # Should default to (0, 0)
        assert positions["node1"] == (0.0, 0.0)

    def test_deserialize_workflow_without_description(self, serializer):
        """Test deserializing workflow without description field."""
        data = {
            "version": "1.0",
            "workflow": {"id": "test", "name": "Test"},
            "nodes": [],
            "connections": [],
        }

        workflow_meta, _, _, _ = serializer.deserialize(data)

        # Should use None or empty string from original data
        assert workflow_meta.get("description", "") == ""
