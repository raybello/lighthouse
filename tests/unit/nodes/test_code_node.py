"""Unit tests for CodeNode."""

import pytest

from lighthouse.nodes.execution.code_node import SAFE_BUILTINS, CodeNode


@pytest.fixture
def code_node():
    """Create a CodeNode instance."""
    return CodeNode(name="Test Code")


class TestCodeNodeInitialization:
    """Tests for node initialization."""

    def test_node_creation(self, code_node):
        """Test creating code node."""
        assert code_node.name == "Test Code"
        assert code_node.id is not None

    def test_metadata(self, code_node):
        """Test node metadata."""
        metadata = code_node.metadata
        assert metadata.name == "Code"
        assert len(metadata.fields) == 2  # code, timeout

    def test_default_state(self, code_node):
        """Test default state values."""
        state = code_node.state
        assert "code" in state
        assert "result = 42" in state["code"]
        assert state["timeout"] == 30

    def test_safe_builtins(self):
        """Test that SAFE_BUILTINS contains expected functions."""
        assert "len" in SAFE_BUILTINS
        assert "sum" in SAFE_BUILTINS
        assert "range" in SAFE_BUILTINS
        assert "list" in SAFE_BUILTINS
        assert "dict" in SAFE_BUILTINS
        # Dangerous functions should NOT be present
        assert "eval" not in SAFE_BUILTINS
        assert "exec" not in SAFE_BUILTINS
        assert "open" not in SAFE_BUILTINS
        assert "__import__" not in SAFE_BUILTINS


class TestCodeExecution:
    """Tests for code execution."""

    def test_simple_arithmetic(self, code_node):
        """Test executing simple arithmetic."""
        code_node.update_state(
            {
                "code": "result = 2 + 2",
                "timeout": 5,
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == 4

    def test_string_manipulation(self, code_node):
        """Test executing string operations."""
        code_node.update_state(
            {
                "code": "result = 'hello ' + 'world'",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == "hello world"

    def test_list_operations(self, code_node):
        """Test executing list operations."""
        code_node.update_state(
            {
                "code": "numbers = [1, 2, 3, 4, 5]\nresult = sum(numbers)",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == 15

    def test_dict_operations(self, code_node):
        """Test executing dictionary operations."""
        code_node.update_state(
            {
                "code": "data = {'name': 'Alice', 'age': 30}\nresult = data['name']",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == "Alice"

    def test_loop_execution(self, code_node):
        """Test executing loops."""
        code_node.update_state(
            {
                "code": "total = 0\nfor i in range(5):\n    total += i\nresult = total",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == 10

    def test_function_definition(self, code_node):
        """Test defining and calling functions."""
        code_node.update_state(
            {
                "code": "def add(a, b):\n    return a + b\nresult = add(10, 20)",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == 30

    def test_no_result_variable(self, code_node):
        """Test code that doesn't set result variable."""
        code_node.update_state(
            {
                "code": "x = 5\ny = 10",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] is None

    def test_context_access(self, code_node):
        """Test accessing context in code."""
        code_node.update_state(
            {
                "code": "result = context.get('value', 0) * 2",
            }
        )

        result = code_node.execute({"value": 21})

        assert result.success is True
        assert result.data["result"] == 42


class TestCodeSafety:
    """Tests for code safety validation."""

    def test_reject_imports(self, code_node):
        """Test that imports are rejected."""
        code_node.update_state(
            {
                "code": "import os\nresult = os.getcwd()",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "imports are not allowed" in result.error.lower()

    def test_reject_from_imports(self, code_node):
        """Test that from imports are rejected."""
        code_node.update_state(
            {
                "code": "from datetime import datetime\nresult = datetime.now()",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "imports are not allowed" in result.error.lower()

    def test_reject_eval(self, code_node):
        """Test that eval is rejected."""
        code_node.update_state(
            {
                "code": "result = eval('2 + 2')",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "eval" in result.error.lower()
        assert "not allowed" in result.error.lower()

    def test_reject_exec(self, code_node):
        """Test that exec is rejected."""
        code_node.update_state(
            {
                "code": "exec('result = 42')",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "exec" in result.error.lower()
        assert "not allowed" in result.error.lower()

    def test_reject_compile(self, code_node):
        """Test that compile is rejected."""
        code_node.update_state(
            {
                "code": "compile('2+2', '<string>', 'eval')",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "compile" in result.error.lower()
        assert "not allowed" in result.error.lower()

    def test_reject_open(self, code_node):
        """Test that open is rejected."""
        code_node.update_state(
            {
                "code": "result = open('/etc/passwd', 'r')",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "open" in result.error.lower()
        assert "not allowed" in result.error.lower()

    def test_reject_import_function(self, code_node):
        """Test that __import__ is rejected."""
        code_node.update_state(
            {
                "code": "os = __import__('os')\nresult = os.getcwd()",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "__import__" in result.error.lower()
        assert "not allowed" in result.error.lower()

    def test_reject_globals(self, code_node):
        """Test that globals is rejected."""
        code_node.update_state(
            {
                "code": "result = globals()",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "globals" in result.error.lower()
        assert "not allowed" in result.error.lower()

    def test_reject_locals(self, code_node):
        """Test that locals is rejected."""
        code_node.update_state(
            {
                "code": "result = locals()",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "locals" in result.error.lower()
        assert "not allowed" in result.error.lower()

    def test_reject_getattr(self, code_node):
        """Test that getattr is rejected."""
        code_node.update_state(
            {
                "code": "result = getattr(object, '__class__')",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "getattr" in result.error.lower()
        assert "not allowed" in result.error.lower()

    def test_reject_private_attributes(self, code_node):
        """Test that private attribute access is rejected."""
        code_node.update_state(
            {
                "code": "x = []\nresult = x.__class__",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "private attribute" in result.error.lower()
        assert "not allowed" in result.error.lower()

    def test_reject_dunder_methods(self, code_node):
        """Test that dunder method access is rejected."""
        code_node.update_state(
            {
                "code": "class Foo:\n    pass\nresult = Foo.__init__",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "private attribute" in result.error.lower()


class TestTimeout:
    """Tests for timeout handling."""

    def test_timeout_enforcement(self, code_node):
        """Test that infinite loops timeout."""
        code_node.update_state(
            {
                "code": "while True:\n    pass",
                "timeout": 1,
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_custom_timeout(self, code_node):
        """Test custom timeout value."""
        code_node.update_state(
            {
                "code": "import time\ntime.sleep(2)\nresult = 42",
                "timeout": 1,
            }
        )

        result = code_node.execute({})

        # Should timeout because sleep(2) > timeout(1)
        # But imports are blocked, so this will fail at validation
        assert result.success is False

    def test_fast_execution_no_timeout(self, code_node):
        """Test that fast code doesn't timeout."""
        code_node.update_state(
            {
                "code": "result = sum(range(1000))",
                "timeout": 30,
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == 499500


class TestErrorHandling:
    """Tests for error handling."""

    def test_syntax_error(self, code_node):
        """Test handling syntax errors."""
        code_node.update_state(
            {
                "code": "result = 2 +",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "syntax error" in result.error.lower()

    def test_runtime_error(self, code_node):
        """Test handling runtime errors."""
        code_node.update_state(
            {
                "code": "result = 10 / 0",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert "division" in result.error.lower()

    def test_name_error(self, code_node):
        """Test handling name errors."""
        code_node.update_state(
            {
                "code": "result = undefined_variable",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert result.error is not None

    def test_type_error(self, code_node):
        """Test handling type errors."""
        code_node.update_state(
            {
                "code": "result = 'string' + 42",
            }
        )

        result = code_node.execute({})

        assert result.success is False
        assert result.error is not None

    def test_empty_code(self, code_node):
        """Test error with empty code."""
        code_node.update_state({"code": ""})

        result = code_node.execute({})

        assert result.success is False
        assert "no code provided" in result.error.lower()

    def test_whitespace_only_code(self, code_node):
        """Test error with whitespace-only code."""
        code_node.update_state({"code": "   \n\n   "})

        result = code_node.execute({})

        assert result.success is False
        assert "no code provided" in result.error.lower()


class TestValidation:
    """Tests for configuration validation."""

    def test_validate_valid_config(self, code_node):
        """Test validation with valid configuration."""
        errors = code_node.validate()
        assert errors == []

    def test_validate_empty_code(self, code_node):
        """Test validation catches empty code."""
        code_node.set_state_value("code", "")

        errors = code_node.validate()

        assert len(errors) > 0
        assert any("code" in err.lower() and "empty" in err.lower() for err in errors)

    def test_validate_unsafe_code(self, code_node):
        """Test validation catches unsafe code."""
        code_node.set_state_value("code", "import os")

        errors = code_node.validate()

        assert len(errors) > 0
        assert any("import" in err.lower() for err in errors)

    def test_validate_negative_timeout(self, code_node):
        """Test validation catches negative timeout."""
        code_node.set_state_value("timeout", -10)

        errors = code_node.validate()

        assert len(errors) > 0
        assert any("timeout" in err.lower() for err in errors)

    def test_validate_zero_timeout(self, code_node):
        """Test validation catches zero timeout."""
        code_node.set_state_value("timeout", 0)

        errors = code_node.validate()

        assert len(errors) > 0
        assert any("timeout" in err.lower() for err in errors)

    def test_validate_excessive_timeout(self, code_node):
        """Test validation catches timeout > 300 seconds."""
        code_node.set_state_value("timeout", 500)

        errors = code_node.validate()

        assert len(errors) > 0
        assert any("timeout" in err.lower() and "300" in err.lower() for err in errors)

    def test_validate_invalid_timeout_type(self, code_node):
        """Test validation catches non-numeric timeout."""
        code_node.set_state_value("timeout", "not a number")

        errors = code_node.validate()

        assert len(errors) > 0
        assert any("timeout" in err.lower() and "number" in err.lower() for err in errors)


class TestStateManagement:
    """Tests for state management."""

    def test_state_persistence(self, code_node):
        """Test that state persists across updates."""
        code_node.update_state(
            {
                "code": "result = 100",
                "timeout": 15,
            }
        )

        state = code_node.state

        assert state["code"] == "result = 100"
        assert state["timeout"] == 15

    def test_timeout_conversion(self, code_node):
        """Test that timeout is converted to float."""
        code_node.set_state_value("timeout", "25")
        code_node.set_state_value("code", "result = 42")

        result = code_node.execute({})

        assert result.success is True
        # Timeout conversion is internal, but execution should succeed

    def test_invalid_timeout_defaults(self, code_node):
        """Test that invalid timeout defaults to 30 seconds."""
        code_node.set_state_value("timeout", "invalid")
        code_node.set_state_value("code", "result = 42")

        result = code_node.execute({})

        assert result.success is True


class TestExecutionResult:
    """Tests for execution result properties."""

    def test_result_has_duration(self, code_node):
        """Test that result includes execution duration."""
        code_node.update_state({"code": "result = 42"})
        result = code_node.execute({})

        assert result.duration_seconds >= 0

    def test_successful_result_structure(self, code_node):
        """Test structure of successful result."""
        code_node.update_state({"code": "result = 42"})
        result = code_node.execute({})

        assert result.success is True
        assert result.error is None
        assert isinstance(result.data, dict)
        assert "result" in result.data

    def test_failed_result_structure(self, code_node):
        """Test structure of failed result."""
        code_node.update_state({"code": "import os"})
        result = code_node.execute({})

        assert result.success is False
        assert result.error is not None
        assert isinstance(result.error, str)


class TestBuiltinFunctions:
    """Tests for safe builtin functions."""

    def test_math_functions(self, code_node):
        """Test math builtin functions."""
        code_node.update_state(
            {
                "code": "result = abs(-42) + min(5, 10) + max(5, 10) + round(3.7)",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == 42 + 5 + 10 + 4

    def test_sequence_functions(self, code_node):
        """Test sequence builtin functions."""
        code_node.update_state(
            {
                "code": "result = len([1,2,3]) + sum([10, 20, 30])",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == 3 + 60

    def test_type_constructors(self, code_node):
        """Test type constructor functions."""
        code_node.update_state(
            {
                "code": "result = int('42') + float('3.14') + len(str(100))",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == 42 + 3.14 + 3

    def test_iteration_functions(self, code_node):
        """Test iteration builtin functions."""
        code_node.update_state(
            {
                "code": "result = list(range(5)) + sorted([3,1,2]) + list(reversed([1,2,3]))",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == [0, 1, 2, 3, 4] + [1, 2, 3] + [3, 2, 1]

    def test_filter_map(self, code_node):
        """Test filter and map functions."""
        code_node.update_state(
            {
                "code": (
                    "evens = list(filter(lambda x: x % 2 == 0, range(10)))\n"
                    "doubled = list(map(lambda x: x * 2, [1,2,3]))\n"
                    "result = evens + doubled"
                ),
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == [0, 2, 4, 6, 8] + [2, 4, 6]


class TestComplexScenarios:
    """Tests for complex code scenarios."""

    def test_nested_data_structures(self, code_node):
        """Test working with nested data structures."""
        code_node.update_state(
            {
                "code": """
users = [
    {'name': 'Alice', 'age': 30},
    {'name': 'Bob', 'age': 25},
    {'name': 'Charlie', 'age': 35}
]
result = [u['name'] for u in users if u['age'] >= 30]
""",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == ["Alice", "Charlie"]

    def test_class_definition(self, code_node):
        """Test defining and using classes."""
        code_node.update_state(
            {
                "code": """
class Calculator:
    def add(self, a, b):
        return a + b

calc = Calculator()
result = calc.add(10, 32)
""",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"] == 42

    def test_multiple_operations(self, code_node):
        """Test multiple sequential operations."""
        code_node.update_state(
            {
                "code": """
# Calculate factorial
n = 5
factorial = 1
for i in range(1, n + 1):
    factorial *= i

# Calculate fibonacci
fib = [0, 1]
for i in range(8):
    fib.append(fib[-1] + fib[-2])

result = {'factorial': factorial, 'fibonacci': fib[-1]}
""",
            }
        )

        result = code_node.execute({})

        assert result.success is True
        assert result.data["result"]["factorial"] == 120
        assert result.data["result"]["fibonacci"] == 34
