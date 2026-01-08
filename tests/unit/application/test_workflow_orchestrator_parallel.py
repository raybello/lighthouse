"""Tests for parallel workflow execution."""

import threading
import time
from typing import Any, Dict

from lighthouse.application.services.execution_manager import ExecutionManager
from lighthouse.application.services.workflow_orchestrator import WorkflowOrchestrator
from lighthouse.domain.models.execution import ExecutionConfig, ExecutionMode
from lighthouse.domain.models.workflow import Workflow
from lighthouse.nodes.execution.calculator_node import CalculatorNode
from lighthouse.nodes.trigger.input_node import InputNode
from lighthouse.nodes.trigger.manual_trigger_node import ManualTriggerNode


class TestParallelExecution:
    """Test parallel execution of workflows."""

    def test_sequential_execution_mode_default(self):
        """Test that sequential mode is the default."""
        config = ExecutionConfig()
        assert config.mode == ExecutionMode.SEQUENTIAL

    def test_parallel_execution_mode(self):
        """Test parallel execution mode configuration."""
        config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=4)
        assert config.mode == ExecutionMode.PARALLEL
        assert config.max_workers == 4

    def test_execute_workflow_sequential_with_config(self):
        """Test sequential execution with explicit config."""
        # Create workflow with multiple independent nodes
        workflow = Workflow(id="test", name="Test Workflow")

        trigger = ManualTriggerNode(name="Start")
        calc1 = CalculatorNode(name="Calc1")
        calc1.state = {"expression": "10 + 5"}
        calc2 = CalculatorNode(name="Calc2")
        calc2.state = {"expression": "20 + 5"}

        workflow.add_node(trigger)
        workflow.add_node(calc1)
        workflow.add_node(calc2)
        workflow.add_connection(trigger.id, calc1.id)
        workflow.add_connection(trigger.id, calc2.id)

        # Execute with sequential config
        config = ExecutionConfig(mode=ExecutionMode.SEQUENTIAL)
        orchestrator = WorkflowOrchestrator(execution_config=config)

        result = orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        assert result["status"] == "COMPLETED"
        assert result["execution_mode"] == "sequential"
        assert result["levels"] == 2  # Level 0: trigger, Level 1: calc1, calc2

    def test_execute_workflow_parallel_mode(self):
        """Test parallel execution mode."""
        # Create workflow with multiple independent nodes at same level
        workflow = Workflow(id="test", name="Test Workflow")

        trigger = ManualTriggerNode(name="Start")
        calc1 = CalculatorNode(name="Calc1")
        calc1.state = {"expression": "10 + 5"}
        calc2 = CalculatorNode(name="Calc2")
        calc2.state = {"expression": "20 + 5"}
        calc3 = CalculatorNode(name="Calc3")
        calc3.state = {"expression": "30 + 5"}

        workflow.add_node(trigger)
        workflow.add_node(calc1)
        workflow.add_node(calc2)
        workflow.add_node(calc3)
        workflow.add_connection(trigger.id, calc1.id)
        workflow.add_connection(trigger.id, calc2.id)
        workflow.add_connection(trigger.id, calc3.id)

        # Execute with parallel config
        config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=3)
        orchestrator = WorkflowOrchestrator(execution_config=config)

        result = orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        assert result["status"] == "COMPLETED"
        assert result["execution_mode"] == "parallel"
        assert result["levels"] == 2
        assert len(result["results"]) == 4

    def test_parallel_execution_with_diamond_dependency(self):
        """Test parallel execution with diamond-shaped dependency graph."""
        # Diamond: A -> B, C -> D (B and C can run in parallel)
        workflow = Workflow(id="test", name="Diamond Workflow")

        input_a = InputNode(name="A")
        input_a.state = {"properties": '[{"name": "value", "value": "10", "type": "number"}]'}

        calc_b = CalculatorNode(name="B")
        calc_b.state = {"field_a": "{{$node['A'].data.value}}", "field_b": "5", "operation": "+"}

        calc_c = CalculatorNode(name="C")
        calc_c.state = {"field_a": "{{$node['A'].data.value}}", "field_b": "2", "operation": "*"}

        calc_d = CalculatorNode(name="D")
        calc_d.state = {
            "field_a": "{{$node['B'].data.result}}",
            "field_b": "{{$node['C'].data.result}}",
            "operation": "+",
        }

        workflow.add_node(input_a)
        workflow.add_node(calc_b)
        workflow.add_node(calc_c)
        workflow.add_node(calc_d)
        workflow.add_connection(input_a.id, calc_b.id)
        workflow.add_connection(input_a.id, calc_c.id)
        workflow.add_connection(calc_b.id, calc_d.id)
        workflow.add_connection(calc_c.id, calc_d.id)

        # Execute with parallel config
        config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=2)
        orchestrator = WorkflowOrchestrator(execution_config=config)

        result = orchestrator.execute_workflow(workflow, triggered_by=input_a.id)

        assert result["status"] == "COMPLETED"
        assert result["levels"] == 3  # Level 0: A, Level 1: B, C, Level 2: D

        # Verify D's result is correct (15 + 20 = 35)
        d_result = result["results"][calc_d.id]
        assert d_result.success
        assert d_result.data["result"] == 35

    def test_parallel_execution_thread_safety(self):
        """Test that context is thread-safe during parallel execution."""
        # Create workflow with nodes that will update context concurrently
        workflow = Workflow(id="test", name="Thread Safety Test")

        trigger = ManualTriggerNode(name="Start")
        workflow.add_node(trigger)

        # Create multiple calculator nodes that will execute in parallel
        nodes = []
        for i in range(5):
            calc = CalculatorNode(name=f"Node{i}")
            calc.state = {"field_a": str(i), "field_b": "10", "operation": "*"}
            nodes.append(calc)
            workflow.add_node(calc)
            workflow.add_connection(trigger.id, calc.id)

        # Execute with parallel config
        config = ExecutionConfig(mode=ExecutionMode.PARALLEL, max_workers=5)
        orchestrator = WorkflowOrchestrator(execution_config=config)

        result = orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        assert result["status"] == "COMPLETED"

        # Verify all nodes executed correctly
        for i, node in enumerate(nodes):
            assert result["results"][node.id].success
            assert result["results"][node.id].data["result"] == i * 10

    def test_parallel_execution_profiling_data(self):
        """Test that profiling data is recorded correctly."""
        workflow = Workflow(id="test", name="Profiling Test")

        trigger = ManualTriggerNode(name="Start")
        calc1 = CalculatorNode(name="Calc1")
        calc1.state = {"expression": "10 + 5"}
        calc2 = CalculatorNode(name="Calc2")
        calc2.state = {"expression": "20 + 5"}

        workflow.add_node(trigger)
        workflow.add_node(calc1)
        workflow.add_node(calc2)
        workflow.add_connection(trigger.id, calc1.id)
        workflow.add_connection(trigger.id, calc2.id)

        # Execute with parallel config
        config = ExecutionConfig(mode=ExecutionMode.PARALLEL, enable_profiling=True)
        orchestrator = WorkflowOrchestrator(execution_config=config)

        result = orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        assert result["status"] == "COMPLETED"

        # Check profiling data
        profiling = orchestrator.execution_manager.get_profiling_data()
        assert "traces" in profiling
        assert len(profiling["traces"]) == 3  # trigger + 2 calcs

        # Verify trace has required fields
        for trace in profiling["traces"]:
            assert "node_id" in trace
            assert "node_name" in trace
            assert "thread_id" in trace
            assert "level" in trace
            assert "start_time" in trace
            assert "end_time" in trace

    def test_parallel_execution_fail_fast(self):
        """Test that fail_fast stops execution on first error."""
        workflow = Workflow(id="test", name="Fail Fast Test")

        trigger = ManualTriggerNode(name="Start")
        # Use division by zero to cause an error
        calc_fail = CalculatorNode(name="Fail")
        calc_fail.state = {"field_a": "10", "field_b": "0", "operation": "/"}
        calc_ok = CalculatorNode(name="OK")
        calc_ok.state = {"field_a": "10", "field_b": "5", "operation": "+"}

        workflow.add_node(trigger)
        workflow.add_node(calc_fail)
        workflow.add_node(calc_ok)
        workflow.add_connection(trigger.id, calc_fail.id)
        workflow.add_connection(trigger.id, calc_ok.id)

        # Execute with fail_fast=True
        config = ExecutionConfig(mode=ExecutionMode.PARALLEL, fail_fast=True)
        orchestrator = WorkflowOrchestrator(execution_config=config)

        result = orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        assert result["status"] == "FAILED"
        assert "division" in result["error"].lower() or "zero" in result["error"].lower()

    def test_parallel_execution_override_config(self):
        """Test overriding execution config at runtime."""
        workflow = Workflow(id="test", name="Override Test")

        trigger = ManualTriggerNode(name="Start")
        calc = CalculatorNode(name="Calc")
        calc.state = {"expression": "10 + 5"}

        workflow.add_node(trigger)
        workflow.add_node(calc)
        workflow.add_connection(trigger.id, calc.id)

        # Create orchestrator with sequential config
        default_config = ExecutionConfig(mode=ExecutionMode.SEQUENTIAL)
        orchestrator = WorkflowOrchestrator(execution_config=default_config)

        # Override with parallel config at runtime
        parallel_config = ExecutionConfig(mode=ExecutionMode.PARALLEL)
        result = orchestrator.execute_workflow(
            workflow, triggered_by=trigger.id, config=parallel_config
        )

        assert result["status"] == "COMPLETED"
        # Since only one node in level 1, it falls back to sequential for that level
        assert result["execution_mode"] == "parallel"


class TestParallelAsyncExecution:
    """Test parallel async execution of workflows."""

    def test_async_parallel_execution(self):
        """Test async workflow execution with parallel mode."""
        workflow = Workflow(id="test", name="Async Parallel Test")

        trigger = ManualTriggerNode(name="Start")
        calc1 = CalculatorNode(name="Calc1")
        calc1.state = {"expression": "10 + 5"}
        calc2 = CalculatorNode(name="Calc2")
        calc2.state = {"expression": "20 + 5"}

        workflow.add_node(trigger)
        workflow.add_node(calc1)
        workflow.add_node(calc2)
        workflow.add_connection(trigger.id, calc1.id)
        workflow.add_connection(trigger.id, calc2.id)

        # Track callbacks
        callback_data = {
            "node_starts": [],
            "node_completes": [],
            "complete_called": False,
            "final_result": None,
        }

        def on_node_start(node_id: str, node_name: str):
            callback_data["node_starts"].append(node_name)

        def on_node_complete(node_id: str, result: Any):
            callback_data["node_completes"].append(node_id)

        def on_complete(result: Dict[str, Any]):
            callback_data["complete_called"] = True
            callback_data["final_result"] = result

        # Execute with parallel config
        config = ExecutionConfig(mode=ExecutionMode.PARALLEL)
        orchestrator = WorkflowOrchestrator(execution_config=config)

        thread = orchestrator.execute_workflow_async(
            workflow=workflow,
            triggered_by=trigger.id,
            on_node_start=on_node_start,
            on_node_complete=on_node_complete,
            on_complete=on_complete,
            config=config,
        )

        thread.join(timeout=5.0)

        assert callback_data["complete_called"]
        assert callback_data["final_result"]["status"] == "COMPLETED"
        assert len(callback_data["node_completes"]) == 3


class TestExecutionLevels:
    """Test execution level grouping."""

    def test_single_level_workflow(self):
        """Test workflow with single level."""
        workflow = Workflow(id="test", name="Single Level")
        trigger = ManualTriggerNode(name="Start")
        workflow.add_node(trigger)

        orchestrator = WorkflowOrchestrator()
        result = orchestrator.execute_workflow(workflow, triggered_by=trigger.id)

        assert result["status"] == "COMPLETED"
        assert result["levels"] == 1

    def test_multi_level_workflow(self):
        """Test workflow with multiple levels."""
        workflow = Workflow(id="test", name="Multi Level")

        # Level 0: A
        node_a = InputNode(name="A")
        node_a.state = {"properties": '[{"name": "x", "value": "1", "type": "number"}]'}

        # Level 1: B, C (both depend on A)
        node_b = CalculatorNode(name="B")
        node_b.state = {"field_a": "{{$node['A'].data.x}}", "field_b": "1", "operation": "+"}
        node_c = CalculatorNode(name="C")
        node_c.state = {"field_a": "{{$node['A'].data.x}}", "field_b": "2", "operation": "+"}

        # Level 2: D (depends on B and C)
        node_d = CalculatorNode(name="D")
        node_d.state = {
            "field_a": "{{$node['B'].data.result}}",
            "field_b": "{{$node['C'].data.result}}",
            "operation": "+",
        }

        # Level 3: E (depends on D)
        node_e = CalculatorNode(name="E")
        node_e.state = {"field_a": "{{$node['D'].data.result}}", "field_b": "2", "operation": "*"}

        workflow.add_node(node_a)
        workflow.add_node(node_b)
        workflow.add_node(node_c)
        workflow.add_node(node_d)
        workflow.add_node(node_e)
        workflow.add_connection(node_a.id, node_b.id)
        workflow.add_connection(node_a.id, node_c.id)
        workflow.add_connection(node_b.id, node_d.id)
        workflow.add_connection(node_c.id, node_d.id)
        workflow.add_connection(node_d.id, node_e.id)

        config = ExecutionConfig(mode=ExecutionMode.PARALLEL)
        orchestrator = WorkflowOrchestrator(execution_config=config)
        result = orchestrator.execute_workflow(workflow, triggered_by=node_a.id)

        assert result["status"] == "COMPLETED"
        assert result["levels"] == 4

        # Verify final result: E = (B + C) * 2 = ((1+1) + (1+2)) * 2 = (2 + 3) * 2 = 10
        assert result["results"][node_e.id].data["result"] == 10


class TestThreadSafetyContextManager:
    """Test thread safety of execution manager context."""

    def test_concurrent_context_updates(self):
        """Test that concurrent context updates are thread-safe."""
        execution_manager = ExecutionManager()

        # Create a session
        execution_manager.create_session(
            workflow_id="test",
            workflow_name="Test",
            triggered_by="trigger",
        )
        execution_manager.start_session()

        errors = []

        def update_context(i):
            try:
                execution_manager.set_node_context(f"node_{i}", f"Node{i}", {"value": i})
                time.sleep(0.001)  # Small delay to increase race condition chance
                context = execution_manager.get_node_context()
                # Context should contain our entry
                if f"node_{i}" not in context:
                    errors.append(f"Missing node_{i}")
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads updating context concurrently
        threads = []
        for i in range(20):
            t = threading.Thread(target=update_context, args=(i,))
            threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        execution_manager.end_session()

        # Verify no errors
        assert len(errors) == 0, f"Errors: {errors}"

        # Verify all context entries exist
        final_context = execution_manager.get_node_context()
        for i in range(20):
            assert f"node_{i}" in final_context or f"Node{i}" in final_context
