"""
Pure domain service for evaluating {{}} syntax expressions.

Supports:
- Variable references from previous nodes: $node["NodeName"].data.property
- Basic arithmetic operations: +, -, *, /, %
- String concatenation
- Object property access (dot notation and bracket notation)
- Array indexing
- Basic Python-like expressions

This is a PURE service with ZERO external dependencies.
No UI, no logging, no file I/O - just computation.
"""

import re
from typing import Any, Dict

from lighthouse.domain.exceptions import ExpressionError


class DictWrapper:
    """
    Wrapper class to allow attribute access on dictionaries.
    This enables expressions like obj.property instead of obj["property"]
    """

    def __init__(self, data):
        self._data = data
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    setattr(self, key, DictWrapper(value))
                elif isinstance(value, list):
                    setattr(
                        self,
                        key,
                        [DictWrapper(item) if isinstance(item, dict) else item for item in value],
                    )
                else:
                    setattr(self, key, value)
        else:
            # If it's not a dict, just store it
            self._value = data

    def __getitem__(self, key):
        """Allow bracket notation access"""
        return getattr(self, key, None)

    def __repr__(self):
        # Return original dict for display
        return str(self.to_dict())

    def to_dict(self):
        """Convert back to a regular dict"""
        if isinstance(self._data, dict):
            result = {}
            for key, value in self._data.items():
                if isinstance(value, dict):
                    result[key] = value
                else:
                    result[key] = value
            return result
        return self._data

    def __eq__(self, other):
        """Allow equality comparison with dicts"""
        if isinstance(other, dict):
            return self.to_dict() == other
        elif isinstance(other, DictWrapper):
            return self.to_dict() == other.to_dict()
        return False


class ExpressionService:
    """
    Pure domain service for parsing and evaluating expressions with {{}} syntax.

    Expressions can reference node outputs using $node["NodeName"] syntax
    and perform calculations, property access, and string operations.

    This is a stateless service where context is passed to methods,
    not stored as mutable state.
    """

    def __init__(self):
        """Initialize the expression service (stateless)."""
        pass

    def has_expression(self, text: str) -> bool:
        """
        Check if a string contains {{}} expression syntax.

        Args:
            text: String to check

        Returns:
            True if the string contains at least one expression
        """
        if not isinstance(text, str):
            return False
        return bool(re.search(r"\{\{.*?\}\}", text))

    def extract_expressions(self, text: str) -> list:
        """
        Extract all {{}} expressions from a string.

        Args:
            text: String to extract expressions from

        Returns:
            List of expression strings (without {{ }})
        """
        if not isinstance(text, str):
            return []
        matches = re.findall(r"\{\{(.*?)\}\}", text)
        return matches

    def evaluate_expression(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        Evaluate a single expression using the provided context.

        Args:
            expression: Expression string (without {{ }})
            context: Dictionary mapping node names to their output data

        Returns:
            Evaluated result

        Raises:
            ExpressionError: If evaluation fails
        """
        try:
            # Replace $node["NodeName"] with context access
            # Pattern: $node["name"] or $node['name']
            node_pattern = r'\$node\[(["\'])([^"\']+)\1\]'

            def replace_node_ref(match):
                node_name = match.group(2)
                if node_name in context:
                    # Return a placeholder that we'll replace with actual data
                    return f"__node__{node_name}__"
                else:
                    raise ExpressionError(f"Node '{node_name}' not found in context")

            # Replace node references with placeholders
            modified_expr = re.sub(node_pattern, replace_node_ref, expression)

            # Build evaluation context with node data
            temp_context = {}
            for node_name, node_data in context.items():
                placeholder = f"__node__{node_name}__"
                if placeholder in modified_expr:
                    # Wrap the node data to allow attribute access
                    temp_context[placeholder] = DictWrapper(node_data)

            # Replace placeholders in the expression for evaluation
            # Use a simple variable name approach
            eval_context = {}
            for placeholder, data in temp_context.items():
                var_name = placeholder.replace("__node__", "node_").replace("__", "")
                modified_expr = modified_expr.replace(placeholder, var_name)
                eval_context[var_name] = data

            # Evaluate the expression with restricted builtins for safety
            result = eval(modified_expr, {"__builtins__": {}}, eval_context)
            return result

        except Exception as e:
            raise ExpressionError(f"Failed to evaluate expression '{expression}': {str(e)}")

    def resolve(self, value: Any, context: Dict[str, Any]) -> Any:
        """
        Resolve a value, evaluating any expressions it contains.

        For strings containing {{}} expressions:
        - If the string is ONLY an expression, return the evaluated result
        - If the string contains mixed content, substitute expressions and return string

        For other types, return as-is.

        Args:
            value: Value to resolve (can be string, number, dict, list, etc.)
            context: Execution context with node outputs

        Returns:
            Resolved value with expressions evaluated
        """
        if not isinstance(value, str):
            return value

        # Check if string has expressions
        if not self.has_expression(value):
            return value

        # Check if the entire string is a single expression
        single_expr_match = re.match(r"^\{\{(.+)\}\}$", value.strip())
        if single_expr_match:
            # Entire string is one expression - return evaluated result
            expression = single_expr_match.group(1).strip()
            try:
                return self.evaluate_expression(expression, context)
            except ExpressionError:
                # Return original value if evaluation fails
                # (caller can handle errors as needed)
                return value

        # String contains expressions mixed with other content
        # Substitute each expression with its evaluated result
        result = value
        expressions = self.extract_expressions(value)
        for expr in expressions:
            try:
                evaluated = self.evaluate_expression(expr, context)
                # Convert to string for substitution
                evaluated_str = str(evaluated) if evaluated is not None else ""
                result = result.replace(f"{{{{{expr}}}}}", evaluated_str)
            except ExpressionError:
                # Leave the expression as-is if evaluation fails
                pass

        return result

    def resolve_dict(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively resolve all expressions in a dictionary.

        Args:
            data: Dictionary with potential expressions
            context: Execution context with node outputs

        Returns:
            Dictionary with all expressions resolved
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self.resolve_dict(value, context)
            elif isinstance(value, list):
                result[key] = [
                    (
                        self.resolve(item, context)
                        if not isinstance(item, dict)
                        else self.resolve_dict(item, context)
                    )
                    for item in value
                ]
            else:
                result[key] = self.resolve(value, context)
        return result
