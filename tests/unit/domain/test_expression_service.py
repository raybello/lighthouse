"""Unit tests for ExpressionService."""

import pytest
from lighthouse.domain.services.expression_service import ExpressionService
from lighthouse.domain.exceptions import ExpressionError


@pytest.fixture
def expression_service():
    """Create an ExpressionService instance."""
    return ExpressionService()


@pytest.fixture
def sample_context():
    """Create a sample execution context for testing."""
    return {
        "Input": {
            "data": {
                "name": "John Doe",
                "age": 30,
                "email": "john@example.com",
                "active": True,
            }
        },
        "Calculator": {"data": {"result": 42, "numbers": [1, 2, 3, 4, 5]}},
        "Form": {
            "data": {
                "user": {"first_name": "Jane", "last_name": "Smith"},
                "score": 95.5,
            }
        },
    }


class TestExpressionDetection:
    """Tests for expression detection."""

    def test_has_expression_detects_simple_expression(
        self, expression_service
    ):
        """Test detecting simple {{}} expressions."""
        assert expression_service.has_expression("{{foo}}")
        assert expression_service.has_expression("Hello {{world}}")
        assert expression_service.has_expression("{{a}} and {{b}}")

    def test_has_expression_returns_false_for_plain_text(
        self, expression_service
    ):
        """Test that plain text without expressions returns False."""
        assert not expression_service.has_expression("plain text")
        assert not expression_service.has_expression("no expressions here")
        assert not expression_service.has_expression("")

    def test_has_expression_with_non_string(self, expression_service):
        """Test has_expression with non-string inputs."""
        assert not expression_service.has_expression(123)
        assert not expression_service.has_expression(None)
        assert not expression_service.has_expression([])


class TestExpressionExtraction:
    """Tests for extracting expressions from strings."""

    def test_extract_single_expression(self, expression_service):
        """Test extracting a single expression."""
        expressions = expression_service.extract_expressions("{{foo}}")
        assert len(expressions) == 1
        assert expressions[0] == "foo"

    def test_extract_multiple_expressions(self, expression_service):
        """Test extracting multiple expressions."""
        expressions = expression_service.extract_expressions(
            "{{first}} and {{second}}"
        )
        assert len(expressions) == 2
        assert "first" in expressions
        assert "second" in expressions

    def test_extract_expressions_from_plain_text(self, expression_service):
        """Test extracting from text with no expressions."""
        expressions = expression_service.extract_expressions("no expressions")
        assert len(expressions) == 0

    def test_extract_complex_expressions(self, expression_service):
        """Test extracting complex expressions."""
        text = 'Hello {{$node["Input"].data.name}}, your age is {{$node["Input"].data.age}}'
        expressions = expression_service.extract_expressions(text)
        assert len(expressions) == 2


class TestNodeReferences:
    """Tests for node reference evaluation."""

    def test_simple_node_reference(
        self, expression_service, sample_context
    ):
        """Test resolving a simple node reference."""
        result = expression_service.resolve(
            '{{$node["Input"].data.name}}', sample_context
        )
        assert result == "John Doe"

    def test_numeric_property_reference(
        self, expression_service, sample_context
    ):
        """Test resolving numeric property."""
        result = expression_service.resolve(
            '{{$node["Input"].data.age}}', sample_context
        )
        assert result == 30

    def test_boolean_property_reference(
        self, expression_service, sample_context
    ):
        """Test resolving boolean property."""
        result = expression_service.resolve(
            '{{$node["Input"].data.active}}', sample_context
        )
        assert result is True

    def test_nested_property_reference(
        self, expression_service, sample_context
    ):
        """Test resolving nested object properties."""
        result = expression_service.resolve(
            '{{$node["Form"].data.user.first_name}}', sample_context
        )
        assert result == "Jane"


class TestArithmetic:
    """Tests for arithmetic operations."""

    def test_addition(self, expression_service, sample_context):
        """Test arithmetic addition."""
        result = expression_service.resolve(
            '{{$node["Input"].data.age + 10}}', sample_context
        )
        assert result == 40

    def test_subtraction(self, expression_service, sample_context):
        """Test arithmetic subtraction."""
        result = expression_service.resolve(
            '{{$node["Input"].data.age - 5}}', sample_context
        )
        assert result == 25

    def test_multiplication(self, expression_service, sample_context):
        """Test arithmetic multiplication."""
        result = expression_service.resolve(
            '{{$node["Calculator"].data.result * 2}}', sample_context
        )
        assert result == 84

    def test_division(self, expression_service, sample_context):
        """Test arithmetic division."""
        result = expression_service.resolve(
            '{{$node["Calculator"].data.result / 2}}', sample_context
        )
        assert result == 21.0

    def test_complex_arithmetic(self, expression_service, sample_context):
        """Test complex arithmetic expression."""
        result = expression_service.resolve(
            '{{($node["Input"].data.age * 2) + $node["Calculator"].data.result}}',
            sample_context,
        )
        assert result == 102  # (30 * 2) + 42


class TestStringOperations:
    """Tests for string operations."""

    def test_string_concatenation_in_mixed_content(
        self, expression_service, sample_context
    ):
        """Test string substitution in mixed content."""
        result = expression_service.resolve(
            'Hello {{$node["Input"].data.name}}, welcome!', sample_context
        )
        assert result == "Hello John Doe, welcome!"

    def test_multiple_substitutions(
        self, expression_service, sample_context
    ):
        """Test multiple expression substitutions."""
        result = expression_service.resolve(
            '{{$node["Input"].data.name}} is {{$node["Input"].data.age}} years old',
            sample_context,
        )
        assert result == "John Doe is 30 years old"

    def test_numeric_to_string_conversion(
        self, expression_service, sample_context
    ):
        """Test that numbers are converted to strings in mixed content."""
        result = expression_service.resolve(
            'Result: {{$node["Calculator"].data.result}}', sample_context
        )
        assert result == "Result: 42"


class TestDictResolution:
    """Tests for resolving expressions in dictionaries."""

    def test_resolve_dict_with_expressions(
        self, expression_service, sample_context
    ):
        """Test resolving a dictionary with expressions."""
        data = {
            "greeting": 'Hello {{$node["Input"].data.name}}',
            "age_next_year": '{{$node["Input"].data.age + 1}}',
            "plain": "no expression",
        }

        result = expression_service.resolve_dict(data, sample_context)

        assert result["greeting"] == "Hello John Doe"
        assert result["age_next_year"] == 31
        assert result["plain"] == "no expression"

    def test_resolve_nested_dict(self, expression_service, sample_context):
        """Test resolving nested dictionaries."""
        data = {
            "user": {
                "name": '{{$node["Input"].data.name}}',
                "email": '{{$node["Input"].data.email}}',
            },
            "metadata": {"timestamp": "2024-01-01"},
        }

        result = expression_service.resolve_dict(data, sample_context)

        assert result["user"]["name"] == "John Doe"
        assert result["user"]["email"] == "john@example.com"
        assert result["metadata"]["timestamp"] == "2024-01-01"

    def test_resolve_dict_with_list(
        self, expression_service, sample_context
    ):
        """Test resolving dictionary containing lists."""
        data = {
            "values": [
                '{{$node["Input"].data.age}}',
                '{{$node["Calculator"].data.result}}',
                "plain",
            ]
        }

        result = expression_service.resolve_dict(data, sample_context)

        assert result["values"][0] == 30
        assert result["values"][1] == 42
        assert result["values"][2] == "plain"


class TestErrorHandling:
    """Tests for error handling."""

    def test_nonexistent_node_reference(
        self, expression_service, sample_context
    ):
        """Test that referencing non-existent node raises error."""
        with pytest.raises(ExpressionError, match="not found in context"):
            expression_service.evaluate_expression(
                '$node["NonExistent"].data.foo', sample_context
            )

    def test_invalid_expression_syntax(
        self, expression_service, sample_context
    ):
        """Test that invalid syntax raises error."""
        with pytest.raises(ExpressionError):
            expression_service.evaluate_expression(
                "$node[invalid syntax", sample_context
            )

    def test_failed_expression_returns_original_in_resolve(
        self, expression_service, sample_context
    ):
        """Test that failed expressions in resolve() return original value."""
        result = expression_service.resolve(
            '{{$node["NonExistent"].data.foo}}', sample_context
        )
        # Should return original string when evaluation fails
        assert result == '{{$node["NonExistent"].data.foo}}'


class TestEdgeCases:
    """Tests for edge cases."""

    def test_resolve_non_string_value(
        self, expression_service, sample_context
    ):
        """Test that non-string values are returned as-is."""
        assert expression_service.resolve(123, sample_context) == 123
        assert expression_service.resolve(None, sample_context) is None
        assert expression_service.resolve([], sample_context) == []

    def test_resolve_string_without_expressions(
        self, expression_service, sample_context
    ):
        """Test that strings without expressions are returned as-is."""
        plain_text = "no expressions here"
        result = expression_service.resolve(plain_text, sample_context)
        assert result == plain_text

    def test_resolve_empty_string(self, expression_service, sample_context):
        """Test resolving empty string."""
        result = expression_service.resolve("", sample_context)
        assert result == ""

    def test_resolve_with_empty_context(self, expression_service):
        """Test resolving with empty context."""
        result = expression_service.resolve("plain text", {})
        assert result == "plain text"


class TestComparisonOperations:
    """Tests for comparison operations."""

    def test_greater_than(self, expression_service, sample_context):
        """Test greater than comparison."""
        result = expression_service.resolve(
            '{{$node["Input"].data.age > 25}}', sample_context
        )
        assert result is True

    def test_less_than(self, expression_service, sample_context):
        """Test less than comparison."""
        result = expression_service.resolve(
            '{{$node["Input"].data.age < 25}}', sample_context
        )
        assert result is False

    def test_equality(self, expression_service, sample_context):
        """Test equality comparison."""
        result = expression_service.resolve(
            '{{$node["Input"].data.age == 30}}', sample_context
        )
        assert result is True
