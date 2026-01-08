"""
Integration tests for workflow save/load functionality.

Tests the complete round-trip from creating a workflow, saving it,
and loading it back with all data preserved.
"""

import json
import tempfile
from pathlib import Path

import pytest

from lighthouse.container import create_headless_container


class TestWorkflowSaveLoad:
    """Integration tests for workflow save/load."""

    @pytest.fixture
    def container(self):
        """Create a service container."""
        return create_headless_container()

    def test_save_and_load_simple_workflow(self, container):
        """Test saving and loading a simple workflow."""
        # Create workflow
        factory = container.node_factory
        workflow_service = container.workflow_file_service

        from lighthouse.domain.models.workflow import Workflow

        workflow = Workflow(
            id="test-workflow",
            name="Simple Test Workflow",
            description="A simple workflow for testing",
        )

        # Create nodes
        input_node = factory.create_node("Input", name="UserInput")
        calc_node = factory.create_node("Calculator", name="DoubleValue")

        # Configure nodes
        input_node.update_state(
            {"properties": json.dumps([{"name": "value", "value": "10"}])}
        )
        calc_node.update_state(
            {
                "field_a": '{{$node["UserInput"].data.value}}',
                "field_b": "2",
                "operation": "*",
            }
        )

        # Add to workflow
        workflow.add_node(input_node.to_domain_node())
        workflow.add_node(calc_node.to_domain_node())
        workflow.add_connection(input_node.id, calc_node.id)

        # Define positions
        positions = {input_node.id: (100.0, 200.0), calc_node.id: (500.0, 200.0)}

        # Save to file
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_workflow.lh"

            workflow_service.save_to_file(workflow, positions, str(filepath))

            # Verify file exists
            assert filepath.exists()

            # Load from file
            loaded_workflow, loaded_positions = workflow_service.load_from_file(
                str(filepath)
            )

            # Verify workflow metadata
            assert loaded_workflow.id == workflow.id
            assert loaded_workflow.name == workflow.name
            assert loaded_workflow.description == workflow.description

            # Verify nodes
            assert len(loaded_workflow.nodes) == 2
            assert input_node.id in loaded_workflow.nodes
            assert calc_node.id in loaded_workflow.nodes

            # Verify node properties (nodes are BaseNode instances)
            loaded_input = loaded_workflow.nodes[input_node.id]
            assert loaded_input.name == "UserInput"
            assert loaded_input.metadata.name == "Input"

            loaded_calc = loaded_workflow.nodes[calc_node.id]
            assert loaded_calc.name == "DoubleValue"
            assert loaded_calc.metadata.name == "Calculator"
            assert loaded_calc.state["operation"] == "*"
            assert '{{$node["UserInput"].data.value}}' in loaded_calc.state["field_a"]

            # Verify connections
            assert len(loaded_workflow.connections) == 1
            conn = loaded_workflow.connections[0]
            assert conn.from_node_id == input_node.id
            assert conn.to_node_id == calc_node.id

            # Verify positions
            assert loaded_positions == positions

    def test_save_and_load_complex_workflow(self, container):
        """Test saving and loading a workflow with multiple nodes and connections."""
        factory = container.node_factory
        workflow_service = container.workflow_file_service

        from lighthouse.domain.models.workflow import Workflow

        workflow = Workflow(id="complex", name="Complex Workflow")

        # Create multiple nodes
        input1 = factory.create_node("Input", name="Input1")
        input2 = factory.create_node("Input", name="Input2")
        calc1 = factory.create_node("Calculator", name="Add")
        calc2 = factory.create_node("Calculator", name="Multiply")

        # Configure
        input1.update_state({"properties": json.dumps([{"name": "a", "value": "5"}])})
        input2.update_state({"properties": json.dumps([{"name": "b", "value": "3"}])})
        calc1.update_state(
            {
                "field_a": '{{$node["Input1"].data.a}}',
                "field_b": '{{$node["Input2"].data.b}}',
                "operation": "+",
            }
        )
        calc2.update_state(
            {"field_a": '{{$node["Add"].data.result}}', "field_b": "2", "operation": "*"}
        )

        # Build workflow
        for node in [input1, input2, calc1, calc2]:
            workflow.add_node(node.to_domain_node())

        workflow.add_connection(input1.id, calc1.id)
        workflow.add_connection(input2.id, calc1.id)
        workflow.add_connection(calc1.id, calc2.id)

        positions = {
            input1.id: (100.0, 100.0),
            input2.id: (100.0, 300.0),
            calc1.id: (400.0, 200.0),
            calc2.id: (700.0, 200.0),
        }

        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "complex.lh"

            workflow_service.save_to_file(workflow, positions, str(filepath))
            loaded_workflow, loaded_positions = workflow_service.load_from_file(
                str(filepath)
            )

            # Verify
            assert len(loaded_workflow.nodes) == 4
            assert len(loaded_workflow.connections) == 3
            assert loaded_positions == positions

    def test_saved_file_is_valid_json(self, container):
        """Test that saved files are valid, formatted JSON."""
        factory = container.node_factory
        workflow_service = container.workflow_file_service

        from lighthouse.domain.models.workflow import Workflow

        workflow = Workflow(id="json-test", name="JSON Test")
        node = factory.create_node("ManualTrigger", name="Start")
        workflow.add_node(node.to_domain_node())

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.lh"

            workflow_service.save_to_file(workflow, {node.id: (0.0, 0.0)}, str(filepath))

            # Read and parse JSON
            with open(filepath) as f:
                data = json.load(f)

            # Verify structure
            assert "version" in data
            assert "workflow" in data
            assert "nodes" in data
            assert "connections" in data

            # Verify it's pretty-printed
            content = filepath.read_text()
            assert "  " in content  # Indented
            assert data["version"] == "1.0"

    def test_expressions_preserved_through_save_load(self, container):
        """Test that expression syntax is preserved exactly."""
        factory = container.node_factory
        workflow_service = container.workflow_file_service

        from lighthouse.domain.models.workflow import Workflow

        workflow = Workflow(id="expr-test", name="Expression Test")

        input_node = factory.create_node("Input", name="Data")
        calc_node = factory.create_node("Calculator", name="Process")

        # Set complex expression
        complex_expr = '{{$node["Data"].data.value * 2 + 10}}'
        calc_node.update_state({"field_a": complex_expr, "field_b": "1", "operation": "+"})

        workflow.add_node(input_node.to_domain_node())
        workflow.add_node(calc_node.to_domain_node())
        workflow.add_connection(input_node.id, calc_node.id)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "expr.lh"

            workflow_service.save_to_file(
                workflow, {input_node.id: (0.0, 0.0), calc_node.id: (100.0, 0.0)}, str(filepath)
            )

            loaded_workflow, _ = workflow_service.load_from_file(str(filepath))

            loaded_calc = loaded_workflow.nodes[calc_node.id]
            assert loaded_calc.state["field_a"] == complex_expr

    def test_empty_workflow_round_trip(self, container):
        """Test saving and loading an empty workflow."""
        workflow_service = container.workflow_file_service

        from lighthouse.domain.models.workflow import Workflow

        workflow = Workflow(id="empty", name="Empty Workflow", description="No nodes")

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "empty.lh"

            workflow_service.save_to_file(workflow, {}, str(filepath))
            loaded_workflow, loaded_positions = workflow_service.load_from_file(str(filepath))

            assert loaded_workflow.id == "empty"
            assert loaded_workflow.name == "Empty Workflow"
            assert len(loaded_workflow.nodes) == 0
            assert len(loaded_workflow.connections) == 0
            assert loaded_positions == {}
