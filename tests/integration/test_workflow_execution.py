"""Integration tests for workflow execution."""

import pytest

from lighthouse.container import create_headless_container
from lighthouse.domain.models.workflow import Workflow


@pytest.fixture
def container():
    """Create a headless container for testing."""
    return create_headless_container()


@pytest.fixture
def workflow(container):
    """Create a test workflow."""
    return Workflow(id="test-workflow", name="Test Workflow")


class TestWorkflowExecution:
    """Integration tests for workflow execution."""

    def test_simple_calculator_workflow(self, container, workflow):
        """Test executing a simple calculator workflow."""
        # Create nodes
        factory = container.node_factory
        input_node = factory.create_node("Input", name="Input")
        calc_node = factory.create_node("Calculator", name="Calc")

        # Configure input node
        input_node.update_state(
            {
                "properties": (
                    '[{"name": "a", "value": "10", "type": "number"}, '
                    '{"name": "b", "value": "5", "type": "number"}]'
                )
            }
        )

        # Configure calculator node with expressions
        calc_node.update_state(
            {
                "field_a": "{{$node['Input'].data.a}}",
                "field_b": "{{$node['Input'].data.b}}",
                "operation": "+",
            }
        )

        # Add nodes to workflow
        workflow.add_node(input_node)
        workflow.add_node(calc_node)

        # Add connection
        workflow.add_connection(input_node.id, calc_node.id)

        # Execute workflow
        orchestrator = container.workflow_orchestrator
        result = orchestrator.execute_workflow(workflow, triggered_by=input_node.id)

        # Verify results
        assert result["status"] == "COMPLETED"
        assert calc_node.id in result["results"]

        calc_result = result["results"][calc_node.id]
        assert calc_result.success is True
        assert calc_result.data["result"] == 15

    def test_multi_node_workflow(self, container, workflow):
        """Test executing workflow with multiple nodes."""
        factory = container.node_factory

        # Create nodes
        input_node = factory.create_node("Input", name="Numbers")
        calc1 = factory.create_node("Calculator", name="Add")
        calc2 = factory.create_node("Calculator", name="Multiply")

        # Configure input
        input_node.update_state(
            {
                "properties": (
                    '[{"name": "x", "value": "3", "type": "number"}, '
                    '{"name": "y", "value": "4", "type": "number"}]'
                )
            }
        )

        # Configure calc1: x + y = 7
        calc1.update_state(
            {
                "field_a": "{{$node['Numbers'].data.x}}",
                "field_b": "{{$node['Numbers'].data.y}}",
                "operation": "+",
            }
        )

        # Configure calc2: (x + y) * 2 = 14
        calc2.update_state(
            {"field_a": "{{$node['Add'].data.result}}", "field_b": "2", "operation": "*"}
        )

        # Build workflow
        workflow.add_node(input_node)
        workflow.add_node(calc1)
        workflow.add_node(calc2)

        workflow.add_connection(input_node.id, calc1.id)
        workflow.add_connection(calc1.id, calc2.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify
        assert result["status"] == "COMPLETED"

        add_result = result["results"][calc1.id]
        assert add_result.data["result"] == 7

        multiply_result = result["results"][calc2.id]
        assert multiply_result.data["result"] == 14

    def test_failed_node_stops_execution(self, container, workflow):
        """Test that workflow stops when a node fails."""
        factory = container.node_factory

        # Create nodes
        input_node = factory.create_node("Input")
        calc_node = factory.create_node("Calculator")

        # Configure calculator with division by zero
        calc_node.update_state({"field_a": "10", "field_b": "0", "operation": "/"})

        workflow.add_node(input_node)
        workflow.add_node(calc_node)
        workflow.add_connection(input_node.id, calc_node.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify execution failed
        assert result["status"] == "FAILED"
        assert "error" in result


class TestNodeFactory:
    """Integration tests for node factory."""

    def test_create_all_node_types(self, container):
        """Test that all node types can be created."""
        factory = container.node_factory

        node_types = factory.get_available_node_types()

        for node_type in node_types:
            node = factory.create_node(node_type)
            assert node is not None
            assert node.id is not None

    def test_created_nodes_can_execute(self, container):
        """Test that created nodes can execute."""
        factory = container.node_factory

        # Create and execute a calculator node
        calc = factory.create_node("Calculator")
        calc.update_state({"field_a": "5", "field_b": "3", "operation": "+"})

        result = calc.execute({})

        assert result.success is True
        assert result.data["result"] == 8


class TestExecutionContext:
    """Integration tests for execution context."""

    def test_context_building(self, container, workflow):
        """Test that node context is built correctly."""
        factory = container.node_factory

        # Create nodes
        input_node = factory.create_node("Input", name="Data")
        input_node.update_state(
            {
                "properties": (
                    '[{"name": "name", "value": "Alice", "type": "string"}, '
                    '{"name": "age", "value": "30", "type": "number"}]'
                )
            }
        )

        workflow.add_node(input_node)

        # Execute
        orchestrator = container.workflow_orchestrator
        orchestrator.execute_workflow(workflow, triggered_by=input_node.id)

        # Verify context was built
        context = orchestrator.get_execution_manager().get_node_context()

        assert "Data" in context
        assert context["Data"]["data"]["name"] == "Alice"
        assert context["Data"]["data"]["age"] == 30

    def test_expression_resolution(self, container, workflow):
        """Test that expressions are resolved correctly."""
        factory = container.node_factory

        # Create form node with expression
        input_node = factory.create_node("Input", name="Source")
        form_node = factory.create_node("Form", name="Destination")

        input_node.update_state(
            {"properties": '[{"name": "value", "value": "42", "type": "string"}]'}
        )

        # Form uses expression to reference input
        form_node.update_state(
            {
                "form_fields_json": (
                    '[{"name": "computed", "type": "string", '
                    '"value": "{{$node[\'Source\'].data.value}}"}]'
                )
            }
        )

        workflow.add_node(input_node)
        workflow.add_node(form_node)
        workflow.add_connection(input_node.id, form_node.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify expression was resolved
        assert result["status"] == "COMPLETED"

        form_result = result["results"][form_node.id]
        assert form_result.success is True
        assert form_result.data["computed"] == "42"


class TestExecutionManager:
    """Integration tests for execution manager."""

    def test_execution_session_tracking(self, container, workflow):
        """Test that execution sessions are tracked."""
        factory = container.node_factory
        manager = container.execution_manager

        # Create simple workflow
        input_node = factory.create_node("Input")
        workflow.add_node(input_node)

        # Execute
        container.workflow_orchestrator.execute_workflow(workflow, triggered_by=input_node.id)

        # Verify session was tracked
        history = manager.get_session_history()
        assert len(history) == 1

        from lighthouse.domain.models.execution import ExecutionStatus

        session = history[0]
        assert session.status == ExecutionStatus.COMPLETED
        assert session.end_time is not None

    def test_node_trace_tracking(self, container, workflow):
        """Test that node execution traces are tracked."""
        factory = container.node_factory
        orchestrator = container.workflow_orchestrator

        # Create workflow
        calc_node = factory.create_node("Calculator", name="TestCalc")
        calc_node.update_state({"field_a": "10", "field_b": "5", "operation": "+"})

        workflow.add_node(calc_node)

        # Execute
        orchestrator.execute_workflow(workflow, triggered_by=calc_node.id)

        # Verify trace from session history
        from lighthouse.domain.models.execution import ExecutionStatus

        manager = orchestrator.get_execution_manager()
        history = manager.get_session_history()
        assert len(history) == 1

        session = history[0]
        trace = session.get_node_record(calc_node.id)

        assert trace is not None
        assert trace.node_name == "TestCalc"
        assert trace.status == ExecutionStatus.COMPLETED
        assert trace.outputs is not None


class TestServiceIntegration:
    """Integration tests for service interactions."""

    def test_topology_service_integration(self, container, workflow):
        """Test topology service integration."""
        factory = container.node_factory

        # Create linear workflow: A -> B -> C
        node_a = factory.create_node("Input", name="A")
        node_b = factory.create_node("Calculator", name="B")
        node_c = factory.create_node("Calculator", name="C")

        workflow.add_node(node_a)
        workflow.add_node(node_b)
        workflow.add_node(node_c)

        workflow.add_connection(node_a.id, node_b.id)
        workflow.add_connection(node_b.id, node_c.id)

        # Get sorted order
        topology_service = container.topology_service
        sorted_ids = topology_service.topological_sort(workflow)

        # Verify order
        assert sorted_ids.index(node_a.id) < sorted_ids.index(node_b.id)
        assert sorted_ids.index(node_b.id) < sorted_ids.index(node_c.id)

    def test_expression_service_integration(self, container):
        """Test expression service integration."""
        expression_service = container.expression_service

        context = {"TestNode": {"data": {"value": 42, "name": "Alice"}}}

        # Resolve expressions
        result1 = expression_service.resolve("{{$node['TestNode'].data.value}}", context)
        result2 = expression_service.resolve("{{$node['TestNode'].data.name}}", context)

        assert result1 == 42
        assert result2 == "Alice"
