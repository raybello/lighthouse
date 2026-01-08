"""
Unit tests for WorkflowFileService.

Tests file I/O operations for workflow save/load functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from lighthouse.application.services.node_factory import NodeFactory
from lighthouse.application.services.workflow_file_service import WorkflowFileService
from lighthouse.domain.models.workflow import Workflow
from lighthouse.domain.services.workflow_serializer import WorkflowSerializer
from lighthouse.nodes.registry import get_registry


class TestWorkflowFileService:
    """Test suite for WorkflowFileService."""

    @pytest.fixture
    def registry(self):
        """Get the node registry."""
        return get_registry()

    @pytest.fixture
    def node_factory(self, registry):
        """Create a NodeFactory."""
        return NodeFactory(registry)

    @pytest.fixture
    def serializer(self):
        """Create a WorkflowSerializer."""
        return WorkflowSerializer()

    @pytest.fixture
    def service(self, serializer, node_factory):
        """Create a WorkflowFileService."""
        return WorkflowFileService(serializer, node_factory)

    @pytest.fixture
    def sample_workflow(self, node_factory):
        """Create a sample workflow with real nodes."""
        workflow = Workflow(
            id="test-workflow", name="Test Workflow", description="A test workflow"
        )

        # Create nodes using factory
        input_node = node_factory.create_node("Input", name="InputData")
        calc_node = node_factory.create_node("Calculator", name="Calculate")

        # Configure nodes
        input_node.update_state(
            {"properties": json.dumps([{"name": "age", "value": "30"}])}
        )
        calc_node.update_state(
            {"field_a": '{{$node["InputData"].data.age}}', "field_b": "2", "operation": "*"}
        )

        # Add to workflow
        workflow.add_node(input_node.to_domain_node())
        workflow.add_node(calc_node.to_domain_node())
        workflow.add_connection(input_node.id, calc_node.id)

        return workflow, {input_node.id: (100.0, 150.0), calc_node.id: (400.0, 150.0)}

    def test_save_to_file(self, service, sample_workflow):
        """Test saving workflow to a .lh file."""
        workflow, positions = sample_workflow

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.lh"

            service.save_to_file(workflow, positions, str(filepath))

            # Verify file exists
            assert filepath.exists()

            # Verify JSON structure
            with open(filepath, "r") as f:
                data = json.load(f)

            assert data["version"] == "1.0"
            assert data["workflow"]["id"] == "test-workflow"
            assert data["workflow"]["name"] == "Test Workflow"
            assert len(data["nodes"]) == 2
            assert len(data["connections"]) == 1

    def test_save_invalid_extension(self, service, sample_workflow):
        """Test saving with invalid file extension."""
        workflow, positions = sample_workflow

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"

            with pytest.raises(ValueError, match="Invalid file extension"):
                service.save_to_file(workflow, positions, str(filepath))

    def test_save_creates_parent_directories(self, service, sample_workflow):
        """Test that save creates parent directories if they don't exist."""
        workflow, positions = sample_workflow

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "nested" / "test.lh"

            service.save_to_file(workflow, positions, str(filepath))

            assert filepath.exists()
            assert filepath.parent.exists()

    def test_load_from_file(self, service, sample_workflow):
        """Test loading workflow from a .lh file."""
        original_workflow, original_positions = sample_workflow

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.lh"

            # Save first
            service.save_to_file(original_workflow, original_positions, str(filepath))

            # Load
            loaded_workflow, loaded_positions = service.load_from_file(str(filepath))

            # Verify workflow
            assert loaded_workflow.id == original_workflow.id
            assert loaded_workflow.name == original_workflow.name
            assert loaded_workflow.description == original_workflow.description
            assert len(loaded_workflow.nodes) == len(original_workflow.nodes)
            assert len(loaded_workflow.connections) == len(original_workflow.connections)

            # Verify positions
            assert loaded_positions == original_positions

    def test_load_invalid_extension(self, service):
        """Test loading with invalid file extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"
            filepath.write_text("{}")

            with pytest.raises(ValueError, match="Invalid file extension"):
                service.load_from_file(str(filepath))

    def test_load_file_not_found(self, service):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            service.load_from_file("/nonexistent/path/test.lh")

    def test_load_invalid_json(self, service):
        """Test loading file with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.lh"
            filepath.write_text("not valid json{]")

            with pytest.raises(ValueError, match="Invalid JSON"):
                service.load_from_file(str(filepath))

    def test_load_invalid_node_type(self, service):
        """Test loading file with unknown node type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.lh"

            # Create file with invalid node type
            data = {
                "version": "1.0",
                "workflow": {"id": "test", "name": "Test"},
                "nodes": [
                    {
                        "id": "node1",
                        "name": "Invalid",
                        "node_type": "NonExistentNodeType",
                        "state": {},
                        "position": {"x": 0, "y": 0},
                    }
                ],
                "connections": [],
            }

            with open(filepath, "w") as f:
                json.dump(data, f)

            with pytest.raises(ValueError, match="Failed to reconstruct node"):
                service.load_from_file(str(filepath))

    def test_round_trip_preserves_data(self, service, sample_workflow):
        """Test that save then load preserves all data."""
        original_workflow, original_positions = sample_workflow

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.lh"

            # Save
            service.save_to_file(original_workflow, original_positions, str(filepath))

            # Load
            loaded_workflow, loaded_positions = service.load_from_file(str(filepath))

            # Verify workflow metadata
            assert loaded_workflow.id == original_workflow.id
            assert loaded_workflow.name == original_workflow.name

            # Verify nodes
            for node_id in original_workflow.nodes:
                assert node_id in loaded_workflow.nodes
                original_node = original_workflow.nodes[node_id]
                loaded_node = loaded_workflow.nodes[node_id]

                assert loaded_node.name == original_node.name
                assert loaded_node.metadata.name == original_node.metadata.name
                assert loaded_node.state == original_node.state
                # Status is an internal property, not directly accessible
                # last_output is never restored

            # Verify connections
            assert len(loaded_workflow.connections) == len(original_workflow.connections)

            # Verify positions
            assert loaded_positions == original_positions

    def test_save_empty_workflow(self, service):
        """Test saving an empty workflow."""
        workflow = Workflow(id="empty", name="Empty Workflow")
        positions = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "empty.lh"

            service.save_to_file(workflow, positions, str(filepath))

            # Load back
            loaded_workflow, loaded_positions = service.load_from_file(str(filepath))

            assert loaded_workflow.id == "empty"
            assert len(loaded_workflow.nodes) == 0
            assert len(loaded_workflow.connections) == 0
            assert loaded_positions == {}

    def test_load_preserves_expressions(self, service, sample_workflow):
        """Test that expressions with {{}} syntax are preserved during load."""
        workflow, positions = sample_workflow

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.lh"

            service.save_to_file(workflow, positions, str(filepath))
            loaded_workflow, _ = service.load_from_file(str(filepath))

            # Find calculator node (nodes are BaseNode instances)
            calc_node = next(
                n for n in loaded_workflow.nodes.values() if n.metadata.name == "Calculator"
            )

            # Verify expression preserved
            assert '{{$node["InputData"].data.age}}' in calc_node.state["field_a"]

    def test_save_with_missing_positions(self, service, sample_workflow):
        """Test saving when some nodes don't have positions."""
        workflow, positions = sample_workflow

        # Remove one position
        node_ids = list(positions.keys())
        partial_positions = {node_ids[0]: positions[node_ids[0]]}

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.lh"

            service.save_to_file(workflow, partial_positions, str(filepath))
            loaded_workflow, loaded_positions = service.load_from_file(str(filepath))

            # Missing positions should default to (0, 0)
            assert loaded_positions[node_ids[0]] == positions[node_ids[0]]
            assert loaded_positions[node_ids[1]] == (0.0, 0.0)

    def test_json_formatting(self, service, sample_workflow):
        """Test that saved JSON is properly formatted."""
        workflow, positions = sample_workflow

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.lh"

            service.save_to_file(workflow, positions, str(filepath))

            # Read raw file
            content = filepath.read_text()

            # Verify it's indented (pretty-printed)
            assert "  " in content  # Should have indentation
            assert "\n" in content  # Should have newlines
