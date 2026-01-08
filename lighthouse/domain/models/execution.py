"""Execution session domain models."""

import multiprocessing
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionStatus(Enum):
    """Execution session status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExecutionMode(Enum):
    """Execution mode for workflow execution."""

    SEQUENTIAL = "sequential"  # Execute nodes one at a time (default)
    PARALLEL = "parallel"  # Execute independent nodes in parallel using threads


@dataclass
class ExecutionConfig:
    """Configuration for workflow execution."""

    mode: ExecutionMode = ExecutionMode.PARALLEL
    max_workers: int = field(default_factory=lambda: min(4, multiprocessing.cpu_count()))
    enable_profiling: bool = True
    fail_fast: bool = True  # Stop on first error vs collect all errors


@dataclass
class NodeExecutionRecord:
    """
    Record of a single node's execution within a session.

    Tracks inputs, outputs, duration, and status for a node execution.
    Includes profiling fields for parallel execution analysis.
    """

    node_id: str
    node_name: str
    status: ExecutionStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    # Profiling fields for parallel execution
    thread_id: Optional[str] = None
    level: int = 0  # Execution level (nodes at same level can run in parallel)
    relative_start_seconds: float = 0.0  # Start time relative to session start
    relative_end_seconds: float = 0.0  # End time relative to session start
    node_type: str = "Unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
            "logs": self.logs,
            "thread_id": self.thread_id,
            "level": self.level,
            "relative_start_seconds": self.relative_start_seconds,
            "relative_end_seconds": self.relative_end_seconds,
            "node_type": self.node_type,
        }


@dataclass
class ExecutionSession:
    """
    Domain model for a workflow execution session.

    Tracks the complete lifecycle of a workflow execution,
    including all node executions, timing, and final status.

    Attributes:
        id: Unique session identifier
        workflow_id: ID of the workflow being executed
        workflow_name: Name of the workflow
        status: Current session status
        triggered_by: Node ID that triggered the execution
        start_time: When execution started
        end_time: When execution completed
        execution_order: Order in which nodes should execute
        node_records: Record of each node's execution
        context: Shared context for expression resolution
    """

    id: str
    workflow_id: str
    workflow_name: str
    status: ExecutionStatus
    triggered_by: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_order: List[str] = field(default_factory=list)
    node_records: Dict[str, NodeExecutionRecord] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Mark session as started."""
        self.status = ExecutionStatus.RUNNING
        self.start_time = datetime.now()

    def complete(self) -> None:
        """Mark session as completed successfully."""
        self.status = ExecutionStatus.COMPLETED
        self.end_time = datetime.now()

    def fail(self, error: str) -> None:
        """
        Mark session as failed.

        Args:
            error: Error message describing the failure
        """
        self.status = ExecutionStatus.FAILED
        self.end_time = datetime.now()

    def cancel(self) -> None:
        """Mark session as cancelled."""
        self.status = ExecutionStatus.CANCELLED
        self.end_time = datetime.now()

    def add_node_record(self, record: NodeExecutionRecord) -> None:
        """
        Add a node execution record.

        Args:
            record: Node execution record to add
        """
        self.node_records[record.node_id] = record

    def get_node_record(self, node_id: str) -> Optional[NodeExecutionRecord]:
        """
        Get execution record for a specific node.

        Args:
            node_id: Node identifier

        Returns:
            Node execution record or None if not found
        """
        return self.node_records.get(node_id)

    def get_node_output(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get output data from a specific node.

        Args:
            node_id: Node identifier

        Returns:
            Node output data or None if not found
        """
        record = self.get_node_record(node_id)
        return record.outputs if record else None

    def update_context(self, node_id: str, node_name: str, output: Dict[str, Any]) -> None:
        """
        Update execution context with node output.

        Args:
            node_id: Node identifier
            node_name: Node name (for expression references)
            output: Output data from node execution
        """
        self.context[node_name] = output

    def get_duration_seconds(self) -> float:
        """
        Calculate total execution duration.

        Returns:
            Duration in seconds, or 0 if not started
        """
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def get_completed_nodes_count(self) -> int:
        """Get count of successfully completed nodes."""
        return sum(
            1 for record in self.node_records.values() if record.status == ExecutionStatus.COMPLETED
        )

    def get_failed_nodes_count(self) -> int:
        """Get count of failed nodes."""
        return sum(
            1 for record in self.node_records.values() if record.status == ExecutionStatus.FAILED
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize session to dictionary.

        Returns:
            Dictionary representation of the session
        """
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "triggered_by": self.triggered_by,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration_seconds(),
            "execution_order": self.execution_order,
            "node_records": {nid: record.to_dict() for nid, record in self.node_records.items()},
            "completed_nodes": self.get_completed_nodes_count(),
            "failed_nodes": self.get_failed_nodes_count(),
        }
