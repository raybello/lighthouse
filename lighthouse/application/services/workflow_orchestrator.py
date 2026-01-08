"""
Workflow orchestrator for coordinating node execution.

Pure business logic with NO UI dependencies.
Supports both sequential and parallel execution modes.
"""

import copy
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event, Thread
from typing import Any, Callable, Dict, List, Optional, Tuple

from lighthouse.application.services.execution_manager import ExecutionManager
from lighthouse.domain.models.execution import ExecutionConfig, ExecutionMode
from lighthouse.domain.models.node import ExecutionResult
from lighthouse.domain.models.workflow import Workflow
from lighthouse.domain.services.expression_service import ExpressionService
from lighthouse.domain.services.topology_service import TopologyService
from lighthouse.nodes.base.base_node import BaseNode

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrates workflow execution by coordinating nodes.

    Responsible for:
    - Topological sorting of nodes into execution levels
    - Sequential or parallel node execution based on configuration
    - Expression resolution with thread-safe context management
    - Execution profiling and statistics
    """

    def __init__(
        self,
        topology_service: Optional[TopologyService] = None,
        expression_service: Optional[ExpressionService] = None,
        execution_manager: Optional[ExecutionManager] = None,
        execution_config: Optional[ExecutionConfig] = None,
    ):
        """
        Initialize the workflow orchestrator.

        Args:
            topology_service: Service for graph topology operations
            expression_service: Service for expression evaluation
            execution_manager: Manager for execution state
            execution_config: Configuration for execution mode and parallelism
        """
        self.topology_service = topology_service or TopologyService()
        self.expression_service = expression_service or ExpressionService()
        self.execution_manager = execution_manager or ExecutionManager()
        self.execution_config = execution_config or ExecutionConfig()
        self._cancel_event = Event()
        self._execution_thread: Optional[Thread] = None

    def execute_workflow(
        self,
        workflow: Workflow,
        triggered_by: str,
        config: Optional[ExecutionConfig] = None,
    ) -> Dict[str, Any]:
        """
        Execute a workflow synchronously with optional parallel execution.

        Args:
            workflow: Workflow to execute
            triggered_by: Node that triggered execution
            config: Optional execution config (overrides instance config)

        Returns:
            Execution results dictionary with profiling data

        Raises:
            ValueError: If workflow has cycles or is invalid
        """
        config = config or self.execution_config

        # Validate workflow
        if not workflow.nodes:
            raise ValueError("Workflow has no nodes")

        # Get execution levels (nodes at same level can run in parallel)
        try:
            execution_levels = self.topology_service.get_execution_levels(workflow)
        except ValueError as e:
            raise ValueError(f"Workflow has cycles: {e}")

        # Flatten for execution order tracking
        sorted_node_ids = [node_id for level in execution_levels for node_id in level]

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

        logger.info(
            f"Starting workflow execution: {workflow.name} "
            f"({len(execution_levels)} levels, {len(sorted_node_ids)} nodes, "
            f"mode={config.mode.value})"
        )

        # Execute each level
        execution_results: Dict[str, ExecutionResult] = {}
        failed_node: Optional[Tuple[str, str]] = None  # (node_id, error)

        for level_idx, level_node_ids in enumerate(execution_levels):
            # Get nodes for this level
            level_nodes = [
                workflow.get_node(node_id)
                for node_id in level_node_ids
                if workflow.get_node(node_id) is not None
            ]

            if not level_nodes:
                continue

            logger.info(
                f"Executing level {level_idx}: {[n.name for n in level_nodes]} "
                f"({len(level_nodes)} nodes)"
            )

            # Execute level based on mode
            if config.mode == ExecutionMode.PARALLEL and len(level_nodes) > 1:
                level_results, level_error = self._execute_level_parallel(
                    level_nodes, level_idx, workflow, config.max_workers, config.fail_fast
                )
            else:
                level_results, level_error = self._execute_level_sequential(
                    level_nodes, level_idx, workflow, config.fail_fast
                )

            # Merge results
            execution_results.update(level_results)

            # Handle errors
            if level_error:
                failed_node = level_error
                if config.fail_fast:
                    break

        # End execution
        if failed_node:
            self.execution_manager.end_session(status="FAILED")
            node_id, error = failed_node
            node = workflow.get_node(node_id)
            node_name = node.name if node else node_id
            return {
                "session_id": session_id,
                "status": "FAILED",
                "results": execution_results,
                "error": f"Node {node_name} failed: {error}",
                "execution_mode": config.mode.value,
                "levels": len(execution_levels),
            }

        self.execution_manager.end_session(status="COMPLETED")

        return {
            "session_id": session_id,
            "status": "COMPLETED",
            "results": execution_results,
            "execution_mode": config.mode.value,
            "levels": len(execution_levels),
        }

    def _execute_level_parallel(
        self,
        nodes: List[BaseNode],
        level_idx: int,
        workflow: Workflow,
        max_workers: int,
        fail_fast: bool,
    ) -> Tuple[Dict[str, ExecutionResult], Optional[Tuple[str, str]]]:
        """
        Execute all nodes in a level using parallel threads.

        Args:
            nodes: List of nodes to execute
            level_idx: Level index for profiling
            workflow: Parent workflow
            max_workers: Maximum number of worker threads
            fail_fast: Stop on first error

        Returns:
            Tuple of (results dict, optional (node_id, error) if failed)
        """
        results: Dict[str, ExecutionResult] = {}
        failed_node: Optional[Tuple[str, str]] = None

        logger.info(f"Executing {len(nodes)} nodes in parallel (max_workers={max_workers})")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all nodes for execution
            future_to_node = {
                executor.submit(self._execute_node, node, workflow, level_idx): node
                for node in nodes
            }

            # Collect results as they complete
            for future in as_completed(future_to_node):
                node = future_to_node[future]
                try:
                    result = future.result()
                    results[node.id] = result

                    if not result.success:
                        failed_node = (node.id, result.error or "Unknown error")
                        if fail_fast:
                            # Cancel remaining futures
                            for f in future_to_node:
                                f.cancel()
                            break

                except Exception as e:
                    error_msg = str(e)
                    results[node.id] = ExecutionResult.error_result(error=error_msg)
                    failed_node = (node.id, error_msg)
                    if fail_fast:
                        for f in future_to_node:
                            f.cancel()
                        break

        return results, failed_node

    def _execute_level_sequential(
        self,
        nodes: List[BaseNode],
        level_idx: int,
        workflow: Workflow,
        fail_fast: bool,
    ) -> Tuple[Dict[str, ExecutionResult], Optional[Tuple[str, str]]]:
        """
        Execute all nodes in a level sequentially.

        Args:
            nodes: List of nodes to execute
            level_idx: Level index for profiling
            workflow: Parent workflow
            fail_fast: Stop on first error

        Returns:
            Tuple of (results dict, optional (node_id, error) if failed)
        """
        results: Dict[str, ExecutionResult] = {}
        failed_node: Optional[Tuple[str, str]] = None

        for node in nodes:
            result = self._execute_node(node, workflow, level_idx)
            results[node.id] = result

            if not result.success:
                failed_node = (node.id, result.error or "Unknown error")
                if fail_fast:
                    break

        return results, failed_node

    def execute_workflow_async(
        self,
        workflow: Workflow,
        triggered_by: str,
        on_node_start: Optional[Callable[[str, str], None]] = None,
        on_node_complete: Optional[Callable[[str, Any], None]] = None,
        on_node_error: Optional[Callable[[str, str], None]] = None,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
        config: Optional[ExecutionConfig] = None,
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
            config: Optional execution config (overrides instance config)

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
                config,
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
        config: Optional[ExecutionConfig] = None,
    ) -> None:
        """
        Internal method to execute workflow in a thread with parallel support.

        Args:
            workflow: Workflow to execute
            triggered_by: Node that triggered execution
            on_node_start: Callback when a node starts
            on_node_complete: Callback when a node completes
            on_node_error: Callback when a node errors
            on_complete: Callback when execution completes
            config: Optional execution config
        """
        config = config or self.execution_config

        try:
            # Validate workflow
            if not workflow.nodes:
                if on_complete:
                    on_complete({"status": "FAILED", "error": "Workflow has no nodes"})
                return

            # Get execution levels
            try:
                execution_levels = self.topology_service.get_execution_levels(workflow)
            except ValueError as e:
                if on_complete:
                    on_complete({"status": "FAILED", "error": f"Workflow has cycles: {e}"})
                return

            sorted_node_ids = [node_id for level in execution_levels for node_id in level]

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

            # Execute levels
            execution_results: Dict[str, ExecutionResult] = {}
            failed_node: Optional[Tuple[str, str]] = None

            for level_idx, level_node_ids in enumerate(execution_levels):
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

                # Get nodes for this level
                level_nodes = [
                    workflow.get_node(node_id)
                    for node_id in level_node_ids
                    if workflow.get_node(node_id) is not None
                ]

                if not level_nodes:
                    continue

                # Notify starts
                for node in level_nodes:
                    if on_node_start:
                        on_node_start(node.id, node.name)

                # Execute level
                if config.mode == ExecutionMode.PARALLEL and len(level_nodes) > 1:
                    level_results, level_error = self._execute_level_parallel(
                        level_nodes, level_idx, workflow, config.max_workers, config.fail_fast
                    )
                else:
                    level_results, level_error = self._execute_level_sequential(
                        level_nodes, level_idx, workflow, config.fail_fast
                    )

                # Merge results and notify
                for node_id, result in level_results.items():
                    execution_results[node_id] = result
                    if result.success:
                        if on_node_complete:
                            on_node_complete(node_id, result)
                    else:
                        if on_node_error:
                            on_node_error(node_id, result.error or "Unknown error")

                # Handle errors
                if level_error:
                    failed_node = level_error
                    if config.fail_fast:
                        break

            # End execution
            if failed_node:
                self.execution_manager.end_session(status="FAILED")
                node_id, error = failed_node
                node = workflow.get_node(node_id)
                node_name = node.name if node else node_id
                if on_complete:
                    on_complete(
                        {
                            "session_id": session_id,
                            "status": "FAILED",
                            "results": execution_results,
                            "error": f"Node {node_name} failed: {error}",
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
                        "execution_mode": config.mode.value,
                        "levels": len(execution_levels),
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

    def _execute_node(self, node: BaseNode, workflow: Workflow, level: int = 0) -> ExecutionResult:
        """
        Execute a single node.

        Thread-safe for parallel execution.

        Args:
            node: Node to execute
            workflow: Parent workflow
            level: Execution level (for profiling)

        Returns:
            Execution result
        """
        # Log node start with level for profiling
        self.execution_manager.log_node_start(
            node.id, node.name, node_type=node.__class__.__name__, level=level
        )

        # Get current context (thread-safe)
        context = self.execution_manager.get_node_context()

        # Save original state (deep copy to preserve expressions)
        original_state = copy.deepcopy(node.state)

        try:
            # Resolve expressions in node state
            resolved_state = self._resolve_node_state(node, context)

            # Temporarily update node state with resolved values
            if resolved_state:
                node.state = resolved_state

            # Execute node
            result = node.execute(context)

            # Log success
            self.execution_manager.log_node_end(node.id, status="SUCCESS", output_data=result.data)

            # Update context with node output (thread-safe)
            if result.success and result.data:
                self.execution_manager.set_node_context(node.id, node.name, result.data)

            return result

        except Exception as e:
            # Log error
            error_message = str(e)
            self.execution_manager.log_node_end(
                node.id, status="ERROR", error_message=error_message
            )

            return ExecutionResult.error_result(error=error_message, duration=0.0)

        finally:
            # ALWAYS restore original state with expressions intact (even if execution failed)
            node.state = original_state

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
