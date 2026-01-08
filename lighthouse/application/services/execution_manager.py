"""
Execution manager for tracking execution sessions and state.

Pure business logic with NO UI dependencies.
"""

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

    def log_node_start(self, node_id: str, node_name: str, node_type: str = "Unknown") -> None:
        """
        Log the start of a node execution.

        Args:
            node_id: Node ID
            node_name: Node name
            node_type: Node type/class
        """
        if not self.current_session:
            raise RuntimeError("No active session for logging")

        record = NodeExecutionRecord(
            node_id=node_id,
            node_name=node_name,
            status=ExecutionStatus.RUNNING,
            start_time=datetime.now(),
        )

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

        record = self.current_session.get_node_record(node_id)
        if not record:
            raise KeyError(f"No record found for node {node_id}")

        # Update record
        record.end_time = datetime.now()
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

        Args:
            node_id: Node ID
            node_name: Node name
            output_data: Node output data
        """
        # Store by both ID and name for flexible referencing
        self.node_context[node_id] = {"data": output_data}
        self.node_context[node_name] = {"data": output_data}

    def get_node_context(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current node context.

        Returns:
            Node context dictionary
        """
        return self.node_context.copy()

    def clear_context(self) -> None:
        """Clear the node context."""
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
