"""Protocol for workflow execution engines."""

from typing import Protocol
from lighthouse.domain.models.workflow import Workflow
from lighthouse.domain.models.execution import ExecutionSession


class IExecutor(Protocol):
    """
    Protocol for workflow execution engines.

    Defines the contract for executing workflows and managing
    execution sessions. Implementations handle the orchestration
    of node execution, context management, and error handling.
    """

    def execute_workflow(
        self,
        workflow: Workflow,
        triggered_by: str
    ) -> ExecutionSession:
        """
        Execute a workflow from a specific trigger node.

        Args:
            workflow: Workflow to execute
            triggered_by: Node ID that triggered execution

        Returns:
            ExecutionSession with execution results

        Raises:
            WorkflowExecutionError: If execution fails
            CycleDetectedError: If workflow contains cycles
        """
        ...

    def cancel_execution(self, execution_id: str) -> None:
        """
        Cancel a running execution.

        Args:
            execution_id: ID of execution to cancel
        """
        ...

    def get_execution(self, execution_id: str) -> ExecutionSession:
        """
        Get execution session by ID.

        Args:
            execution_id: Session identifier

        Returns:
            ExecutionSession instance

        Raises:
            KeyError: If execution not found
        """
        ...
