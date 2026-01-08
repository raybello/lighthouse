"""Unit tests for CalculatorNode."""

import pytest
from lighthouse.nodes.execution.calculator_node import CalculatorNode, OperationType
from lighthouse.domain.models.node import NodeType


@pytest.fixture
def calculator_node():
    """Create a CalculatorNode instance."""
    return CalculatorNode(name="Test Calculator")


class TestCalculatorNodeInitialization:
    """Tests for node initialization."""

    def test_node_creation(self, calculator_node):
        """Test creating a calculator node."""
        assert calculator_node.name == "Test Calculator"
        assert calculator_node.id is not None
        assert len(calculator_node.id) == 8  # UUID suffix

    def test_metadata(self, calculator_node):
        """Test node metadata."""
        metadata = calculator_node.metadata
        assert metadata.name == "Calculator"
        assert metadata.node_type == NodeType.EXECUTION
        assert metadata.has_inputs is True
        assert metadata.has_config is True
        assert len(metadata.fields) == 3  # field_a, field_b, operation

    def test_default_state(self, calculator_node):
        """Test default state values."""
        state = calculator_node.state
        assert state["field_a"] == "10"
        assert state["field_b"] == "5"
        assert state["operation"] == "+"


class TestArithmeticOperations:
    """Tests for arithmetic calculations."""

    def test_addition(self, calculator_node):
        """Test addition operation."""
        calculator_node.update_state({
            "field_a": "10",
            "field_b": "5",
            "operation": "+"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == 15.0
        assert result.error is None

    def test_subtraction(self, calculator_node):
        """Test subtraction operation."""
        calculator_node.update_state({
            "field_a": "10",
            "field_b": "3",
            "operation": "-"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == 7.0

    def test_multiplication(self, calculator_node):
        """Test multiplication operation."""
        calculator_node.update_state({
            "field_a": "6",
            "field_b": "7",
            "operation": "*"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == 42.0

    def test_division(self, calculator_node):
        """Test division operation."""
        calculator_node.update_state({
            "field_a": "20",
            "field_b": "4",
            "operation": "/"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == 5.0

    def test_modulo(self, calculator_node):
        """Test modulo operation."""
        calculator_node.update_state({
            "field_a": "17",
            "field_b": "5",
            "operation": "%"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == 2.0


class TestNumberConversion:
    """Tests for number type conversions."""

    def test_integer_strings(self, calculator_node):
        """Test with integer string inputs."""
        calculator_node.update_state({
            "field_a": "100",
            "field_b": "25",
            "operation": "+"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == 125.0

    def test_float_strings(self, calculator_node):
        """Test with float string inputs."""
        calculator_node.update_state({
            "field_a": "10.5",
            "field_b": "2.3",
            "operation": "+"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert abs(result.data["result"] - 12.8) < 0.001  # Float precision

    def test_mixed_integer_and_float(self, calculator_node):
        """Test with mixed int and float inputs."""
        calculator_node.update_state({
            "field_a": "10",
            "field_b": "2.5",
            "operation": "*"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == 25.0

    def test_numeric_types(self, calculator_node):
        """Test with actual numeric types (not strings)."""
        calculator_node.update_state({
            "field_a": 15,
            "field_b": 3,
            "operation": "/"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == 5.0

    def test_negative_numbers(self, calculator_node):
        """Test with negative numbers."""
        calculator_node.update_state({
            "field_a": "-10",
            "field_b": "5",
            "operation": "+"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == -5.0


class TestErrorHandling:
    """Tests for error conditions."""

    def test_division_by_zero(self, calculator_node):
        """Test division by zero error."""
        calculator_node.update_state({
            "field_a": "10",
            "field_b": "0",
            "operation": "/"
        })

        result = calculator_node.execute({})

        assert result.success is False
        assert "division by zero" in result.error.lower()
        assert result.data == {}

    def test_modulo_by_zero(self, calculator_node):
        """Test modulo by zero error."""
        calculator_node.update_state({
            "field_a": "10",
            "field_b": "0",
            "operation": "%"
        })

        result = calculator_node.execute({})

        assert result.success is False
        assert "zero" in result.error.lower()  # Catches both "division" and "modulo" by zero

    def test_invalid_number_format(self, calculator_node):
        """Test with invalid number format."""
        calculator_node.update_state({
            "field_a": "not_a_number",
            "field_b": "5",
            "operation": "+"
        })

        result = calculator_node.execute({})

        assert result.success is False
        assert "invalid number format" in result.error.lower()

    def test_empty_field(self, calculator_node):
        """Test with empty field."""
        calculator_node.update_state({
            "field_a": "",
            "field_b": "5",
            "operation": "+"
        })

        result = calculator_node.execute({})

        assert result.success is False

    def test_unknown_operation(self, calculator_node):
        """Test with unknown operation."""
        calculator_node.update_state({
            "field_a": "10",
            "field_b": "5",
            "operation": "^"  # Unknown operation
        })

        result = calculator_node.execute({})

        assert result.success is False
        assert "unknown operation" in result.error.lower()


class TestStateManagement:
    """Tests for state management."""

    def test_get_state_value(self, calculator_node):
        """Test getting state values."""
        assert calculator_node.get_state_value("field_a") == "10"
        assert calculator_node.get_state_value("nonexistent", "default") == "default"

    def test_set_state_value(self, calculator_node):
        """Test setting state values."""
        calculator_node.set_state_value("field_a", "99")

        assert calculator_node.get_state_value("field_a") == "99"

    def test_update_state(self, calculator_node):
        """Test updating state."""
        calculator_node.update_state({
            "field_a": "20",
            "operation": "*"
        })

        state = calculator_node.state
        assert state["field_a"] == "20"
        assert state["operation"] == "*"
        assert state["field_b"] == "5"  # Unchanged

    def test_reset(self, calculator_node):
        """Test resetting node state."""
        calculator_node.update_state({
            "field_a": "999",
            "field_b": "888",
            "operation": "*"
        })

        calculator_node.reset()

        state = calculator_node.state
        assert state["field_a"] == "10"  # Back to default
        assert state["field_b"] == "5"   # Back to default
        assert state["operation"] == "+" # Back to default


class TestValidation:
    """Tests for node validation."""

    def test_validate_valid_state(self, calculator_node):
        """Test validation with valid state."""
        errors = calculator_node.validate()

        assert errors == []

    def test_validate_with_custom_state(self, calculator_node):
        """Test validation with custom state."""
        calculator_node.update_state({
            "field_a": "100",
            "field_b": "50",
            "operation": "*"
        })

        errors = calculator_node.validate()

        assert errors == []


class TestExecutionResult:
    """Tests for execution result properties."""

    def test_result_contains_duration(self, calculator_node):
        """Test that result contains execution duration."""
        result = calculator_node.execute({})

        assert result.duration_seconds > 0

    def test_successful_result_structure(self, calculator_node):
        """Test successful result structure."""
        result = calculator_node.execute({})

        assert result.success is True
        assert "result" in result.data
        assert isinstance(result.data["result"], (int, float))
        assert result.error is None

    def test_error_result_structure(self, calculator_node):
        """Test error result structure."""
        calculator_node.update_state({
            "field_a": "invalid",
            "field_b": "5",
            "operation": "+"
        })

        result = calculator_node.execute({})

        assert result.success is False
        assert result.data == {}
        assert result.error is not None
        assert isinstance(result.error, str)


class TestComplexScenarios:
    """Tests for complex calculation scenarios."""

    def test_large_numbers(self, calculator_node):
        """Test with large numbers."""
        calculator_node.update_state({
            "field_a": "999999999",
            "field_b": "1000000000",
            "operation": "+"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert result.data["result"] == 1999999999.0

    def test_very_small_division(self, calculator_node):
        """Test division resulting in very small number."""
        calculator_node.update_state({
            "field_a": "1",
            "field_b": "1000000",
            "operation": "/"
        })

        result = calculator_node.execute({})

        assert result.success is True
        assert abs(result.data["result"] - 0.000001) < 0.0000001

    def test_decimal_precision(self, calculator_node):
        """Test decimal precision in results."""
        calculator_node.update_state({
            "field_a": "0.1",
            "field_b": "0.2",
            "operation": "+"
        })

        result = calculator_node.execute({})

        assert result.success is True
        # Account for floating point precision
        assert abs(result.data["result"] - 0.3) < 0.0001
