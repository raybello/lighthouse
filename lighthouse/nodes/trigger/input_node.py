"""
Input node for providing static data to workflows.

Pure business logic with NO UI dependencies.
"""

import json
from typing import Any, Dict, List

from lighthouse.domain.models.field_types import FieldDefinition, FieldType
from lighthouse.domain.models.node import ExecutionResult, NodeMetadata, NodeType
from lighthouse.nodes.base.base_node import TriggerNode


class InputNode(TriggerNode):
    """
    Input node for providing static data to workflows.

    Allows defining key-value pairs that can be referenced by downstream nodes.
    Supports dynamic property management (add/remove properties).

    State Fields:
        properties: JSON string containing list of {name, value, type} objects
    """

    def __init__(self, name: str = "Input", **kwargs):
        """Initialize InputNode with default properties."""
        super().__init__(name, **kwargs)

        # Initialize with default properties if not provided
        if not self.state.get("properties"):
            default_properties = [{"name": "name", "value": "John"}, {"name": "age", "value": "30"}]
            self.state["properties"] = json.dumps(default_properties)

    @property
    def metadata(self) -> NodeMetadata:
        """Get input node metadata."""
        return NodeMetadata(
            node_type=NodeType.TRIGGER,
            name="Input",
            description="Provides static data to workflows via configurable properties",
            version="1.0.0",
            fields=[
                FieldDefinition(
                    name="properties",
                    label="Properties",
                    field_type=FieldType.STRING,  # JSON string
                    default_value=json.dumps(
                        [{"name": "name", "value": "John"}, {"name": "age", "value": "30"}]
                    ),
                    required=False,
                    description="JSON array of property definitions",
                ),
            ],
            has_inputs=False,  # Triggers have no inputs
            has_config=True,  # Has custom configuration
            category="Triggers",
        )

    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the input node.

        Parses the properties JSON and returns the key-value pairs as data.

        Args:
            context: Execution context (not used)

        Returns:
            ExecutionResult with property data
        """
        import time

        start_time = time.time()

        try:
            # Parse properties JSON
            properties_json = self.get_state_value("properties", "[]")
            properties = self._parse_properties(properties_json)

            # Convert properties list to data dictionary
            data = self._properties_to_dict(properties)

            duration = time.time() - start_time

            return ExecutionResult.success_result(
                data=data,
                duration=duration,
            )

        except json.JSONDecodeError as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Invalid JSON in properties: {str(e)}",
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult.error_result(
                error=f"Error processing input: {str(e)}",
                duration=duration,
            )

    def _parse_properties(self, properties_json: str) -> List[Dict[str, Any]]:
        """
        Parse properties JSON string.

        Args:
            properties_json: JSON string containing property definitions

        Returns:
            List of property dictionaries

        Raises:
            json.JSONDecodeError: If JSON is invalid
        """
        if not properties_json or properties_json.strip() == "":
            return []

        properties = json.loads(properties_json)

        if not isinstance(properties, list):
            return []

        return properties

    def _properties_to_dict(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert properties list to dictionary.

        Args:
            properties: List of property objects with name, value, type

        Returns:
            Dictionary mapping property names to values
        """
        data = {}

        for prop in properties:
            if not isinstance(prop, dict):
                continue

            name = prop.get("name")
            value = prop.get("value")
            prop_type = prop.get("type", "string")

            if not name:
                continue

            # Convert value based on type
            try:
                converted_value = self._convert_value(value, prop_type)
                data[name] = converted_value
            except Exception:
                # If conversion fails, use string value
                data[name] = str(value) if value is not None else ""

        return data

    def _convert_value(self, value: Any, value_type: str) -> Any:
        """
        Convert value to specified type.

        Args:
            value: Raw value
            value_type: Target type (string, number, boolean, object)

        Returns:
            Converted value
        """
        if value_type == "number":
            if isinstance(value, (int, float)):
                return value
            return float(value) if "." in str(value) else int(value)

        elif value_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1", "on")
            return bool(value)

        elif value_type == "object":
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                return json.loads(value)
            return value

        else:  # string or default
            return str(value) if value is not None else ""

    def add_property(self, name: str, value: Any, value_type: str = "string") -> None:
        """
        Add a new property to the input node.

        Helper method for programmatically adding properties.

        Args:
            name: Property name
            value: Property value
            value_type: Property type (string, number, boolean, object)
        """
        properties = self._parse_properties(self.get_state_value("properties", "[]"))
        properties.append({"name": name, "value": value, "type": value_type})
        self.set_state_value("properties", json.dumps(properties))

    def remove_property(self, name: str) -> None:
        """
        Remove a property from the input node.

        Args:
            name: Property name to remove
        """
        properties = self._parse_properties(self.get_state_value("properties", "[]"))
        properties = [p for p in properties if p.get("name") != name]
        self.set_state_value("properties", json.dumps(properties))

    def get_property_value(self, name: str) -> Any:
        """
        Get a property value by name.

        Args:
            name: Property name

        Returns:
            Property value or None if not found
        """
        properties = self._parse_properties(self.get_state_value("properties", "[]"))
        for prop in properties:
            if prop.get("name") == name:
                return prop.get("value")
        return None

    def validate(self) -> List[str]:
        """
        Validate input node configuration.

        Returns:
            List of validation errors
        """
        errors = []

        properties_json = self.get_state_value("properties", "[]")

        # Try to parse JSON
        try:
            properties = self._parse_properties(properties_json)

            # Validate each property
            for i, prop in enumerate(properties):
                if not isinstance(prop, dict):
                    errors.append(f"Property {i} is not a valid object")
                    continue

                if "name" not in prop or not prop["name"]:
                    errors.append(f"Property {i} is missing a name")

                if "value" not in prop:
                    errors.append(
                        f"Property {i} ('{prop.get('name', 'unnamed')}') is missing a value"
                    )

        except json.JSONDecodeError:
            errors.append("Properties must be valid JSON")

        return errors
