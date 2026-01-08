"""
File-based logging service for Lighthouse workflows.

Creates a directory per execution in .logs/ with separate log files
for each node execution, matching the legacy logging behavior.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileLogger:
    """
    File-based logging service for workflow execution tracking.

    Creates structured log directories with:
    - One directory per execution in .logs/exec_<timestamp>_<id>/
    - Separate log file for each node execution
    - execution_metadata.json with session details
    - execution_summary.log with high-level events
    - errors.log for all errors
    """

    def __init__(self, logs_dir: str = ".logs"):
        """
        Initialize the file logger.

        Args:
            logs_dir: Base directory for log storage (default: .logs)
        """
        self.logs_dir = Path(logs_dir)
        self.current_session: Optional[Dict[str, Any]] = None
        self.registry_file = self.logs_dir / "execution_registry.json"
        self.execution_registry: List[Dict[str, Any]] = []

        # Setup logs directory
        self._setup_logs_directory()

        # Load registry
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

    def create_session(self, execution_id: str, metadata: Dict[str, Any]) -> None:
        """
        Create a new logging session for a workflow execution.

        Args:
            execution_id: Unique execution identifier
            metadata: Session metadata (workflow name, trigger, etc.)
        """
        created_at = datetime.now().isoformat()

        # Create session metadata
        self.current_session = {
            "id": execution_id,
            "status": "INITIALIZING",
            "created_at": created_at,
            "started_at": None,
            "ended_at": None,
            "duration_seconds": None,
            "workflow_id": metadata.get("workflow_id", ""),
            "workflow_name": metadata.get("workflow_name", ""),
            "triggered_by": metadata.get("triggered_by", ""),
            "node_count": metadata.get("node_count", 0),
            "nodes_executed": 0,
            "nodes_failed": 0,
            "log_directory": str(self.logs_dir / execution_id),
            "execution_order": metadata.get("execution_order", []),
            "node_logs": [],
        }

        # Create execution-specific log directory
        exec_dir = self.logs_dir / execution_id
        exec_dir.mkdir(exist_ok=True)

        # Save initial metadata
        self._save_session_metadata()

        # Create execution summary log file
        summary_log = exec_dir / "execution_summary.log"
        self._log_to_file(
            summary_log, "INFO", "SYSTEM", f"Execution session {execution_id} initialized"
        )

    def start_session(self, execution_id: str) -> None:
        """
        Mark the execution session as started.

        Args:
            execution_id: Execution identifier
        """
        if not self.current_session or self.current_session["id"] != execution_id:
            return

        self.current_session["status"] = "RUNNING"
        self.current_session["started_at"] = datetime.now().isoformat()
        self._save_session_metadata()

    def end_session(self, execution_id: str, status: str, duration: float) -> None:
        """
        Finalize a logging session.

        Args:
            execution_id: Execution session ID
            status: Final status (COMPLETED, FAILED, CANCELLED)
            duration: Total session duration in seconds
        """
        if not self.current_session or self.current_session["id"] != execution_id:
            return

        ended_at = datetime.now()
        self.current_session["status"] = status
        self.current_session["ended_at"] = ended_at.isoformat()
        self.current_session["duration_seconds"] = duration

        # Update metadata
        self._save_session_metadata()

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
            f"Execution {execution_id} {status} (Duration: {duration:.2f}s)",
        )

        # Clear current session
        self.current_session = None

    def log(self, execution_id: str, level: str, source: str, message: str) -> None:
        """
        Write a log message.

        Args:
            execution_id: Execution session ID
            level: Log level (DEBUG, INFO, WARN, ERROR)
            source: Source identifier (node ID or SYSTEM)
            message: Log message content
        """
        if not self.current_session or self.current_session["id"] != execution_id:
            return

        exec_dir = Path(self.current_session["log_directory"])
        summary_log = exec_dir / "execution_summary.log"

        self._log_to_file(summary_log, level, source, message)

    def log_node_start(
        self, execution_id: str, node_id: str, node_name: str, node_type: str = "Unknown"
    ) -> None:
        """
        Log the start of a node execution.

        Args:
            execution_id: Execution session ID
            node_id: Node identifier
            node_name: Node display name
            node_type: Node type/class
        """
        if not self.current_session or self.current_session["id"] != execution_id:
            return

        exec_dir = Path(self.current_session["log_directory"])
        log_filename = f"{node_id}_{node_name.replace(' ', '_')}.log"
        log_file = exec_dir / log_filename

        # Create node execution log entry
        node_log_entry = {
            "node_id": node_id,
            "node_name": node_name,
            "node_type": node_type,
            "execution_id": execution_id,
            "status": "RUNNING",
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
            "duration_seconds": None,
            "log_file": log_filename,
            "error_message": None,
            "outputs": None,
        }

        self.current_session["node_logs"].append(node_log_entry)

        # Log to node-specific file
        self._log_to_file(
            log_file, "INFO", node_id, f"Started execution of {node_name} ({node_type})"
        )

        # Log to summary file
        summary_log = exec_dir / "execution_summary.log"
        self._log_to_file(summary_log, "INFO", node_id, f"Node {node_name} execution started")

    def log_node_end(
        self,
        execution_id: str,
        node_id: str,
        node_name: str,
        success: bool,
        duration: float,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Log the completion of a node execution.

        Args:
            execution_id: Execution session ID
            node_id: Node identifier
            node_name: Node display name
            success: Whether execution succeeded
            duration: Execution duration in seconds
            output_data: Node output data
            error: Error message if failed
        """
        if not self.current_session or self.current_session["id"] != execution_id:
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
        status = "COMPLETED" if success else "FAILED"
        node_log_entry["status"] = status
        node_log_entry["ended_at"] = ended_at.isoformat()
        node_log_entry["duration_seconds"] = duration
        node_log_entry["error_message"] = error
        node_log_entry["outputs"] = output_data

        # Update execution counters
        if success:
            self.current_session["nodes_executed"] += 1
        else:
            self.current_session["nodes_failed"] += 1

        # Log to node-specific file
        exec_dir = Path(self.current_session["log_directory"])
        log_file = exec_dir / node_log_entry["log_file"]

        if output_data:
            self._log_to_file(
                log_file, "INFO", node_id, f"Output data: {json.dumps(output_data, indent=2)}"
            )

        log_level = "ERROR" if not success else "INFO"
        message = f"Node execution {status} (Duration: {duration:.2f}s)"
        if error:
            message += f" - Error: {error}"

        self._log_to_file(log_file, log_level, node_id, message)

        # Log to summary file
        summary_log = exec_dir / "execution_summary.log"
        self._log_to_file(summary_log, log_level, node_id, message)

        # Log errors to dedicated error log
        if error:
            error_log = exec_dir / "errors.log"
            self._log_to_file(error_log, "ERROR", node_id, f"{node_name}: {error}")

        # Update session metadata
        self._save_session_metadata()

    def log_to_node(self, execution_id: str, node_id: str, level: str, message: str) -> None:
        """
        Write a log message to a specific node's log file.

        Args:
            execution_id: Execution session ID
            node_id: Node identifier
            level: Log level (INFO, DEBUG, WARN, ERROR)
            message: Log message
        """
        if not self.current_session or self.current_session["id"] != execution_id:
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

    def get_session_path(self, execution_id: str) -> str:
        """
        Get the filesystem path for a session's logs.

        Args:
            execution_id: Execution session ID

        Returns:
            Path to log directory
        """
        return str(self.logs_dir / execution_id)

    def _log_to_file(self, file_path: Path, level: str, source: str, message: str) -> None:
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

    def _save_session_metadata(self) -> None:
        """Update the execution metadata file on disk."""
        if not self.current_session:
            return

        exec_dir = Path(self.current_session["log_directory"])
        metadata_file = exec_dir / "execution_metadata.json"

        with open(metadata_file, "w") as f:
            json.dump(self.current_session, f, indent=2)

    def get_execution_history(
        self, limit: Optional[int] = None, status_filter: Optional[str] = None
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
            history = [exec_data for exec_data in history if exec_data["status"] == status_filter]

        # Sort by created_at (most recent first)
        history.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply limit
        if limit:
            history = history[:limit]

        return history
