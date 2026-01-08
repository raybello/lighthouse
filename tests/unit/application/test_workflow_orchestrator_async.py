"""Tests for async workflow execution."""

import time
from typing import Any, Dict

import pytest

from lighthouse.application.services.workflow_orchestrator import WorkflowOrchestrator
from lighthouse.domain.models.workflow import Workflow
from lighthouse.nodes.execution.calculator_node import CalculatorNode
from lighthouse.nodes.trigger.manual_trigger_node import ManualTriggerNode


class TestAsyncWorkflowExecution:
    """Test async execution of workflows in threads."""

    def test_execute_workflow_async_basic(self):
        """Test basic async workflow execution."""
        # Create workflow
        workflow = Workflow(id="test", name="Test Workflow")

        trigger = ManualTriggerNode(name="Start")
        calc = CalculatorNode(name="Calc")
        calc.state = {"expression": "10 + 5"}

        workflow.add_node(trigger)
        workflow.add_node(calc)
        workflow.add_connection(trigger.id, calc.id)

        # Create orchestrator
        orchestrator = WorkflowOrchestrator()

        # Track callbacks
        callback_data = {
            "node_starts": [],
            "node_completes": [],
            "node_errors": [],
            "complete_called": False,
            "final_result": None,
        }

        def on_node_start(node_id: str, node_name: str):
            callback_data["node_starts"].append((node_id, node_name))

        def on_node_complete(node_id: str, result: Any):
            callback_data["node_completes"].append((node_id, result))

        def on_node_error(node_id: str, error: str):
            callback_data["node_errors"].append((node_id, error))

        def on_complete(result: Dict[str, Any]):
            callback_data["complete_called"] = True
            callback_data["final_result"] = result

        # Execute async
        thread = orchestrator.execute_workflow_async(
            workflow=workflow,
            triggered_by=trigger.id,
            on_node_start=on_node_start,
            on_node_complete=on_node_complete,
            on_node_error=on_node_error,
            on_complete=on_complete,
        )

        # Wait for completion
        thread.join(timeout=5.0)

        # Verify callbacks were called
        assert len(callback_data["node_starts"]) == 2
        assert len(callback_data["node_completes"]) == 2
        assert len(callback_data["node_errors"]) == 0
        assert callback_data["complete_called"] is True
        assert callback_data["final_result"]["status"] == "COMPLETED"

    def test_execute_workflow_async_error_handling(self):
        """Test async workflow execution with errors."""
        from lighthouse.nodes.execution.code_node import CodeNode

        # Create workflow with failing node
        workflow = Workflow(id="test", name="Test Workflow")

        trigger = ManualTriggerNode(name="Start")
        code = CodeNode(name="FailingCode")
        code.state = {"code": "raise ValueError('Test error')"}

        workflow.add_node(trigger)
        workflow.add_node(code)
        workflow.add_connection(trigger.id, code.id)

        # Create orchestrator
        orchestrator = WorkflowOrchestrator()

        # Track callbacks
        callback_data = {
            "node_errors": [],
            "complete_called": False,
            "final_result": None,
        }

        def on_node_error(node_id: str, error: str):
            callback_data["node_errors"].append((node_id, error))

        def on_complete(result: Dict[str, Any]):
            callback_data["complete_called"] = True
            callback_data["final_result"] = result

        # Execute async
        thread = orchestrator.execute_workflow_async(
            workflow=workflow,
            triggered_by=trigger.id,
            on_node_error=on_node_error,
            on_complete=on_complete,
        )

        # Wait for completion
        thread.join(timeout=5.0)

        # Verify error was captured
        assert len(callback_data["node_errors"]) >= 1
        assert callback_data["complete_called"] is True
        assert callback_data["final_result"]["status"] == "FAILED"

    def test_execute_workflow_async_cancellation(self):
        """Test cancelling async workflow execution."""
        from lighthouse.nodes.execution.command_node import ExecuteCommandNode

        # Create workflow with long-running node
        workflow = Workflow(id="test", name="Test Workflow")

        trigger = ManualTriggerNode(name="Start")
        cmd1 = ExecuteCommandNode(name="Sleep1")
        cmd1.state = {"command": "sleep 1"}
        cmd2 = ExecuteCommandNode(name="Sleep2")
        cmd2.state = {"command": "sleep 1"}

        workflow.add_node(trigger)
        workflow.add_node(cmd1)
        workflow.add_node(cmd2)
        workflow.add_connection(trigger.id, cmd1.id)
        workflow.add_connection(cmd1.id, cmd2.id)

        # Create orchestrator
        orchestrator = WorkflowOrchestrator()

        # Track callbacks
        callback_data = {
            "complete_called": False,
            "final_result": None,
        }

        def on_complete(result: Dict[str, Any]):
            callback_data["complete_called"] = True
            callback_data["final_result"] = result

        # Execute async
        thread = orchestrator.execute_workflow_async(
            workflow=workflow,
            triggered_by=trigger.id,
            on_complete=on_complete,
        )

        # Cancel after a short delay
        time.sleep(0.5)
        orchestrator.cancel_execution()

        # Wait for thread to finish
        thread.join(timeout=5.0)

        # Verify cancellation
        assert callback_data["complete_called"] is True
        assert callback_data["final_result"]["status"] == "CANCELLED"

    def test_execute_workflow_async_prevents_concurrent_execution(self):
        """Test that concurrent executions are prevented."""
        from lighthouse.nodes.execution.command_node import ExecuteCommandNode

        # Create workflow with a sleep to ensure it's running
        workflow = Workflow(id="test", name="Test Workflow")
        trigger = ManualTriggerNode(name="Start")
        cmd = ExecuteCommandNode(name="Sleep")
        cmd.state = {"command": "sleep 0.5"}

        workflow.add_node(trigger)
        workflow.add_node(cmd)
        workflow.add_connection(trigger.id, cmd.id)

        # Create orchestrator
        orchestrator = WorkflowOrchestrator()

        # Start first execution
        thread1 = orchestrator.execute_workflow_async(
            workflow=workflow,
            triggered_by=trigger.id,
        )

        # Wait a tiny bit to ensure thread starts
        time.sleep(0.1)

        # Try to start second execution
        with pytest.raises(RuntimeError, match="already running"):
            orchestrator.execute_workflow_async(
                workflow=workflow,
                triggered_by=trigger.id,
            )

        # Wait for first to complete
        thread1.join(timeout=5.0)

        # Now second execution should work
        thread2 = orchestrator.execute_workflow_async(
            workflow=workflow,
            triggered_by=trigger.id,
        )
        thread2.join(timeout=5.0)

        # Give thread time to clean up
        time.sleep(0.1)
        assert not orchestrator.is_executing()

    def test_is_executing_reflects_state(self):
        """Test is_executing method reflects execution state."""
        from lighthouse.nodes.execution.command_node import ExecuteCommandNode

        # Create workflow with a sleep to ensure it's running
        workflow = Workflow(id="test", name="Test Workflow")
        trigger = ManualTriggerNode(name="Start")
        cmd = ExecuteCommandNode(name="Sleep")
        cmd.state = {"command": "sleep 0.5"}

        workflow.add_node(trigger)
        workflow.add_node(cmd)
        workflow.add_connection(trigger.id, cmd.id)

        # Create orchestrator
        orchestrator = WorkflowOrchestrator()

        # Initially not executing
        assert not orchestrator.is_executing()

        # Start execution
        thread = orchestrator.execute_workflow_async(
            workflow=workflow,
            triggered_by=trigger.id,
        )

        # Wait a tiny bit for thread to start
        time.sleep(0.1)

        # Should be executing
        assert orchestrator.is_executing()

        # Wait for completion
        thread.join(timeout=5.0)

        # Should no longer be executing
        time.sleep(0.1)  # Small delay to ensure thread cleanup
        assert not orchestrator.is_executing()
