"""Unit tests for ExecuteCommandNode."""

import pytest
from unittest.mock import Mock
from lighthouse.nodes.execution.command_node import ExecuteCommandNode


@pytest.fixture
def command_node():
    """Create an ExecuteCommandNode instance."""
    return ExecuteCommandNode(name="Test Command")


@pytest.fixture
def mock_completed_process():
    """Create a mock successful subprocess result."""
    result = Mock()
    result.returncode = 0
    result.stdout = "Command output"
    result.stderr = ""
    return result


@pytest.fixture
def mock_failed_process():
    """Create a mock failed subprocess result."""
    result = Mock()
    result.returncode = 1
    result.stdout = ""
    result.stderr = "Error message"
    return result


class TestCommandNodeInitialization:
    """Tests for node initialization."""

    def test_node_creation(self, command_node):
        """Test creating command node."""
        assert command_node.name == "Test Command"
        assert command_node.id is not None

    def test_metadata(self, command_node):
        """Test node metadata."""
        metadata = command_node.metadata
        assert metadata.name == "ExecuteCommand"
        assert len(metadata.fields) == 3  # command, timeout, log_output

    def test_default_state(self, command_node):
        """Test default state values."""
        state = command_node.state
        assert "command" in state
        assert state["command"] == "echo 'Hello World'"
        assert state["timeout"] == 60
        assert state["log_output"] is True


class TestCommandExecution:
    """Tests for command execution."""

    def test_successful_command(self, command_node, mock_completed_process, mocker):
        """Test executing successful command."""
        mock_run = mocker.patch('subprocess.run', return_value=mock_completed_process)

        command_node.update_state({
            "command": "echo 'test'",
            "timeout": 10,
        })

        result = command_node.execute({})

        assert result.success is True
        assert result.data["stdout"] == "Command output"
        assert result.data["stderr"] == ""
        assert result.data["exit_code"] == 0
        assert result.data["success"] is True
        mock_run.assert_called_once()

    def test_failed_command(self, command_node, mock_failed_process, mocker):
        """Test executing failed command."""
        mock_run = mocker.patch('subprocess.run', return_value=mock_failed_process)

        command_node.update_state({
            "command": "invalid_command",
            "timeout": 10,
        })

        result = command_node.execute({})

        assert result.success is False
        assert result.data["exit_code"] == 1
        assert result.data["success"] is False
        assert "exited with code 1" in result.error

    def test_command_with_stdout(self, command_node, mocker):
        """Test command with stdout output."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Output line 1\nOutput line 2"
        mock_result.stderr = ""

        mocker.patch('subprocess.run', return_value=mock_result)

        command_node.update_state({"command": "ls -la"})
        result = command_node.execute({})

        assert result.success is True
        assert "Output line 1" in result.data["stdout"]
        assert "Output line 2" in result.data["stdout"]

    def test_command_with_stderr(self, command_node, mocker):
        """Test command with stderr output."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: File not found"

        mocker.patch('subprocess.run', return_value=mock_result)

        command_node.update_state({"command": "cat missing.txt"})
        result = command_node.execute({})

        assert result.success is False
        assert "Error: File not found" in result.data["stderr"]

    def test_command_includes_all_fields(self, command_node, mock_completed_process, mocker):
        """Test that result includes all expected fields."""
        mocker.patch('subprocess.run', return_value=mock_completed_process)

        command_node.update_state({"command": "echo test"})
        result = command_node.execute({})

        assert "stdout" in result.data
        assert "stderr" in result.data
        assert "exit_code" in result.data
        assert "success" in result.data
        assert "command" in result.data


class TestCommandTimeout:
    """Tests for command timeout handling."""

    def test_timeout_error(self, command_node, mocker):
        """Test handling command timeout."""
        import subprocess
        mocker.patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 1))

        command_node.update_state({
            "command": "sleep 100",
            "timeout": 1,
        })

        result = command_node.execute({})

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_custom_timeout(self, command_node, mock_completed_process, mocker):
        """Test custom timeout value."""
        mock_run = mocker.patch('subprocess.run', return_value=mock_completed_process)

        command_node.set_state_value("timeout", 120)
        command_node.set_state_value("command", "echo test")

        command_node.execute({})

        assert mock_run.call_args[1]["timeout"] == 120.0


class TestCommandErrorHandling:
    """Tests for error handling."""

    def test_empty_command_error(self, command_node):
        """Test error with empty command."""
        command_node.update_state({"command": ""})

        result = command_node.execute({})

        assert result.success is False
        assert "cannot be empty" in result.error.lower()

    def test_whitespace_command_error(self, command_node):
        """Test error with whitespace-only command."""
        command_node.update_state({"command": "   "})

        result = command_node.execute({})

        assert result.success is False
        assert "cannot be empty" in result.error.lower()

    def test_file_not_found_error(self, command_node, mocker):
        """Test handling FileNotFoundError."""
        import subprocess
        mocker.patch('subprocess.run', side_effect=FileNotFoundError("command not found"))

        command_node.update_state({"command": "nonexistent_command"})

        result = command_node.execute({})

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_general_exception_handling(self, command_node, mocker):
        """Test handling unexpected exceptions."""
        mocker.patch('subprocess.run', side_effect=RuntimeError("Unexpected error"))

        command_node.update_state({"command": "echo test"})

        result = command_node.execute({})

        assert result.success is False
        assert "execution failed" in result.error.lower()


class TestLogging:
    """Tests for command output logging."""

    def test_logging_enabled(self, command_node, mocker):
        """Test that output is logged when log_output is True."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Test output"
        mock_result.stderr = "Test error"

        mocker.patch('subprocess.run', return_value=mock_result)

        command_node.update_state({
            "command": "echo test",
            "log_output": True,
        })

        result = command_node.execute({})

        assert result.success is True
        assert len(result.logs) > 0
        assert any("STDOUT" in log for log in result.logs)
        assert any("STDERR" in log for log in result.logs)

    def test_logging_disabled(self, command_node, mocker):
        """Test that output is not logged when log_output is False."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Test output"
        mock_result.stderr = ""

        mocker.patch('subprocess.run', return_value=mock_result)

        command_node.update_state({
            "command": "echo test",
            "log_output": False,
        })

        result = command_node.execute({})

        assert result.success is True
        assert len(result.logs) == 0

    def test_output_truncation(self, command_node, mocker):
        """Test that long output is truncated in logs."""
        long_output = "x" * 1000
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = long_output
        mock_result.stderr = ""

        mocker.patch('subprocess.run', return_value=mock_result)

        command_node.update_state({
            "command": "echo test",
            "log_output": True,
        })

        result = command_node.execute({})

        # Logs should be truncated to 500 chars
        for log in result.logs:
            assert len(log) <= 510  # "STDOUT: " prefix + 500 chars


class TestValidation:
    """Tests for configuration validation."""

    def test_validate_valid_config(self, command_node):
        """Test validation with valid configuration."""
        errors = command_node.validate()
        assert errors == []

    def test_validate_empty_command(self, command_node):
        """Test validation catches empty command."""
        command_node.set_state_value("command", "")

        errors = command_node.validate()

        assert len(errors) > 0
        assert any("command" in err.lower() and "empty" in err.lower() for err in errors)

    def test_validate_negative_timeout(self, command_node):
        """Test validation catches negative timeout."""
        command_node.set_state_value("timeout", -10)

        errors = command_node.validate()

        assert len(errors) > 0
        assert any("timeout" in err.lower() for err in errors)

    def test_validate_zero_timeout(self, command_node):
        """Test validation catches zero timeout."""
        command_node.set_state_value("timeout", 0)

        errors = command_node.validate()

        assert len(errors) > 0
        assert any("timeout" in err.lower() for err in errors)

    def test_validate_invalid_timeout_type(self, command_node):
        """Test validation catches non-numeric timeout."""
        command_node.set_state_value("timeout", "not a number")

        errors = command_node.validate()

        assert len(errors) > 0
        assert any("timeout" in err.lower() and "number" in err.lower() for err in errors)


class TestStateManagement:
    """Tests for state management."""

    def test_state_persistence(self, command_node):
        """Test that state persists across updates."""
        command_node.update_state({
            "command": "ls -la",
            "timeout": 30,
        })

        state = command_node.state

        assert state["command"] == "ls -la"
        assert state["timeout"] == 30
        assert state["log_output"] is True  # Default unchanged

    def test_timeout_conversion(self, command_node, mock_completed_process, mocker):
        """Test that timeout is converted to float."""
        mock_run = mocker.patch('subprocess.run', return_value=mock_completed_process)

        command_node.set_state_value("timeout", "45")
        command_node.set_state_value("command", "echo test")

        command_node.execute({})

        assert mock_run.call_args[1]["timeout"] == 45.0

    def test_invalid_timeout_defaults_to_60(self, command_node, mock_completed_process, mocker):
        """Test that invalid timeout defaults to 60 seconds."""
        mock_run = mocker.patch('subprocess.run', return_value=mock_completed_process)

        command_node.set_state_value("timeout", "invalid")
        command_node.set_state_value("command", "echo test")

        command_node.execute({})

        assert mock_run.call_args[1]["timeout"] == 60.0


class TestExecutionResult:
    """Tests for execution result properties."""

    def test_result_has_duration(self, command_node, mock_completed_process, mocker):
        """Test that result includes execution duration."""
        mocker.patch('subprocess.run', return_value=mock_completed_process)

        command_node.update_state({"command": "echo test"})
        result = command_node.execute({})

        assert result.duration_seconds >= 0

    def test_successful_result_structure(self, command_node, mock_completed_process, mocker):
        """Test structure of successful result."""
        mocker.patch('subprocess.run', return_value=mock_completed_process)

        command_node.update_state({"command": "echo test"})
        result = command_node.execute({})

        assert result.success is True
        assert result.error is None
        assert isinstance(result.data, dict)
        assert result.data["exit_code"] == 0

    def test_failed_result_structure(self, command_node, mock_failed_process, mocker):
        """Test structure of failed result."""
        mocker.patch('subprocess.run', return_value=mock_failed_process)

        command_node.update_state({"command": "false"})
        result = command_node.execute({})

        assert result.success is False
        assert result.error is not None
        assert isinstance(result.data, dict)
        assert result.data["exit_code"] == 1
