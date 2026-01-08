"""
Calculator node for arithmetic operations.

Pure business logic with NO UI dependencies.
"""

from enum import Enum
from typing import Any, Dict

from lighthouse.domain.models.field_types import FieldDefinition, FieldType
from lighthouse.domain.models.node import ExecutionResult, NodeMetadata, NodeType
from lighthouse.nodes.base.base_node import ExecutionNode


class OperationType(Enum):
    """Supported arithmetic operations."""

    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"


class CalculatorNode(ExecutionNode):
    """
    Node for performing arithmetic calculations.

    Supports dynamic input via expressions and performs basic
    arithmetic operations: +, -, *, /, %

    State Fields:
        field_a: First operand (string, supports expressions)
        field_b: Second operand (string, supports expressions)
        operation: Arithmetic operation to perform
    """

    @property
    def metadata(self) -> NodeMetadata:
        """Get calculator node metadata."""
        return NodeMetadata(
            node_type=NodeType.EXECUTION,
            name="Calculator",
            description="Performs arithmetic calculations with expression support",
            version="1.0.0",
            fields=[
                FieldDefinition(
                    name="field_a",
                    label="Field A",
                    field_type=FieldType.STRING,
                    default_value="10",
                    required=True,
                    description="First operand (supports expressions)",
                ),
                FieldDefinition(
                    name="field_b",
                    label="Field B",
                    field_type=FieldType.STRING,
                    default_value="5",
                    required=True,
                    description="Second operand (supports expressions)",
                ),
                FieldDefinition(
                    name="operation",
                    label="Operation",
                    field_type=FieldType.ENUM,
                    default_value=OperationType.ADD.value,
                    required=True,
                    enum_options=[op.value for op in OperationType],
                    description="Arithmetic operation to perform",
                ),
            ],
            has_inputs=True,
            has_config=True,
            category="Math",
        )

    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the calculation.

        Note: Expression resolution is handled BEFORE this method is called.
        The state values should already be resolved to actual values.

        Args:
            context: Execution context (not used directly in this node)

        Returns:
            ExecutionResult with calculation result
        """
        import time

        start_time = time.time()

        try:
            # Get the values (should be resolved from expressions already)
            field_a_raw = self.get_state_value("field_a", "0")
            field_b_raw = self.get_state_value("field_b", "0")
            operation = self.get_state_value("operation", "+")

            # Convert to numbers
            field_a = self._to_number(field_a_raw)
            field_b = self._to_number(field_b_raw)

            # Perform the calculation
            result = self._calculate(field_a, field_b, operation)

            duration = time.time() - start_time

            return ExecutionResult.success_result(
                data={"result": result},
                duration=duration,
            )

        except ValueError as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Invalid number format: {str(e)}",
                duration=duration,
            )
        except ZeroDivisionError:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error="Division by zero",
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Calculation error: {str(e)}",
                duration=duration,
            )

    def _to_number(self, value: Any) -> float:
        """
        Convert value to number.

        Args:
            value: Value to convert (string, int, or float)

        Returns:
            Numeric value

        Raises:
            ValueError: If value cannot be converted to number
        """
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            # Try float first (handles both int and float strings)
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to number")

        raise ValueError(f"Invalid type for number conversion: {type(value)}")

    def _calculate(self, a: float, b: float, operation: str) -> float:
        """
        Perform arithmetic calculation.

        Args:
            a: First operand
            b: Second operand
            operation: Operation symbol (+, -, *, /, %)

        Returns:
            Calculation result

        Raises:
            ZeroDivisionError: If dividing by zero
            ValueError: If operation is unknown
        """
        if operation == "+":
            return a + b
        elif operation == "-":
            return a - b
        elif operation == "*":
            return a * b
        elif operation == "/":
            if b == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            return a / b
        elif operation == "%":
            if b == 0:
                raise ZeroDivisionError("Cannot modulo by zero")
            return a % b
        else:
            raise ValueError(f"Unknown operation: {operation}")
