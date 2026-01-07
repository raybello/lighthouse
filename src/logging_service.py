"""
Lighthouse Logging Service

Provides comprehensive execution tracking and logging capabilities
for workflow automation. Manages execution sessions, log files,
and provides real-time monitoring with historical execution review.

Author: Ray B.
Version: 2.0.0
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum


class ExecutionStatus(Enum):
    """Execution status states"""
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class LoggingService:
    """
    Manages execution tracking and logging for Lighthouse workflows.
    
    Provides:
    - Execution session management with unique IDs
    - Per-node log file creation and management
    - Execution metadata tracking and storage
    - Log rotation and cleanup
    - Real-time monitoring support
    
    Attributes:
        logs_dir (Path): Base directory for all logs (.logs/)
        registry_file (Path): Execution registry JSON file
        current_session (Dict): Currently active execution session
    """
    
    def __init__(self, logs_dir: str = ".logs"):
        """
        Initialize the logging service.
        
        Args:
            logs_dir: Base directory for log storage (default: .logs)
        """
        self.logs_dir = Path(logs_dir)
        self.registry_file = self.logs_dir / "execution_registry.json"
        self.current_session: Optional[Dict[str, Any]] = None
        self.node_logs: Dict[str, logging.Logger] = {}
        
        # Create logs directory structure
        self._setup_logs_directory()
        
        # Load or create execution registry
        self.execution_registry = self._load_registry()
    
    def _setup_logs_directory(self) -> None:
        """Create the logs directory structure if it doesn't exist."""
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create a .gitignore file to prevent logs from being committed
        gitignore_path = self.logs_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, "w") as f:
                f.write("# Ignore all log files\n*\n!.gitignore\n")
    
    def _load_registry(self) -> List[Dict[str, Any]]:
        """
        Load the execution registry from disk.
        
        Returns:
            List of execution metadata dictionaries
        """
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []
    
    def _save_registry(self) -> None:
        """Save the execution registry to disk."""
        with open(self.registry_file, "w") as f:
            json.dump(self.execution_registry, f, indent=2)
    
    def generate_execution_id(self) -> str:
        """
        Generate a unique execution ID.
        
        Format: exec_{timestamp}_{8char}
        
        Returns:
            Unique execution ID string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        random_suffix = str(uuid.uuid4())[:8]
        return f"exec_{timestamp}_{random_suffix}"
    
    def create_execution_session(
        self,
        triggered_by: str,
        node_count: int,
        topology: Dict[str, Any]
    ) -> str:
        """
        Create a new execution session and initialize logging.
        
        Args:
            triggered_by: ID of the node that triggered execution
            node_count: Total number of nodes in the workflow
            topology: Graph topology with nodes and edges
            
        Returns:
            Execution ID for the new session
        """
        execution_id = self.generate_execution_id()
        created_at = datetime.now().isoformat()
        
        # Create execution session metadata
        self.current_session = {
            "id": execution_id,
            "status": ExecutionStatus.INITIALIZING.value,
            "created_at": created_at,
            "started_at": None,
            "ended_at": None,
            "duration_seconds": None,
            "triggered_by": triggered_by,
            "node_count": node_count,
            "nodes_executed": 0,
            "nodes_failed": 0,
            "log_directory": str(self.logs_dir / execution_id),
            "topology": topology,
            "performance_metrics": {
                "total_cpu_time": 0.0,
                "peak_memory_mb": 0.0,
                "io_operations": 0
            },
            "node_logs": []
        }
        
        # Create execution-specific log directory
        exec_dir = self.logs_dir / execution_id
        exec_dir.mkdir(exist_ok=True)
        
        # Save initial metadata
        metadata_file = exec_dir / "execution_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(self.current_session, f, indent=2)
        
        # Create execution summary log file
        summary_log = exec_dir / "execution_summary.log"
        self._log_to_file(
            summary_log,
            "INFO",
            "SYSTEM",
            f"Execution session {execution_id} initialized"
        )
        
        return execution_id
    
    def start_execution(self) -> None:
        """Mark the execution session as started."""
        if self.current_session:
            self.current_session["status"] = ExecutionStatus.RUNNING.value
            self.current_session["started_at"] = datetime.now().isoformat()
            self._update_session_metadata()
    
    def end_execution(self, status: ExecutionStatus = ExecutionStatus.COMPLETED) -> None:
        """
        Finalize the execution session.
        
        Args:
            status: Final execution status (COMPLETED or FAILED)
        """
        if not self.current_session:
            return
        
        ended_at = datetime.now()
        self.current_session["status"] = status.value
        self.current_session["ended_at"] = ended_at.isoformat()
        
        # Calculate duration
        if self.current_session["started_at"]:
            started = datetime.fromisoformat(self.current_session["started_at"])
            duration = (ended_at - started).total_seconds()
            self.current_session["duration_seconds"] = duration
        
        # Update metadata
        self._update_session_metadata()
        
        # Add to execution registry
        self.execution_registry.append(self.current_session.copy())
        self._save_registry()
        
        # Log completion
        exec_dir = Path(self.current_session["log_directory"])
        summary_log = exec_dir / "execution_summary.log"
        self._log_to_file(
            summary_log,
            "INFO",
            "SYSTEM",
            f"Execution {self.current_session['id']} {status.value} "
            f"(Duration: {self.current_session['duration_seconds']:.2f}s)"
        )
        
        # Clear current session
        self.current_session = None
        self.node_logs.clear()
    
    def log_node_execution_start(self, node_id: str, node_name: str, node_type: str) -> str:
        """
        Log the start of a node execution.
        
        Args:
            node_id: Unique node identifier
            node_name: Display name of the node
            node_type: Type/class of the node
            
        Returns:
            Path to the node's log file
        """
        if not self.current_session:
            return ""
        
        exec_dir = Path(self.current_session["log_directory"])
        log_filename = f"{node_id}_{node_name.replace(' ', '_')}.log"
        log_file = exec_dir / log_filename
        
        # Create node execution log entry
        node_log_entry = {
            "node_id": node_id,
            "node_name": node_name,
            "node_type": node_type,
            "execution_id": self.current_session["id"],
            "status": "RUNNING",
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
            "duration_seconds": None,
            "log_file": log_filename,
            "error_message": None
        }
        
        self.current_session["node_logs"].append(node_log_entry)
        
        # Log to node-specific file
        self._log_to_file(
            log_file,
            "INFO",
            node_id,
            f"Started execution of {node_name} ({node_type})"
        )
        
        # Log to summary file
        summary_log = exec_dir / "execution_summary.log"
        self._log_to_file(
            summary_log,
            "INFO",
            node_id,
            f"Node {node_name} execution started"
        )
        
        return str(log_file)
    
    def log_node_execution_end(
        self,
        node_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log the completion of a node execution.
        
        Args:
            node_id: Unique node identifier
            status: Completion status (COMPLETED, FAILED, etc.)
            output_data: Node output data
            error_message: Error message if execution failed
        """
        if not self.current_session:
            return
        
        # Find the node log entry
        node_log_entry = None
        for entry in self.current_session["node_logs"]:
            if entry["node_id"] == node_id and entry["ended_at"] is None:
                node_log_entry = entry
                break
        
        if not node_log_entry:
            return
        
        # Update node log entry
        ended_at = datetime.now()
        node_log_entry["status"] = status
        node_log_entry["ended_at"] = ended_at.isoformat()
        node_log_entry["error_message"] = error_message
        
        # Calculate duration
        started = datetime.fromisoformat(node_log_entry["started_at"])
        duration = (ended_at - started).total_seconds()
        node_log_entry["duration_seconds"] = duration
        
        # Update execution counters
        if status == "COMPLETED":
            self.current_session["nodes_executed"] += 1
        elif status == "FAILED":
            self.current_session["nodes_failed"] += 1
        
        # Log to node-specific file
        exec_dir = Path(self.current_session["log_directory"])
        log_file = exec_dir / node_log_entry["log_file"]
        
        if output_data:
            self._log_to_file(
                log_file,
                "INFO",
                node_id,
                f"Output data: {json.dumps(output_data, indent=2)}"
            )
        
        log_level = "ERROR" if status == "FAILED" else "INFO"
        message = f"Node execution {status} (Duration: {duration:.2f}s)"
        if error_message:
            message += f" - Error: {error_message}"
        
        self._log_to_file(log_file, log_level, node_id, message)
        
        # Log to summary file
        summary_log = exec_dir / "execution_summary.log"
        self._log_to_file(summary_log, log_level, node_id, message)
        
        # Log errors to dedicated error log
        if error_message:
            error_log = exec_dir / "errors.log"
            self._log_to_file(
                error_log,
                "ERROR",
                node_id,
                f"{node_log_entry['node_name']}: {error_message}"
            )
        
        # Update session metadata
        self._update_session_metadata()
    
    def log_to_node_file(self, node_id: str, level: str, message: str) -> None:
        """
        Write a log message to a specific node's log file.
        
        Args:
            node_id: Node identifier
            level: Log level (INFO, DEBUG, WARN, ERROR)
            message: Log message
        """
        if not self.current_session:
            return
        
        # Find the node log entry
        node_log_entry = None
        for entry in self.current_session["node_logs"]:
            if entry["node_id"] == node_id:
                node_log_entry = entry
                break
        
        if not node_log_entry:
            return
        
        exec_dir = Path(self.current_session["log_directory"])
        log_file = exec_dir / node_log_entry["log_file"]
        
        self._log_to_file(log_file, level, node_id, message)
    
    def _log_to_file(
        self,
        file_path: Path,
        level: str,
        source: str,
        message: str
    ) -> None:
        """
        Write a formatted log entry to a file.
        
        Args:
            file_path: Path to the log file
            level: Log level
            source: Source identifier (node ID or SYSTEM)
            message: Log message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] [{source}] {message}\n"
        
        with open(file_path, "a") as f:
            f.write(log_entry)
    
    def _update_session_metadata(self) -> None:
        """Update the execution metadata file on disk."""
        if not self.current_session:
            return
        
        exec_dir = Path(self.current_session["log_directory"])
        metadata_file = exec_dir / "execution_metadata.json"
        
        with open(metadata_file, "w") as f:
            json.dump(self.current_session, f, indent=2)
    
    def get_execution_history(
        self,
        limit: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve execution history with optional filtering.
        
        Args:
            limit: Maximum number of executions to return
            status_filter: Filter by execution status
            
        Returns:
            List of execution metadata dictionaries
        """
        history = self.execution_registry.copy()
        
        # Apply status filter
        if status_filter:
            history = [
                exec_data for exec_data in history
                if exec_data["status"] == status_filter
            ]
        
        # Sort by created_at (most recent first)
        history.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply limit
        if limit:
            history = history[:limit]
        
        return history
    
    def get_execution_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve execution metadata by ID.
        
        Args:
            execution_id: Execution identifier
            
        Returns:
            Execution metadata dictionary or None if not found
        """
        for exec_data in self.execution_registry:
            if exec_data["id"] == execution_id:
                return exec_data.copy()
        return None
    
    def read_log_file(self, execution_id: str, filename: str) -> str:
        """
        Read the contents of a log file.
        
        Args:
            execution_id: Execution identifier
            filename: Name of the log file
            
        Returns:
            Log file contents as string
        """
        log_file = self.logs_dir / execution_id / filename
        
        if not log_file.exists():
            return ""
        
        try:
            with open(log_file, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading log file: {str(e)}"
    
    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the current execution session.
        
        Returns:
            Current session metadata or None
        """
        return self.current_session.copy() if self.current_session else None
