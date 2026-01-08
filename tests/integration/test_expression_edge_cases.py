"""
Integration tests for edge cases in expression handling.

Tests edge cases like nested expressions, invalid expressions,
empty expressions, and complex expression scenarios.
"""

import pytest

from lighthouse.container import create_headless_container
from lighthouse.domain.models.workflow import Workflow


@pytest.fixture
def container():
    """Create a headless container for testing."""
    return create_headless_container()


@pytest.fixture(scope="function")
def workflow():
    """Create a fresh test workflow for each test."""
    import uuid

    # Use unique ID for each test to avoid conflicts
    return Workflow(id=f"edge-case-{uuid.uuid4().hex[:8]}", name="Edge Case Workflow")


class TestNestedExpressions:
    """Tests for nested and complex expressions."""

    def test_nested_arithmetic_expression(self, container, workflow):
        """Test nested arithmetic expressions are preserved and evaluated."""
        factory = container.node_factory

        # Create nodes
        input_node = factory.create_node("Input", name="Numbers")
        calc_node = factory.create_node("Calculator", name="Nested")

        # Configure with nested expression
        input_node.update_state(
            {
                "properties": '[{"name": "a", "value": "5", "type": "number"}, {"name": "b", "value": "3", "type": "number"}]'
            }
        )

        # Calculator uses field_a + field_b with operation
        # To test nested expression, put it in field_a
        nested_expr = '{{$node["Numbers"].data.a * 2 + $node["Numbers"].data.b}}'
        calc_node.update_state({"field_a": nested_expr, "field_b": "0", "operation": "+"})

        # Build workflow
        workflow.add_node(input_node)
        workflow.add_node(calc_node)
        workflow.add_connection(input_node.id, calc_node.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify execution succeeded
        assert result["status"] == "COMPLETED"
        assert result["results"][calc_node.id].data["result"] == 13  # (5*2 + 3) + 0 = 13

        # Verify expression is preserved
        assert nested_expr in calc_node.state.get("field_a", ""), (
            f"Nested expression not preserved! Got: {calc_node.state.get('field_a')}"
        )

    def test_multiple_node_references_in_expression(self, container, workflow):
        """Test expressions referencing multiple nodes."""
        factory = container.node_factory

        # Create nodes
        input1 = factory.create_node("Input", name="A")
        input2 = factory.create_node("Input", name="B")
        calc_node = factory.create_node("Calculator", name="Multi")

        # Configure inputs
        input1.update_state({"properties": '[{"name": "x", "value": "10", "type": "number"}]'})
        input2.update_state({"properties": '[{"name": "y", "value": "5", "type": "number"}]'})

        # Expression referencing both nodes
        multi_expr = '{{$node["A"].data.x + $node["B"].data.y}}'
        calc_node.update_state({"field_a": multi_expr, "field_b": "0", "operation": "+"})

        # Build workflow
        workflow.add_node(input1)
        workflow.add_node(input2)
        workflow.add_node(calc_node)
        workflow.add_connection(input1.id, calc_node.id)
        workflow.add_connection(input2.id, calc_node.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(workflow, triggered_by=input1.id)

        # Verify
        assert result["status"] == "COMPLETED"
        assert result["results"][calc_node.id].data["result"] == 15

        # Verify expression preserved
        assert multi_expr in calc_node.state.get("field_a", "")

    def test_chained_expressions(self, container, workflow):
        """Test expressions that chain through multiple nodes."""
        factory = container.node_factory

        # Create chain: Input -> Calc1 -> Calc2 -> Calc3
        input_node = factory.create_node("Input", name="Start")
        calc1 = factory.create_node("Calculator", name="Step1")
        calc2 = factory.create_node("Calculator", name="Step2")
        calc3 = factory.create_node("Calculator", name="Step3")

        # Configure
        input_node.update_state(
            {"properties": '[{"name": "value", "value": "2", "type": "number"}]'}
        )

        expr1 = '{{$node["Start"].data.value}}'
        calc1.update_state({"field_a": expr1, "field_b": "2", "operation": "*"})

        expr2 = '{{$node["Step1"].data.result}}'
        calc2.update_state({"field_a": expr2, "field_b": "3", "operation": "+"})

        expr3 = '{{$node["Step2"].data.result}}'
        calc3.update_state({"field_a": expr3, "field_b": "1", "operation": "-"})

        # Build workflow
        workflow.add_node(input_node)
        workflow.add_node(calc1)
        workflow.add_node(calc2)
        workflow.add_node(calc3)

        workflow.add_connection(input_node.id, calc1.id)
        workflow.add_connection(calc1.id, calc2.id)
        workflow.add_connection(calc2.id, calc3.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify
        assert result["status"] == "COMPLETED"
        assert result["results"][calc1.id].data["result"] == 4  # 2*2
        assert result["results"][calc2.id].data["result"] == 7  # 4+3
        assert result["results"][calc3.id].data["result"] == 6  # 7-1

        # Verify all expressions preserved
        assert expr1 in calc1.state.get("field_a", "")
        assert expr2 in calc2.state.get("field_a", "")
        assert expr3 in calc3.state.get("field_a", "")


class TestInvalidExpressions:
    """Tests for handling invalid expressions."""

    def test_expression_with_missing_node(self, container, workflow):
        """Test expression referencing non-existent node is preserved."""
        factory = container.node_factory

        # Create calc node with expression referencing non-existent node
        calc_node = factory.create_node("Calculator", name="BadRef")
        invalid_expr = '{{$node["NonExistent"].data.value}}'
        calc_node.update_state({"field_a": invalid_expr, "field_b": "0", "operation": "+"})

        workflow.add_node(calc_node)

        # Execute - may fail or resolve to empty value
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=calc_node.id
        )

        # Expression should still be preserved in node state regardless of execution status
        assert invalid_expr in calc_node.state.get("field_a", "")

    def test_expression_with_invalid_syntax(self, container, workflow):
        """Test expression with invalid syntax is preserved."""
        factory = container.node_factory

        input_node = factory.create_node("Input", name="Data")
        calc_node = factory.create_node("Calculator", name="BadSyntax")

        input_node.update_state({"properties": '[{"name": "x", "value": "5"}]'})

        # Malformed expression (missing closing braces)
        invalid_expr = '{{$node["Data"].data.x'
        calc_node.update_state({"field_a": invalid_expr, "field_b": "0", "operation": "+"})

        workflow.add_node(input_node)
        workflow.add_node(calc_node)
        workflow.add_connection(input_node.id, calc_node.id)

        # Execute - likely to fail
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Expression should be preserved regardless of execution status
        assert invalid_expr in calc_node.state.get("field_a", "")

    def test_expression_with_missing_property(self, container, workflow):
        """Test expression referencing non-existent property."""
        factory = container.node_factory

        input_node = factory.create_node("Input", name="Data")
        calc_node = factory.create_node("Calculator", name="MissingProp")

        input_node.update_state({"properties": '[{"name": "x", "value": "5"}]'})

        # Expression referencing property that doesn't exist
        missing_prop_expr = '{{$node["Data"].data.nonexistent}}'
        calc_node.update_state({"field_a": missing_prop_expr, "field_b": "0", "operation": "+"})

        workflow.add_node(input_node)
        workflow.add_node(calc_node)
        workflow.add_connection(input_node.id, calc_node.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Expression should be preserved regardless of execution status
        assert missing_prop_expr in calc_node.state.get("field_a", "")


class TestEmptyExpressions:
    """Tests for empty or whitespace expressions."""

    def test_empty_expression_string(self, container, workflow):
        """Test handling of empty expression string."""
        factory = container.node_factory

        calc_node = factory.create_node("Calculator", name="Empty")
        calc_node.update_state({"field_a": "", "field_b": "0", "operation": "+"})

        workflow.add_node(calc_node)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=calc_node.id
        )

        # Empty expression might fail or return empty result
        # But state should preserve the empty string
        assert calc_node.state.get("field_a", None) == ""

    def test_whitespace_only_expression(self, container, workflow):
        """Test handling of whitespace-only expression."""
        factory = container.node_factory

        calc_node = factory.create_node("Calculator", name="Whitespace")
        whitespace_expr = "   "
        calc_node.update_state({"field_a": whitespace_expr, "field_b": "0", "operation": "+"})

        workflow.add_node(calc_node)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=calc_node.id
        )

        # Whitespace should be preserved
        assert calc_node.state.get("field_a") == whitespace_expr

    def test_expression_with_only_braces(self, container, workflow):
        """Test expression that is just empty braces."""
        factory = container.node_factory

        calc_node = factory.create_node("Calculator", name="EmptyBraces")
        empty_braces = "{{}}"
        calc_node.update_state({"field_a": empty_braces, "field_b": "0", "operation": "+"})

        workflow.add_node(calc_node)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=calc_node.id
        )

        # Empty braces should be preserved
        assert empty_braces in calc_node.state.get("field_a", "")


class TestComplexExpressionScenarios:
    """Tests for complex real-world expression scenarios."""

    def test_expression_with_special_characters(self, container, workflow):
        """Test expressions containing special characters in strings."""
        factory = container.node_factory

        input_node = factory.create_node("Input", name="Data")
        form_node = factory.create_node("Form", name="Display")

        # Input with special characters
        input_node.update_state(
            {"properties": '[{"name": "text", "value": "hello@world.com", "type": "string"}]'}
        )

        # Expression referencing value with special characters
        expr = '{{$node["Data"].data.text}}'
        form_node.update_state(
            {"form_fields_json": f'[{{"name": "email", "type": "string", "value": "{expr}"}}]'}
        )

        workflow.add_node(input_node)
        workflow.add_node(form_node)
        workflow.add_connection(input_node.id, form_node.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify
        assert result["status"] == "COMPLETED"
        assert expr in form_node.state.get("form_fields_json", "")

    def test_expression_in_json_string(self, container, workflow):
        """Test expression embedded in JSON string."""
        factory = container.node_factory

        input_node = factory.create_node("Input", name="API")
        http_node = factory.create_node("HTTPRequest", name="Request")

        input_node.update_state({"properties": '[{"name": "endpoint", "value": "/users/123"}]'})

        # Expression in JSON body
        body_with_expr = '{"url": "{{$node[\\"API\\"].data.endpoint}}"}'
        http_node.update_state(
            {
                "url": "http://example.com",
                "method": "POST",
                "body": body_with_expr,
                "timeout": "5",
            }
        )

        workflow.add_node(input_node)
        workflow.add_node(http_node)
        workflow.add_connection(input_node.id, http_node.id)

        # The expression should be preserved in state
        assert "{{$node" in http_node.state.get("body", "")

    def test_expression_with_boolean_operators(self, container, workflow):
        """Test expressions with boolean operations."""
        factory = container.node_factory

        input_node = factory.create_node("Input", name="Check")
        calc_node = factory.create_node("Calculator", name="Boolean")

        input_node.update_state(
            {"properties": '[{"name": "age", "value": "25", "type": "number"}]'}
        )

        # Expression with comparison
        bool_expr = '{{$node["Check"].data.age >= 18}}'
        calc_node.update_state({"field_a": bool_expr, "field_b": "0", "operation": "+"})

        workflow.add_node(input_node)
        workflow.add_node(calc_node)
        workflow.add_connection(input_node.id, calc_node.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify expression preserved
        assert bool_expr in calc_node.state.get("field_a", "")

    def test_expression_with_string_concatenation(self, container, workflow):
        """Test expressions with string operations."""
        factory = container.node_factory

        input_node = factory.create_node("Input", name="Names")
        form_node = factory.create_node("Form", name="Concat")

        input_node.update_state(
            {
                "properties": '[{"name": "first", "value": "John", "type": "string"}, {"name": "last", "value": "Doe", "type": "string"}]'
            }
        )

        # Expression with string concatenation (if supported by expression engine)
        concat_expr = '{{$node["Names"].data.first + " " + $node["Names"].data.last}}'
        form_node.update_state(
            {
                "form_fields_json": f'[{{"name": "fullname", "type": "string", "value": "{concat_expr}"}}]'
            }
        )

        workflow.add_node(input_node)
        workflow.add_node(form_node)
        workflow.add_connection(input_node.id, form_node.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify expression preserved
        assert concat_expr in form_node.state.get("form_fields_json", "")

    def test_multiple_expressions_in_single_field(self, container, workflow):
        """Test multiple expressions within a single field value."""
        factory = container.node_factory

        input_node = factory.create_node("Input", name="Data")
        command_node = factory.create_node("ExecuteCommand", name="Multi")

        input_node.update_state(
            {
                "properties": '[{"name": "a", "value": "hello", "type": "string"}, {"name": "b", "value": "world", "type": "string"}]'
            }
        )

        # Multiple expressions in one field
        multi_expr = 'echo {{$node["Data"].data.a}} and {{$node["Data"].data.b}}'
        command_node.update_state({"command": multi_expr})

        workflow.add_node(input_node)
        workflow.add_node(command_node)
        workflow.add_connection(input_node.id, command_node.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify both expressions preserved
        assert '{{$node["Data"].data.a}}' in command_node.state.get("command", "")
        assert '{{$node["Data"].data.b}}' in command_node.state.get("command", "")
