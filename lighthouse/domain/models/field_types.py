"""Field type definitions for node configuration."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class FieldType(Enum):
    """Supported field types for node configuration."""

    STRING = "string"
    LONG_STRING = "long_string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    OBJECT = "object"


@dataclass
class FieldDefinition:
    """
    Definition of a configuration field for a node.

    Attributes:
        name: Unique field identifier
        label: Display label for the field
        field_type: Type of the field
        default_value: Default value for the field
        required: Whether the field is required
        validation: Optional validation function
        enum_options: For ENUM type, list of valid options
        description: Optional field description
    """

    name: str
    label: str
    field_type: FieldType
    default_value: Any
    required: bool = True
    validation: Optional[Callable[[Any], bool]] = None
    enum_options: Optional[list] = None
    description: Optional[str] = None

    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this field definition.

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required
        if self.required and (value is None or value == ""):
            return False, f"{self.label} is required"

        # Check enum options
        if self.field_type == FieldType.ENUM and self.enum_options:
            if value not in self.enum_options:
                return False, f"{self.label} must be one of {self.enum_options}"

        # Run custom validation if provided
        if self.validation and not self.validation(value):
            return False, f"{self.label} validation failed"

        return True, None
