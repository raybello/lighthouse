"""
Execution manager for tracking execution sessions and state.

Pure business logic with NO UI dependencies.
Thread-safe for parallel execution support.
"""

import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from lighthouse.domain.models.execution import (
    ExecutionSession,
    ExecutionStatus,
    NodeExecutionRecord,
)
from lighthouse.domain.protocols.logger_protocol import ILogger


class ExecutionManager:
    """
    Manages execution sessions and tracks execution state.

    Responsible for:
    - Creating and managing execution sessions
    - Tracking node execution records
    - Building and maintaining node context
    - Managing execution lifecycle
    - Delegating logging to ILogger implementation

    Thread-safe for parallel execution support.
    """

    def __init__(self, logger: Optional[ILogger] = None):
        """
        Initialize the execution manager.

        Args:
            logger: Optional logger implementation for file/remote logging
        """
        self.current_session: Optional[ExecutionSession] = None
        self.session_history: list[ExecutionSession] = []
        self.node_context: Dict[str, Dict[str, Any]] = {}
        self.logger = logger
        # Thread safety locks
        self._context_lock = threading.Lock()
        self._records_lock = threading.Lock()
        # Session start time for relative timing
        self._session_start_time: float = 0.0

    def create_session(
        self,
        workflow_id: str,
        workflow_name: str,
        triggered_by: str,
        execution_order: Optional[list[str]] = None,
    ) -> str:
        """
        Create a new execution session.

        Args:
            workflow_id: ID of the workflow being executed
            workflow_name: Name of the workflow
            triggered_by: Node that triggered the execution
            execution_order: Optional topologically sorted node IDs

        Returns:
            Execution session ID
        """
        session_id = str(uuid.uuid4())[:8]

        self.current_session = ExecutionSession(
            id=session_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            status=ExecutionStatus.PENDING,
            triggered_by=triggered_by,
            execution_order=execution_order or [],
        )

        self.node_context = {}

        # Create logging session if logger is available
        if self.logger:
            self.logger.create_session(
                execution_id=session_id,
                metadata={
                    "workflow_id": workflow_id,
                    "workflow_name": workflow_name,
                    "triggered_by": triggered_by,
                    "node_count": len(execution_order) if execution_order else 0,
                    "execution_order": execution_order or [],
                },
            )

        return session_id

    def start_session(self) -> None:
        """Mark session as started."""
        if not self.current_session:
            raise RuntimeError("No active session to start")

        self.current_session.start()
        self._session_start_time = time.time()

        # Start logging session
        if self.logger:
            self.logger.start_session(self.current_session.id)

    def end_session(self, status: str = "COMPLETED") -> None:
        """
        End the current execution session.

        Args:
            status: Final session status (COMPLETED, FAILED, CANCELLED)
        """
        if not self.current_session:
            raise RuntimeError("No active session to end")

        # Calculate duration
        duration = 0.0
        if self.current_session.start_time:
            duration = (datetime.now() - self.current_session.start_time).total_seconds()

        # Use domain model methods
        if status == "COMPLETED":
            self.current_session.complete()
        elif status == "FAILED":
            self.current_session.fail(error="Execution failed")
        elif status == "CANCELLED":
            self.current_session.cancel()
        else:
            # Fallback
            self.current_session.status = ExecutionStatus.COMPLETED

        # End logging session
        if self.logger:
            self.logger.end_session(
                execution_id=self.current_session.id, status=status, duration=duration
            )

        # Archive session
        self.session_history.append(self.current_session)
        self.current_session = None

    def log_node_start(
        self, node_id: str, node_name: str, node_type: str = "Unknown", level: int = 0
    ) -> None:
        """
        Log the start of a node execution.

        Args:
            node_id: Node ID
            node_name: Node name
            node_type: Node type/class
            level: Execution level (for parallel execution profiling)
        """
        if not self.current_session:
            raise RuntimeError("No active session for logging")

        current_time = time.time()
        relative_start = current_time - self._session_start_time

        record = NodeExecutionRecord(
            node_id=node_id,
            node_name=node_name,
            status=ExecutionStatus.RUNNING,
            start_time=datetime.now(),
            thread_id=threading.current_thread().name,
            level=level,
            relative_start_seconds=relative_start,
            node_type=node_type,
        )

        with self._records_lock:
            self.current_session.add_node_record(record)

        # Log to file if logger is available
        if self.logger:
            self.logger.log_node_start(
                execution_id=self.current_session.id,
                node_id=node_id,
                node_name=node_name,
                node_type=node_type,
            )

    def log_node_end(
        self,
        node_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log the end of a node execution.

        Args:
            node_id: Node ID
            status: Execution status (SUCCESS, ERROR, FAILED)
            output_data: Node output data
            error_message: Error message if failed
        """
        if not self.current_session:
            raise RuntimeError("No active session for logging")

        with self._records_lock:
            record = self.current_session.get_node_record(node_id)
            if not record:
                raise KeyError(f"No record found for node {node_id}")

            # Update record
            record.end_time = datetime.now()
            current_time = time.time()
            record.relative_end_seconds = current_time - self._session_start_time

            if record.start_time:
                record.duration_seconds = (record.end_time - record.start_time).total_seconds()

            # Map status strings to ExecutionStatus
            if status in ("SUCCESS", "COMPLETED"):
                record.status = ExecutionStatus.COMPLETED
            elif status in ("ERROR", "FAILED"):
                record.status = ExecutionStatus.FAILED
            else:
                record.status = ExecutionStatus.FAILED

            if output_data:
                record.outputs = output_data
            if error_message:
                record.error = error_message

        # Log to file if logger is available
        if self.logger:
            self.logger.log_node_end(
                execution_id=self.current_session.id,
                node_id=node_id,
                node_name=record.node_name,
                success=(status in ("SUCCESS", "COMPLETED")),
                duration=record.duration_seconds or 0.0,
                output_data=output_data,
                error=error_message,
            )

    def set_node_context(self, node_id: str, node_name: str, output_data: Dict[str, Any]) -> None:
        """
        Store node output in context for expression evaluation.

        Thread-safe for parallel execution.

        Args:
            node_id: Node ID
            node_name: Node name
            output_data: Node output data
        """
        with self._context_lock:
            # Store by both ID and name for flexible referencing
            self.node_context[node_id] = {"data": output_data}
            self.node_context[node_name] = {"data": output_data}

    def get_node_context(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current node context.

        Thread-safe for parallel execution.

        Returns:
            Node context dictionary
        """
        with self._context_lock:
            return self.node_context.copy()

    def clear_context(self) -> None:
        """Clear the node context."""
        with self._context_lock:
            self.node_context = {}

    def get_execution_trace(self, node_id: str) -> Optional[NodeExecutionRecord]:
        """
        Get execution record for a node.

        Args:
            node_id: Node ID

        Returns:
            Node execution record or None
        """
        if not self.current_session:
            return None
        return self.current_session.get_node_record(node_id)

    def get_all_traces(self) -> Dict[str, NodeExecutionRecord]:
        """
        Get all execution records for current session.

        Returns:
            Dictionary of node ID to execution record
        """
        if not self.current_session:
            return {}
        return self.current_session.node_records.copy()

    def get_current_session(self) -> Optional[ExecutionSession]:
        """
        Get the current execution session.

        Returns:
            Current session or None
        """
        return self.current_session

    def get_session_history(self) -> list[ExecutionSession]:
        """
        Get execution session history.

        Returns:
            List of completed sessions
        """
        return self.session_history.copy()

    def log_to_node(self, node_id: str, level: str, message: str) -> None:
        """
        Log a message to a specific node's log file.

        Args:
            node_id: Node ID
            level: Log level (INFO, DEBUG, WARN, ERROR)
            message: Log message
        """
        if not self.current_session or not self.logger:
            return

        self.logger.log_to_node(
            execution_id=self.current_session.id, node_id=node_id, level=level, message=message
        )

    def get_profiling_data(self) -> Dict[str, Any]:
        """
        Get profiling data for the current or last completed session.

        Returns:
            Dictionary containing execution statistics and traces
        """
        session = self.current_session
        if not session and self.session_history:
            session = self.session_history[-1]

        if not session:
            return {"error": "No session data available"}

        traces = []
        level_times: Dict[int, float] = {}

        with self._records_lock:
            for record in session.node_records.values():
                traces.append(
                    {
                        "node_id": record.node_id,
                        "node_name": record.node_name,
                        "node_type": record.node_type,
                        "thread_id": record.thread_id,
                        "level": record.level,
                        "start_time": record.relative_start_seconds,
                        "end_time": record.relative_end_seconds,
                        "duration": record.duration_seconds,
                        "success": record.status == ExecutionStatus.COMPLETED,
                        "error": record.error,
                    }
                )
                # Track max end time per level
                if record.level not in level_times:
                    level_times[record.level] = 0.0
                level_times[record.level] = max(
                    level_times[record.level], record.relative_end_seconds
                )

        return {
            "session_id": session.id,
            "workflow_name": session.workflow_name,
            "status": session.status.value,
            "total_duration": session.get_duration_seconds(),
            "total_nodes": len(session.node_records),
            "completed_nodes": session.get_completed_nodes_count(),
            "failed_nodes": session.get_failed_nodes_count(),
            "traces": traces,
            "levels": len(level_times),
        }
