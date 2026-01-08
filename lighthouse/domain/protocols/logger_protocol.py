"""Protocol for logging services."""

from typing import Protocol, Dict, Any


class ILogger(Protocol):
    """
    Protocol for logging services.

    Provides abstraction over logging implementations,
    allowing different backends (file, console, remote) without
    changing business logic.
    """

    def create_session(
        self,
        execution_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Create a new logging session for a workflow execution.

        Args:
            execution_id: Unique execution identifier
            metadata: Session metadata (workflow name, trigger, etc.)
        """
        ...

    def log(
        self,
        execution_id: str,
        level: str,
        source: str,
        message: str
    ) -> None:
        """
        Write a log message.

        Args:
            execution_id: Execution session ID
            level: Log level (DEBUG, INFO, WARN, ERROR)
            source: Source identifier (node ID or SYSTEM)
            message: Log message content
        """
        ...

    def log_node_start(
        self,
        execution_id: str,
        node_id: str,
        node_name: str
    ) -> None:
        """
        Log the start of a node execution.

        Args:
            execution_id: Execution session ID
            node_id: Node identifier
            node_name: Node display name
        """
        ...

    def log_node_end(
        self,
        execution_id: str,
        node_id: str,
        node_name: str,
        success: bool,
        duration: float,
        error: str = None
    ) -> None:
        """
        Log the completion of a node execution.

        Args:
            execution_id: Execution session ID
            node_id: Node identifier
            node_name: Node display name
            success: Whether execution succeeded
            duration: Execution duration in seconds
            error: Error message if failed
        """
        ...

    def end_session(
        self,
        execution_id: str,
        status: str,
        duration: float
    ) -> None:
        """
        Finalize a logging session.

        Args:
            execution_id: Execution session ID
            status: Final status (COMPLETED, FAILED, CANCELLED)
            duration: Total session duration in seconds
        """
        ...

    def get_session_path(self, execution_id: str) -> str:
        """
        Get the filesystem path for a session's logs.

        Args:
            execution_id: Execution session ID

        Returns:
            Path to log directory
        """
        ...
