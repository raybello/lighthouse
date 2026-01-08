"""
Form node for creating dynamic forms with typed fields.

Pure business logic with NO UI dependencies.
"""

import json
import time
from typing import Any, Dict, List

from lighthouse.domain.models.field_types import FieldDefinition, FieldType
from lighthouse.domain.models.node import ExecutionResult, NodeMetadata, NodeType
from lighthouse.nodes.base.base_node import ExecutionNode


class FormNode(ExecutionNode):
    """
    Node for creating dynamic forms with fields that accept expressions.

    Supports multiple field types: string, number, boolean, object
    Each field can contain {{}} expressions to reference previous node outputs.

    State Fields:
        form_fields_json: JSON string storing the list of form fields
            Each field has: name (str), type (str), value (str)
    """

    def __init__(self, name: str = "Form"):
        """Initialize form node with default fields."""
        # Store form fields as a list of dicts (before calling super)
        self.form_fields = [
            {"name": "fullName", "type": "string", "value": ""},
            {"name": "age", "type": "number", "value": "0"},
            {"name": "isActive", "type": "boolean", "value": "true"},
        ]

        super().__init__(name)

        # Initialize state with JSON representation
        self.state["form_fields_json"] = self._fields_to_json()

    @property
    def metadata(self) -> NodeMetadata:
        """Get form node metadata."""
        return NodeMetadata(
            node_type=NodeType.EXECUTION,
            name="Form",
            description="Creates dynamic forms with typed fields supporting expressions",
            version="1.0.0",
            fields=[
                FieldDefinition(
                    name="form_fields_json",
                    label="Form Fields (JSON)",
                    field_type=FieldType.STRING,  # Stores JSON array
                    default_value=json.dumps(
                        [
                            {"name": "fullName", "type": "string", "value": ""},
                            {"name": "age", "type": "number", "value": "0"},
                            {"name": "isActive", "type": "boolean", "value": "true"},
                        ]
                    ),
                    required=True,
                    description="JSON array of form fields with name, type, and value",
                ),
            ],
            has_inputs=True,
            has_config=True,
            category="Data",
        )

    def _fields_to_json(self) -> str:
        """Convert form fields list to JSON string."""
        return json.dumps(self.form_fields)

    def _json_to_fields(self, json_str: str) -> None:
        """Parse JSON string to form fields list."""
        try:
            self.form_fields = json.loads(json_str)
        except json.JSONDecodeError:
            self.form_fields = []

    def update_form_fields(self, fields: List[Dict[str, str]]) -> None:
        """
        Update form fields and sync to state.

        Args:
            fields: List of field dictionaries with name, type, value
        """
        self.form_fields = fields
        self.update_state({"form_fields_json": self._fields_to_json()})

    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the form node - evaluate all field expressions and return structured output.

        Args:
            context: Execution context (not used directly)

        Returns:
            ExecutionResult with form data: {field_name: evaluated_value, ...}
        """
        start_time = time.time()

        try:
            # Sync state to form_fields before execution
            form_fields_json = self.get_state_value("form_fields_json", "[]")
            self._json_to_fields(form_fields_json)

            # Validate before execution
            if not self.form_fields:
                return ExecutionResult.error_result(
                    error="No fields defined",
                    duration=time.time() - start_time,
                )

            # Build the output data
            output_data = {}

            for field in self.form_fields:
                field_name = field.get("name", "")
                field_type = field.get("type", "string")
                field_value = field.get("value", "")

                if not field_name:
                    continue

                # Convert value based on field type
                # Note: Expression resolution happens in the executor layer
                if field_type == "string":
                    output_data[field_name] = str(field_value)
                elif field_type == "number":
                    output_data[field_name] = self._parse_number(field_value)
                elif field_type == "boolean":
                    output_data[field_name] = self._parse_boolean(field_value)
                elif field_type == "object":
                    output_data[field_name] = self._parse_object(field_value)
                else:
                    output_data[field_name] = field_value

            duration = time.time() - start_time

            return ExecutionResult.success_result(
                data=output_data,
                duration=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Form execution failed: {str(e)}",
                duration=duration,
            )

    def _parse_number(self, value: str) -> float | int:
        """Parse value as number."""
        try:
            str_value = str(value)
            if "." in str_value:
                return float(value)
            else:
                return int(value)
        except (ValueError, TypeError):
            return 0

    def _parse_boolean(self, value: str) -> bool:
        """Parse value as boolean."""
        return str(value).lower() in ["true", "1", "yes"]

    def _parse_object(self, value: str) -> Any:
        """Parse value as JSON object."""
        try:
            if isinstance(value, str):
                return json.loads(value)
            else:
                return value
        except json.JSONDecodeError:
            return value

    def validate(self) -> list[str]:
        """
        Validate form configuration.

        Returns:
            List of validation errors
        """
        errors = super().validate()

        # Use form_fields directly instead of reparsing from JSON
        if not isinstance(self.form_fields, list):
            errors.append("Form fields must be a list")
            return errors

        # Validate individual fields
        field_names = set()

        for i, field in enumerate(self.form_fields):
            if not isinstance(field, dict):
                errors.append(f"Field {i + 1}: Must be an object")
                continue

            field_name = field.get("name", "")
            field_type = field.get("type", "")

            # Validate field name
            if not field_name or not field_name.strip():
                errors.append(f"Field {i + 1}: Field name is required")
            elif not field_name.replace("_", "").isalnum():
                errors.append(
                    f"Field {i + 1}: Field name '{field_name}' must be alphanumeric "
                    "(underscores allowed)"
                )
            elif field_name in field_names:
                errors.append(f"Field {i + 1}: Duplicate field name '{field_name}'")
            else:
                field_names.add(field_name)

            # Validate field type
            valid_types = ["string", "number", "boolean", "object"]
            if field_type not in valid_types:
                errors.append(
                    f"Field '{field_name}': Invalid type '{field_type}'. "
                    f"Must be one of: {', '.join(valid_types)}"
                )

            # Validate value based on type (only if not an expression)
            field_value = field.get("value", "")
            if field_value and not str(field_value).strip().startswith("{{"):
                if field_type == "number":
                    try:
                        float(field_value)
                    except (ValueError, TypeError):
                        errors.append(f"Field '{field_name}': Value must be a number or expression")
                elif field_type == "boolean":
                    if str(field_value).lower() not in ["true", "false", "1", "0", "yes", "no"]:
                        errors.append(
                            f"Field '{field_name}': Value must be true/false or expression"
                        )
                elif field_type == "object":
                    if not str(field_value).startswith("{") and not str(field_value).startswith(
                        "["
                    ):
                        errors.append(
                            f"Field '{field_name}': Value must be valid JSON "
                            "object/array or expression"
                        )

        return errors
