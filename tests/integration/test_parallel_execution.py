"""Integration tests for parallel workflow execution."""

import pytest

from lighthouse.container import create_container
from lighthouse.domain.models.execution import ExecutionConfig, ExecutionMode
from lighthouse.domain.models.workflow import Workflow


@pytest.fixture
def parallel_container():
    """Create a container configured for parallel execution."""
    config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=4)
    return create_container(execution_config=config)


@pytest.fixture
def sequential_container():
    """Create a container configured for sequential execution."""
    config = ExecutionConfig(mode=ExecutionMode.SEQUENTIAL)
    return create_container(execution_config=config)


@pytest.fixture
def workflow():
    """Create a test workflow."""
    return Workflow(id="test-parallel", name="Parallel Test Workflow")


class TestParallelExecutionIntegration:
    """Integration tests for parallel execution."""

    def test_parallel_execution_with_container(self, parallel_container, workflow):
        """Test parallel execution using the container."""
        factory = parallel_container.node_factory

        # Create trigger
        trigger = factory.create_node("Input", name="Trigger")
        trigger.update_state({"properties": '[{"name": "value", "value": "1"}]'})

        # Create multiple independent nodes
        calc1 = factory.create_node("Calculator", name="Calc1")
        calc1.update_state({"field_a": "10", "field_b": "5", "operation": "+"})

        calc2 = factory.create_node("Calculator", name="Calc2")
        calc2.update_state({"field_a": "20", "field_b": "3", "operation": "*"})

        calc3 = factory.create_node("Calculator", name="Calc3")
        calc3.update_state({"field_a": "100", "field_b": "25", "operation": "-"})

        # Add to workflow
        workflow.add_node(trigger)
        workflow.add_node(calc1)
        workflow.add_node(calc2)
        workflow.add_node(calc3)

        workflow.add_connection(trigger.id, calc1.id)
        workflow.add_connection(trigger.id, calc2.id)
        workflow.add_connection(trigger.id, calc3.id)

        # Execute
        result = parallel_container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=trigger.id
        )

        # Verify
        assert result["status"] == "COMPLETED"
        assert result["execution_mode"] == "parallel"
        assert result["levels"] == 2

        # Verify all calculations are correct
        assert result["results"][calc1.id].data["result"] == 15
        assert result["results"][calc2.id].data["result"] == 60
        assert result["results"][calc3.id].data["result"] == 75

    def test_diamond_dependency_parallel(self, parallel_container, workflow):
        """Test diamond dependency pattern with parallel execution."""
        factory = parallel_container.node_factory

        # Level 0: Input
        input_node = factory.create_node("Input", name="A")
        input_node.update_state({"properties": '[{"name": "x", "value": "10"}]'})

        # Level 1: B and C (can run in parallel)
        calc_b = factory.create_node("Calculator", name="B")
        calc_b.update_state({"field_a": '{{$node["A"].data.x}}', "field_b": "2", "operation": "+"})

        calc_c = factory.create_node("Calculator", name="C")
        calc_c.update_state({"field_a": '{{$node["A"].data.x}}', "field_b": "3", "operation": "*"})

        # Level 2: D (depends on both B and C)
        calc_d = factory.create_node("Calculator", name="D")
        calc_d.update_state(
            {
                "field_a": '{{$node["B"].data.result}}',
                "field_b": '{{$node["C"].data.result}}',
                "operation": "+",
            }
        )

        # Build workflow
        workflow.add_node(input_node)
        workflow.add_node(calc_b)
        workflow.add_node(calc_c)
        workflow.add_node(calc_d)

        workflow.add_connection(input_node.id, calc_b.id)
        workflow.add_connection(input_node.id, calc_c.id)
        workflow.add_connection(calc_b.id, calc_d.id)
        workflow.add_connection(calc_c.id, calc_d.id)

        # Execute
        result = parallel_container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify
        assert result["status"] == "COMPLETED"
        assert result["levels"] == 3

        # A.x = 10
        # B = 10 + 2 = 12
        # C = 10 * 3 = 30
        # D = 12 + 30 = 42
        assert result["results"][calc_d.id].data["result"] == 42

    def test_parallel_vs_sequential_same_result(self, workflow):
        """Test that parallel and sequential execution produce the same results."""
        # Create workflow with diamond pattern
        parallel_config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=4)
        sequential_config = ExecutionConfig(mode=ExecutionMode.SEQUENTIAL)

        parallel_container = create_container(execution_config=parallel_config)
        sequential_container = create_container(execution_config=sequential_config)

        factory = parallel_container.node_factory

        # Build workflow
        input_node = factory.create_node("Input", name="Start")
        input_node.update_state({"properties": '[{"name": "n", "value": "5"}]'})

        calc1 = factory.create_node("Calculator", name="Double")
        calc1.update_state(
            {"field_a": '{{$node["Start"].data.n}}', "field_b": "2", "operation": "*"}
        )

        calc2 = factory.create_node("Calculator", name="Square")
        calc2.update_state(
            {
                "field_a": '{{$node["Start"].data.n}}',
                "field_b": '{{$node["Start"].data.n}}',
                "operation": "*",
            }
        )

        calc3 = factory.create_node("Calculator", name="Sum")
        calc3.update_state(
            {
                "field_a": '{{$node["Double"].data.result}}',
                "field_b": '{{$node["Square"].data.result}}',
                "operation": "+",
            }
        )

        workflow.add_node(input_node)
        workflow.add_node(calc1)
        workflow.add_node(calc2)
        workflow.add_node(calc3)

        workflow.add_connection(input_node.id, calc1.id)
        workflow.add_connection(input_node.id, calc2.id)
        workflow.add_connection(calc1.id, calc3.id)
        workflow.add_connection(calc2.id, calc3.id)

        # Create identical workflow for sequential execution
        workflow2 = Workflow(id="test-sequential", name="Sequential Test")
        for node in workflow.nodes.values():
            workflow2.add_node(node)
        for conn in workflow.connections:
            workflow2.add_connection(conn.from_node_id, conn.to_node_id)

        # Execute both
        parallel_result = parallel_container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )
        sequential_result = sequential_container.workflow_orchestrator.execute_workflow(
            workflow2, triggered_by=input_node.id
        )

        # Verify same results
        assert parallel_result["status"] == "COMPLETED"
        assert sequential_result["status"] == "COMPLETED"

        # n = 5
        # Double = 5 * 2 = 10
        # Square = 5 * 5 = 25
        # Sum = 10 + 25 = 35
        assert parallel_result["results"][calc3.id].data["result"] == 35
        assert sequential_result["results"][calc3.id].data["result"] == 35


class TestProfilingIntegration:
    """Integration tests for execution profiling."""

    def test_profiling_data_available(self, parallel_container, workflow):
        """Test that profiling data is available after execution."""
        factory = parallel_container.node_factory

        # Create simple workflow
        trigger = factory.create_node("Input", name="Start")
        calc = factory.create_node("Calculator", name="Calc")
        calc.update_state({"field_a": "10", "field_b": "5", "operation": "+"})

        workflow.add_node(trigger)
        workflow.add_node(calc)
        workflow.add_connection(trigger.id, calc.id)

        # Execute
        parallel_container.workflow_orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        # Get profiling data
        profiler = parallel_container.execution_profiler
        stats = profiler.get_statistics()

        assert stats.status == "COMPLETED"
        assert stats.total_nodes == 2
        assert stats.completed_nodes == 2
        assert len(stats.traces) == 2

    def test_profiler_summary(self, parallel_container, workflow):
        """Test profiler summary output."""
        factory = parallel_container.node_factory

        # Create workflow with multiple levels
        trigger = factory.create_node("Input", name="A")
        trigger.update_state({"properties": '[{"name": "x", "value": "1"}]'})

        calc_b = factory.create_node("Calculator", name="B")
        calc_b.update_state({"field_a": "10", "field_b": "5", "operation": "+"})

        calc_c = factory.create_node("Calculator", name="C")
        calc_c.update_state({"field_a": "20", "field_b": "3", "operation": "*"})

        workflow.add_node(trigger)
        workflow.add_node(calc_b)
        workflow.add_node(calc_c)
        workflow.add_connection(trigger.id, calc_b.id)
        workflow.add_connection(trigger.id, calc_c.id)

        # Execute
        parallel_container.workflow_orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        # Get summary
        profiler = parallel_container.execution_profiler
        summary = profiler.print_summary()

        # Verify summary contains expected info
        assert "EXECUTION STATISTICS" in summary
        assert "COMPLETED" in summary
        assert "A" in summary
        assert "B" in summary
        assert "C" in summary

    def test_gantt_data_export(self, parallel_container, workflow):
        """Test Gantt chart data export."""
        factory = parallel_container.node_factory

        trigger = factory.create_node("Input", name="Start")
        calc = factory.create_node("Calculator", name="Calc")
        calc.update_state({"field_a": "10", "field_b": "5", "operation": "+"})

        workflow.add_node(trigger)
        workflow.add_node(calc)
        workflow.add_connection(trigger.id, calc.id)

        # Execute
        parallel_container.workflow_orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        # Get Gantt data
        profiler = parallel_container.execution_profiler
        gantt_data = profiler.export_gantt_data()

        # Verify structure
        assert "metadata" in gantt_data
        assert "nodes" in gantt_data
        assert "levels" in gantt_data

        assert len(gantt_data["nodes"]) == 2
        for node in gantt_data["nodes"]:
            assert "id" in node
            assert "name" in node
            assert "start" in node
            assert "end" in node
            assert "level" in node


class TestExecutionConfigIntegration:
    """Integration tests for execution configuration."""

    def test_config_passed_to_container(self):
        """Test that execution config is properly passed through container."""
        config = ExecutionConfig(
            mode=ExecutionMode.PARALLEL,
            max_workers=8,
            enable_profiling=True,
            fail_fast=False,
        )

        container = create_container(execution_config=config)

        assert container.execution_config.mode == ExecutionMode.PARALLEL
        assert container.execution_config.max_workers == 8
        assert container.execution_config.enable_profiling is True
        assert container.execution_config.fail_fast is False

    def test_runtime_config_override(self, sequential_container, workflow):
        """Test overriding config at runtime."""
        factory = sequential_container.node_factory

        trigger = factory.create_node("Input", name="Start")
        calc = factory.create_node("Calculator", name="Calc")
        calc.update_state({"field_a": "10", "field_b": "5", "operation": "+"})

        workflow.add_node(trigger)
        workflow.add_node(calc)
        workflow.add_connection(trigger.id, calc.id)

        # Container is configured for sequential, but override with parallel
        parallel_config = ExecutionConfig(mode=ExecutionMode.PARALLEL)

        result = sequential_container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=trigger.id, config=parallel_config
        )

        assert result["status"] == "COMPLETED"
        assert result["execution_mode"] == "parallel"


class TestExpressionPreservationWithParallel:
    """Test that expressions are preserved in parallel execution."""

    def test_expressions_preserved_parallel(self, parallel_container, workflow):
        """Test that expressions are preserved when using parallel execution."""
        factory = parallel_container.node_factory

        # Create nodes with expressions
        input_node = factory.create_node("Input", name="Source")
        input_node.update_state({"properties": '[{"name": "x", "value": "5"}]'})

        calc_node = factory.create_node("Calculator", name="Calc")
        expression = '{{$node["Source"].data.x}}'
        calc_node.update_state({"field_a": expression, "field_b": "3", "operation": "*"})

        workflow.add_node(input_node)
        workflow.add_node(calc_node)
        workflow.add_connection(input_node.id, calc_node.id)

        # Execute with parallel mode
        result = parallel_container.workflow_orchestrator.execute_workflow(
            workflow, triggered_by=input_node.id
        )

        # Verify execution succeeded
        assert result["status"] == "COMPLETED"
        assert result["results"][calc_node.id].data["result"] == 15

        # Verify expression is still in node state
        assert expression in calc_node.state.get("field_a", ""), (
            f"Expression not preserved! Got: {calc_node.state.get('field_a')}"
        )


class TestErrorHandlingParallel:
    """Test error handling in parallel execution."""

    def test_fail_fast_stops_parallel_execution(self, workflow):
        """Test that fail_fast stops execution when a node fails."""
        config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=4, fail_fast=True)
        container = create_container(execution_config=config)
        factory = container.node_factory

        trigger = factory.create_node("Input", name="Start")

        # Create nodes, one will fail due to division by zero
        calc_fail = factory.create_node("Calculator", name="Fail")
        calc_fail.update_state({"field_a": "10", "field_b": "0", "operation": "/"})

        calc_ok = factory.create_node("Calculator", name="OK")
        calc_ok.update_state({"field_a": "10", "field_b": "5", "operation": "+"})

        workflow.add_node(trigger)
        workflow.add_node(calc_fail)
        workflow.add_node(calc_ok)
        workflow.add_connection(trigger.id, calc_fail.id)
        workflow.add_connection(trigger.id, calc_ok.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        # Verify failure was detected
        assert result["status"] == "FAILED"
        assert "division" in result["error"].lower() or "zero" in result["error"].lower()

    def test_continue_on_error_when_not_fail_fast(self, workflow):
        """Test that execution continues when fail_fast is False."""
        config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=4, fail_fast=False)
        container = create_container(execution_config=config)
        factory = container.node_factory

        trigger = factory.create_node("Input", name="Start")

        # Create nodes, one will fail but the other should still execute
        code_fail = factory.create_node("Code", name="Fail")
        code_fail.update_state({"code": "raise ValueError('Intentional error')"})

        calc_ok = factory.create_node("Calculator", name="OK")
        calc_ok.update_state({"field_a": "10", "field_b": "5", "operation": "+"})

        workflow.add_node(trigger)
        workflow.add_node(code_fail)
        workflow.add_node(calc_ok)
        workflow.add_connection(trigger.id, code_fail.id)
        workflow.add_connection(trigger.id, calc_ok.id)

        # Execute
        result = container.workflow_orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        # Verify that execution ended with error but both nodes were attempted
        assert result["status"] == "FAILED"
        # The OK node should have completed successfully
        assert calc_ok.id in result["results"]
        assert result["results"][calc_ok.id].success is True
