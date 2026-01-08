"""
Execute Command node for running shell commands.

Pure business logic with NO UI dependencies.
"""

import subprocess
import time
from typing import Any, Dict

from lighthouse.domain.models.field_types import FieldDefinition, FieldType
from lighthouse.domain.models.node import ExecutionResult, NodeMetadata, NodeType
from lighthouse.nodes.base.base_node import ExecutionNode


class ExecuteCommandNode(ExecutionNode):
    """
    Node for executing shell commands.

    Executes system commands and captures stdout, stderr, and exit code.
    Useful for automation tasks and system integrations.

    State Fields:
        command: Shell command to execute
        timeout: Command timeout in seconds
        log_output: Whether to include output in result logs
    """

    @property
    def metadata(self) -> NodeMetadata:
        """Get execute command node metadata."""
        return NodeMetadata(
            node_type=NodeType.EXECUTION,
            name="ExecuteCommand",
            description="Executes shell commands and captures output",
            version="1.0.0",
            fields=[
                FieldDefinition(
                    name="command",
                    label="Command",
                    field_type=FieldType.STRING,
                    default_value="echo 'Hello World'",
                    required=True,
                    description="Shell command to execute",
                ),
                FieldDefinition(
                    name="timeout",
                    label="Timeout (seconds)",
                    field_type=FieldType.NUMBER,
                    default_value=60,
                    required=True,
                    description="Command timeout in seconds",
                ),
                FieldDefinition(
                    name="log_output",
                    label="Log Output",
                    field_type=FieldType.BOOLEAN,
                    default_value=True,
                    required=False,
                    description="Whether to include command output in logs",
                ),
            ],
            has_inputs=True,
            has_config=True,
            category="System",
        )

    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the shell command.

        Args:
            context: Execution context (not used directly)

        Returns:
            ExecutionResult with stdout, stderr, exit_code, and success status
        """
        start_time = time.time()

        try:
            command = self.get_state_value("command", "")
            timeout = self.get_state_value("timeout", 60)
            log_output = self.get_state_value("log_output", True)

            if not command or not command.strip():
                return ExecutionResult.error_result(
                    error="Command cannot be empty",
                    duration=time.time() - start_time,
                )

            # Convert timeout to float
            try:
                timeout_seconds = float(timeout)
            except (ValueError, TypeError):
                timeout_seconds = 60.0

            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode
            success = exit_code == 0

            duration = time.time() - start_time

            # Prepare result data
            data = {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "success": success,
                "command": command,
            }

            # Add logs if enabled
            logs = []
            if log_output:
                if stdout:
                    logs.append(f"STDOUT: {stdout[:500]}")  # Truncate long output
                if stderr:
                    logs.append(f"STDERR: {stderr[:500]}")

            # Return error result if command failed
            if not success:
                return ExecutionResult(
                    success=False,
                    data=data,
                    error=f"Command exited with code {exit_code}",
                    duration_seconds=duration,
                    logs=logs,
                )

            return ExecutionResult(
                success=True,
                data=data,
                duration_seconds=duration,
                logs=logs,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Command timed out after {timeout_seconds}s",
                duration=duration,
            )

        except FileNotFoundError as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Command not found: {str(e)}",
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Command execution failed: {str(e)}",
                duration=duration,
            )

    def validate(self) -> list[str]:
        """
        Validate command configuration.

        Returns:
            List of validation errors
        """
        errors = super().validate()

        command = self.get_state_value("command", "")
        if not command or not command.strip():
            errors.append("Command cannot be empty")

        timeout = self.get_state_value("timeout", 60)
        try:
            timeout_num = float(timeout)
            if timeout_num <= 0:
                errors.append("Timeout must be greater than 0")
        except (ValueError, TypeError):
            errors.append("Timeout must be a number")

        return errors
