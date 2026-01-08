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
        input_node.update_state({"properties": json.dumps([{"name": "value", "value": "10"}])})
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
            loaded_workflow, loaded_positions = workflow_service.load_from_file(str(filepath))

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
            loaded_workflow, loaded_positions = workflow_service.load_from_file(str(filepath))

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

    def test_expression_preserved_in_saved_json_file(self, container):
        """Test that expressions are present in the actual saved JSON file."""
        factory = container.node_factory
        workflow_service = container.workflow_file_service

        from lighthouse.domain.models.workflow import Workflow

        workflow = Workflow(id="json-expr-test", name="JSON Expression Test")

        # Create nodes with expressions
        input_node = factory.create_node("Input", name="TestInput")
        http_node = factory.create_node("HTTPRequest", name="TestHTTP")
        calc_node = factory.create_node("Calculator", name="TestCalc")

        input_node.update_state(
            {"properties": json.dumps([{"name": "url", "value": "example.com"}])}
        )

        http_expression = '{{$node["TestInput"].data.url}}'
        http_node.update_state(
            {"url": http_expression, "method": "GET", "body": "{}", "timeout": "30"}
        )

        calc_expression = '{{$node["TestInput"].data.url}}'
        calc_node.update_state({"expression": calc_expression})

        workflow.add_node(input_node.to_domain_node())
        workflow.add_node(http_node.to_domain_node())
        workflow.add_node(calc_node.to_domain_node())

        workflow.add_connection(input_node.id, http_node.id)
        workflow.add_connection(input_node.id, calc_node.id)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_expressions.lh"

            positions = {
                input_node.id: (100, 100),
                http_node.id: (300, 100),
                calc_node.id: (300, 300),
            }

            workflow_service.save_to_file(workflow, positions, str(filepath))

            # Read the raw JSON file
            with open(filepath, "r") as f:
                saved_data = json.load(f)

            # Check that expressions are in the saved file
            found_http_expr = False
            found_calc_expr = False

            for node_data in saved_data.get("nodes", []):
                state = node_data.get("state", {})
                if "url" in state and http_expression in state["url"]:
                    found_http_expr = True
                if "expression" in state and calc_expression in state["expression"]:
                    found_calc_expr = True

            assert found_http_expr, (
                f"HTTP expression not found in saved file! Nodes: {saved_data['nodes']}"
            )
            assert found_calc_expr, (
                f"Calc expression not found in saved file! Nodes: {saved_data['nodes']}"
            )

    def test_expressions_preserved_after_execution_and_save(self, container):
        """Test that expressions persist through execution and save/load cycle."""
        factory = container.node_factory
        workflow_service = container.workflow_file_service
        orchestrator = container.workflow_orchestrator

        from lighthouse.domain.models.workflow import Workflow

        workflow = Workflow(id="exec-save-test", name="Execution Save Test")

        # Create nodes - use simple Calculator chain to avoid Form node issues
        input_node = factory.create_node("Input", name="Source")
        calc1_node = factory.create_node("Calculator", name="Calc1")
        calc2_node = factory.create_node("Calculator", name="Calc2")

        # Configure nodes
        input_node.update_state(
            {"properties": json.dumps([{"name": "x", "value": "5", "type": "number"}])}
        )

        calc1_expression = '{{$node["Source"].data.x}}'
        calc1_node.update_state({"field_a": calc1_expression, "field_b": "3", "operation": "*"})

        calc2_expression = '{{$node["Calc1"].data.result}}'
        calc2_node.update_state({"field_a": calc2_expression, "field_b": "2", "operation": "+"})

        # Build workflow - add BaseNode instances for execution
        workflow.add_node(input_node)
        workflow.add_node(calc1_node)
        workflow.add_node(calc2_node)

        workflow.add_connection(input_node.id, calc1_node.id)
        workflow.add_connection(calc1_node.id, calc2_node.id)

        # Execute workflow first
        result = orchestrator.execute_workflow(workflow, triggered_by=input_node.id)
        assert result["status"] == "COMPLETED"

        # Verify execution results
        assert result["results"][calc1_node.id].data["result"] == 15  # 5 * 3
        assert result["results"][calc2_node.id].data["result"] == 17  # 15 + 2

        # Save after execution
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "after_exec.lh"

            positions = {
                input_node.id: (0.0, 0.0),
                calc1_node.id: (200.0, 0.0),
                calc2_node.id: (400.0, 0.0),
            }

            # Save the workflow with executed nodes
            workflow_service.save_to_file(workflow, positions, str(filepath))

            # Load it back
            loaded_workflow, _ = workflow_service.load_from_file(str(filepath))

            # Verify expressions are still in the loaded nodes
            loaded_calc1 = loaded_workflow.nodes[calc1_node.id]
            loaded_calc2 = loaded_workflow.nodes[calc2_node.id]

            assert calc1_expression in loaded_calc1.state.get("field_a", ""), (
                f"Calc1 expression lost! Got: {loaded_calc1.state.get('field_a')}"
            )

            assert calc2_expression in loaded_calc2.state.get("field_a", ""), (
                f"Calc2 expression lost! Got: {loaded_calc2.state.get('field_a')}"
            )

    def test_all_node_types_expressions_preserved(self, container):
        """Test expression preservation for all node types that support expressions."""
        factory = container.node_factory
        workflow_service = container.workflow_file_service

        from lighthouse.domain.models.workflow import Workflow

        workflow = Workflow(id="all-nodes-test", name="All Node Types Test")

        # Create input node
        input_node = factory.create_node("Input", name="TestInput")
        input_node.update_state(
            {
                "properties": json.dumps(
                    [
                        {"name": "url", "value": "example.com"},
                        {"name": "value", "value": "42"},
                        {"name": "text", "value": "hello"},
                    ]
                )
            }
        )

        # Create nodes with expressions
        nodes_with_expressions = []

        # HTTPRequest node
        http_node = factory.create_node("HTTPRequest", name="HTTP")
        http_expr = '{{$node["TestInput"].data.url}}'
        http_node.update_state({"url": http_expr, "method": "GET", "body": "{}", "timeout": "5"})
        nodes_with_expressions.append((http_node, "url", http_expr))

        # Calculator node
        calc_node = factory.create_node("Calculator", name="Calc")
        calc_expr = '{{$node["TestInput"].data.value}}'
        calc_node.update_state({"field_a": calc_expr, "field_b": "2", "operation": "+"})
        nodes_with_expressions.append((calc_node, "field_a", calc_expr))

        # Code node
        code_node = factory.create_node("Code", name="Code")
        code_expr = '{{$node["TestInput"].data.value}}'
        code_node.update_state({"code": f"result = {code_expr} * 2"})
        nodes_with_expressions.append((code_node, "code", code_expr))

        # Command node
        command_node = factory.create_node("ExecuteCommand", name="Command")
        command_expr = '{{$node["TestInput"].data.text}}'
        command_node.update_state({"command": f"echo {command_expr}"})
        nodes_with_expressions.append((command_node, "command", command_expr))

        # Form node
        form_node = factory.create_node("Form", name="Form")
        form_expr = '{{$node["TestInput"].data.text}}'
        form_node.update_state(
            {"form_fields_json": f'[{{"name": "field", "type": "string", "value": "{form_expr}"}}]'}
        )
        nodes_with_expressions.append((form_node, "form_fields_json", form_expr))

        # Add all nodes to workflow
        workflow.add_node(input_node.to_domain_node())
        positions = {input_node.id: (0, 0)}

        for i, (node, _, _) in enumerate(nodes_with_expressions):
            workflow.add_node(node.to_domain_node())
            workflow.add_connection(input_node.id, node.id)
            positions[node.id] = (200, i * 100)

        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "all_nodes.lh"

            workflow_service.save_to_file(workflow, positions, str(filepath))
            loaded_workflow, _ = workflow_service.load_from_file(str(filepath))

            # Verify all expressions are preserved
            for node, field, expression in nodes_with_expressions:
                loaded_node = loaded_workflow.nodes[node.id]
                assert expression in loaded_node.state.get(field, ""), (
                    f"Expression lost in {node.name}[{field}]! "
                    f"Expected: {expression}, Got: {loaded_node.state.get(field)}"
                )
