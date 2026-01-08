"""
Workflow orchestrator for coordinating node execution.

Pure business logic with NO UI dependencies.
"""

from typing import Dict, Any, List, Optional, Callable
from threading import Thread, Event
from lighthouse.nodes.base.base_node import BaseNode
from lighthouse.domain.services.topology_service import TopologyService
from lighthouse.domain.services.expression_service import ExpressionService
from lighthouse.application.services.execution_manager import ExecutionManager
from lighthouse.domain.models.workflow import Workflow


class WorkflowOrchestrator:
    """
    Orchestrates workflow execution by coordinating nodes.

    Responsible for:
    - Topological sorting of nodes
    - Sequential node execution
    - Expression resolution
    - Context management
    """

    def __init__(
        self,
        topology_service: Optional[TopologyService] = None,
        expression_service: Optional[ExpressionService] = None,
        execution_manager: Optional[ExecutionManager] = None,
    ):
        """
        Initialize the workflow orchestrator.

        Args:
            topology_service: Service for graph topology operations
            expression_service: Service for expression evaluation
            execution_manager: Manager for execution state
        """
        self.topology_service = topology_service or TopologyService()
        self.expression_service = expression_service or ExpressionService()
        self.execution_manager = execution_manager or ExecutionManager()
        self._cancel_event = Event()
        self._execution_thread: Optional[Thread] = None

    def execute_workflow(self, workflow: Workflow, triggered_by: str) -> Dict[str, Any]:
        """
        Execute a workflow synchronously (for backward compatibility).

        Args:
            workflow: Workflow to execute
            triggered_by: Node that triggered execution

        Returns:
            Execution results dictionary

        Raises:
            ValueError: If workflow has cycles or is invalid
        """
        # Validate workflow
        if not workflow.nodes:
            raise ValueError("Workflow has no nodes")

        # Perform topological sort
        try:
            sorted_node_ids = self.topology_service.topological_sort(workflow)
        except ValueError as e:
            raise ValueError(f"Workflow has cycles: {e}")

        # Create execution session
        session_id = self.execution_manager.create_session(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            triggered_by=triggered_by,
            execution_order=sorted_node_ids,
        )

        # Start execution
        self.execution_manager.start_session()
        self.execution_manager.clear_context()

        # Execute nodes in topological order
        execution_results = {}

        for node_id in sorted_node_ids:
            node = workflow.get_node(node_id)

            if not node:
                continue

            # Execute node
            result = self._execute_node(node, workflow)

            execution_results[node_id] = result

            # Stop execution if node failed
            if not result.success:
                self.execution_manager.end_session(status="FAILED")
                return {
                    "session_id": session_id,
                    "status": "FAILED",
                    "results": execution_results,
                    "error": f"Node {node.name} failed: {result.error}",
                }

        # End execution
        self.execution_manager.end_session(status="COMPLETED")

        return {"session_id": session_id, "status": "COMPLETED", "results": execution_results}

    def execute_workflow_async(
        self,
        workflow: Workflow,
        triggered_by: str,
        on_node_start: Optional[Callable[[str, str], None]] = None,
        on_node_complete: Optional[Callable[[str, Any], None]] = None,
        on_node_error: Optional[Callable[[str, str], None]] = None,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Thread:
        """
        Execute a workflow asynchronously in a separate thread.

        Args:
            workflow: Workflow to execute
            triggered_by: Node that triggered execution
            on_node_start: Callback when a node starts (node_id, node_name)
            on_node_complete: Callback when a node completes (node_id, result)
            on_node_error: Callback when a node errors (node_id, error)
            on_complete: Callback when entire workflow completes (final_result)

        Returns:
            Thread object for the execution

        Raises:
            ValueError: If workflow has cycles or is invalid
            RuntimeError: If another execution is already running
        """
        if self._execution_thread and self._execution_thread.is_alive():
            raise RuntimeError("Another workflow execution is already running")

        # Reset cancel event
        self._cancel_event.clear()

        # Create and start thread
        self._execution_thread = Thread(
            target=self._execute_workflow_thread,
            args=(
                workflow,
                triggered_by,
                on_node_start,
                on_node_complete,
                on_node_error,
                on_complete,
            ),
            daemon=True,
        )
        self._execution_thread.start()

        return self._execution_thread

    def cancel_execution(self) -> None:
        """Cancel the currently running async execution."""
        self._cancel_event.set()

    def is_executing(self) -> bool:
        """Check if a workflow is currently executing."""
        return self._execution_thread is not None and self._execution_thread.is_alive()

    def _execute_workflow_thread(
        self,
        workflow: Workflow,
        triggered_by: str,
        on_node_start: Optional[Callable[[str, str], None]],
        on_node_complete: Optional[Callable[[str, Any], None]],
        on_node_error: Optional[Callable[[str, str], None]],
        on_complete: Optional[Callable[[Dict[str, Any]], None]],
    ) -> None:
        """
        Internal method to execute workflow in a thread.

        Args:
            workflow: Workflow to execute
            triggered_by: Node that triggered execution
            on_node_start: Callback when a node starts
            on_node_complete: Callback when a node completes
            on_node_error: Callback when a node errors
            on_complete: Callback when execution completes
        """
        try:
            # Validate workflow
            if not workflow.nodes:
                if on_complete:
                    on_complete({"status": "FAILED", "error": "Workflow has no nodes"})
                return

            # Perform topological sort
            try:
                sorted_node_ids = self.topology_service.topological_sort(workflow)
            except ValueError as e:
                if on_complete:
                    on_complete({"status": "FAILED", "error": f"Workflow has cycles: {e}"})
                return

            # Create execution session
            session_id = self.execution_manager.create_session(
                workflow_id=workflow.id,
                workflow_name=workflow.name,
                triggered_by=triggered_by,
                execution_order=sorted_node_ids,
            )

            # Start execution
            self.execution_manager.start_session()
            self.execution_manager.clear_context()

            # Execute nodes in topological order
            execution_results = {}

            for node_id in sorted_node_ids:
                # Check for cancellation
                if self._cancel_event.is_set():
                    self.execution_manager.end_session(status="CANCELLED")
                    if on_complete:
                        on_complete(
                            {
                                "session_id": session_id,
                                "status": "CANCELLED",
                                "results": execution_results,
                            }
                        )
                    return

                node = workflow.get_node(node_id)

                if not node:
                    continue

                # Notify node start
                if on_node_start:
                    on_node_start(node_id, node.name)

                # Execute node
                result = self._execute_node(node, workflow)

                execution_results[node_id] = result

                # Notify based on result
                if result.success:
                    if on_node_complete:
                        on_node_complete(node_id, result)
                else:
                    if on_node_error:
                        on_node_error(node_id, result.error or "Unknown error")

                    # Stop execution if node failed
                    self.execution_manager.end_session(status="FAILED")
                    if on_complete:
                        on_complete(
                            {
                                "session_id": session_id,
                                "status": "FAILED",
                                "results": execution_results,
                                "error": f"Node {node.name} failed: {result.error}",
                            }
                        )
                    return

            # End execution successfully
            self.execution_manager.end_session(status="COMPLETED")
            if on_complete:
                on_complete(
                    {
                        "session_id": session_id,
                        "status": "COMPLETED",
                        "results": execution_results,
                    }
                )

        except Exception as e:
            # Handle unexpected errors
            try:
                self.execution_manager.end_session(status="FAILED")
            except Exception:
                pass

            if on_complete:
                on_complete(
                    {
                        "status": "FAILED",
                        "error": f"Execution error: {str(e)}",
                    }
                )

    def _execute_node(self, node: BaseNode, workflow: Workflow) -> Any:
        """
        Execute a single node.

        Args:
            node: Node to execute
            workflow: Parent workflow

        Returns:
            Execution result
        """
        # Log node start
        self.execution_manager.log_node_start(node.id, node.name, node_type=node.__class__.__name__)

        # Get current context
        context = self.execution_manager.get_node_context()

        # Resolve expressions in node state
        resolved_state = self._resolve_node_state(node, context)

        # Update node state with resolved values
        if resolved_state:
            node.update_state(resolved_state)

        # Execute node
        try:
            result = node.execute(context)

            # Log success
            self.execution_manager.log_node_end(node.id, status="SUCCESS", output_data=result.data)

            # Update context with node output
            if result.success and result.data:
                self.execution_manager.set_node_context(node.id, node.name, result.data)

            return result

        except Exception as e:
            # Log error
            error_message = str(e)
            self.execution_manager.log_node_end(
                node.id, status="ERROR", error_message=error_message
            )

            # Return error result
            from lighthouse.domain.models.node import ExecutionResult

            return ExecutionResult.error_result(error=error_message, duration=0.0)

    def _resolve_node_state(self, node: BaseNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve expressions in node state.

        Args:
            node: Node whose state to resolve
            context: Current execution context

        Returns:
            Resolved state dictionary
        """
        resolved_state = {}

        for key, value in node.state.items():
            resolved_value = self.expression_service.resolve(value, context)
            resolved_state[key] = resolved_value

        return resolved_state

    def _build_connection_map(self, workflow: Workflow) -> Dict[str, List[str]]:
        """
        Build connection map from workflow.

        Args:
            workflow: Workflow

        Returns:
            Dictionary mapping target node ID to list of source node IDs
        """
        connection_map: Dict[str, List[str]] = {}

        for connection in workflow.connections:
            target_id = connection.to_node_id

            if target_id not in connection_map:
                connection_map[target_id] = []

            connection_map[target_id].append(connection.from_node_id)

        return connection_map

    def get_execution_manager(self) -> ExecutionManager:
        """
        Get the execution manager.

        Returns:
            ExecutionManager instance
        """
        return self.execution_manager
