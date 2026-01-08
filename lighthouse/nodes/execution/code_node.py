"""
Code node for executing sandboxed Python code.

Pure business logic with NO UI dependencies.
"""

from typing import Dict, Any
import ast
import threading
import time

from lighthouse.nodes.base.base_node import ExecutionNode
from lighthouse.domain.models.node import NodeMetadata, NodeType, ExecutionResult
from lighthouse.domain.models.field_types import FieldDefinition, FieldType


# Safe builtins whitelist for code execution
SAFE_BUILTINS = {
    'abs': abs,
    'all': all,
    'any': any,
    'bool': bool,
    'dict': dict,
    'enumerate': enumerate,
    'filter': filter,
    'float': float,
    'int': int,
    'len': len,
    'list': list,
    'map': map,
    'max': max,
    'min': min,
    'range': range,
    'reversed': reversed,
    'round': round,
    'set': set,
    'sorted': sorted,
    'str': str,
    'sum': sum,
    'tuple': tuple,
    'zip': zip,
    'True': True,
    'False': False,
    'None': None,
    '__build_class__': __builtins__['__build_class__'],  # Required for class definitions
}


class CodeNode(ExecutionNode):
    """
    Node for executing sandboxed Python code.

    Executes Python code with safety restrictions:
    - AST validation to reject dangerous operations
    - Whitelisted safe builtins only
    - Timeout protection (30 seconds)
    - No imports, file I/O, or dangerous functions

    Code should set a 'result' variable for output.

    State Fields:
        code: Python code to execute
        timeout: Execution timeout in seconds
    """

    @property
    def metadata(self) -> NodeMetadata:
        """Get code node metadata."""
        return NodeMetadata(
            node_type=NodeType.EXECUTION,
            name="Code",
            description="Executes sandboxed Python code with safety restrictions",
            version="1.0.0",
            fields=[
                FieldDefinition(
                    name="code",
                    label="Python Code",
                    field_type=FieldType.STRING,  # Long text
                    default_value="# Write Python code here\n# Set 'result' variable for output\nresult = 42",
                    required=True,
                    description="Python code to execute (use 'result' variable for output)",
                ),
                FieldDefinition(
                    name="timeout",
                    label="Timeout (seconds)",
                    field_type=FieldType.NUMBER,
                    default_value=30,
                    required=True,
                    description="Code execution timeout",
                ),
            ],
            has_inputs=True,
            has_config=True,
            category="Programming",
        )

    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute Python code in a sandboxed environment.

        Args:
            context: Execution context (available in code as 'context' variable)

        Returns:
            ExecutionResult with execution result or error
        """
        start_time = time.time()

        try:
            code = self.get_state_value("code", "")
            timeout = self.get_state_value("timeout", 30)

            if not code or not code.strip():
                return ExecutionResult.error_result(
                    error="No code provided",
                    duration=time.time() - start_time,
                )

            # Convert timeout to float
            try:
                timeout_seconds = float(timeout)
            except (ValueError, TypeError):
                timeout_seconds = 30.0

            # Step 1: Validate code safety using AST
            validation_error = self._validate_code_safety(code)
            if validation_error:
                return ExecutionResult.error_result(
                    error=validation_error,
                    duration=time.time() - start_time,
                )

            # Step 2: Compile the code
            try:
                compiled = compile(code, '<code>', 'exec')
            except SyntaxError as e:
                return ExecutionResult.error_result(
                    error=f"Syntax error: {str(e)}",
                    duration=time.time() - start_time,
                )

            # Step 3: Execute with timeout
            result_container = self._execute_with_timeout(
                compiled, context, timeout_seconds
            )

            duration = time.time() - start_time

            if result_container["timeout"]:
                return ExecutionResult.error_result(
                    error=f"Execution timed out after {timeout_seconds}s",
                    duration=duration,
                )

            if result_container["error"]:
                return ExecutionResult.error_result(
                    error=result_container["error"],
                    duration=duration,
                )

            # Get result from execution
            result = result_container.get("result")

            return ExecutionResult.success_result(
                data={"result": result},
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Unexpected error: {str(e)}",
                duration=duration,
            )

    def _validate_code_safety(self, code: str) -> str:
        """
        Validate code safety using AST analysis.

        Args:
            code: Python code to validate

        Returns:
            Error message if unsafe, empty string if safe
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Syntax error: {str(e)}"

        for node in ast.walk(tree):
            # Reject imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return "Imports are not allowed in sandboxed code"

            # Reject dangerous function calls
            if isinstance(node, ast.Name):
                if node.id in ['eval', 'exec', 'compile', 'open', '__import__',
                               'globals', 'locals', 'vars', 'dir',
                               'getattr', 'setattr', 'delattr', 'hasattr']:
                    return f"Function '{node.id}' is not allowed"

            # Reject private/dunder attribute access
            if isinstance(node, ast.Attribute):
                if node.attr.startswith('_'):
                    return f"Access to private attribute '{node.attr}' is not allowed"

        return ""  # Code is safe

    def _execute_with_timeout(
        self, compiled_code, context: Dict[str, Any], timeout: float
    ) -> Dict[str, Any]:
        """
        Execute compiled code with timeout protection.

        Args:
            compiled_code: Compiled Python code
            context: Execution context from workflow
            timeout: Timeout in seconds

        Returns:
            Dictionary with result, error, and timeout status
        """
        result_container = {
            "result": None,
            "error": None,
            "timeout": False,
            "completed": False,
        }

        # Prepare execution namespace
        exec_namespace = {
            '__builtins__': SAFE_BUILTINS.copy(),
            'context': context,  # Make context available to code
            '__name__': '__main__',  # Required for class definitions
        }

        def run_code():
            try:
                exec(compiled_code, exec_namespace)
                result_container["result"] = exec_namespace.get('result', None)
                result_container["completed"] = True
            except Exception as e:
                result_container["error"] = str(e)

        # Execute in thread with timeout
        thread = threading.Thread(target=run_code)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            result_container["timeout"] = True

        return result_container

    def validate(self) -> list[str]:
        """
        Validate code node configuration.

        Returns:
            List of validation errors
        """
        errors = super().validate()

        code = self.get_state_value("code", "")
        if not code or not code.strip():
            errors.append("Code cannot be empty")
        else:
            # Validate code safety
            safety_error = self._validate_code_safety(code)
            if safety_error:
                errors.append(safety_error)

        timeout = self.get_state_value("timeout", 30)
        try:
            timeout_num = float(timeout)
            if timeout_num <= 0:
                errors.append("Timeout must be greater than 0")
            if timeout_num > 300:  # Max 5 minutes
                errors.append("Timeout cannot exceed 300 seconds")
        except (ValueError, TypeError):
            errors.append("Timeout must be a number")

        return errors
