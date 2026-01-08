"""Unit tests for trigger nodes (ManualTrigger and Input)."""

import json

import pytest

from lighthouse.domain.models.node import NodeType
from lighthouse.nodes.trigger.input_node import InputNode
from lighthouse.nodes.trigger.manual_trigger_node import ManualTriggerNode

# ============================================================================
# ManualTriggerNode Tests
# ============================================================================


@pytest.fixture
def manual_trigger_node():
    """Create a ManualTriggerNode instance."""
    return ManualTriggerNode(name="Test Trigger")


class TestManualTriggerNodeInitialization:
    """Tests for ManualTriggerNode initialization."""

    def test_node_creation(self, manual_trigger_node):
        """Test creating a manual trigger node."""
        assert manual_trigger_node.name == "Test Trigger"
        assert manual_trigger_node.id is not None
        assert len(manual_trigger_node.id) == 8

    def test_metadata(self, manual_trigger_node):
        """Test node metadata."""
        metadata = manual_trigger_node.metadata
        assert metadata.name == "ManualTrigger"
        assert metadata.node_type == NodeType.TRIGGER
        assert metadata.has_inputs is False
        assert metadata.has_config is False
        assert len(metadata.fields) == 0

    def test_default_state(self, manual_trigger_node):
        """Test default state is empty."""
        state = manual_trigger_node.state
        assert state == {}


class TestManualTriggerExecution:
    """Tests for ManualTriggerNode execution."""

    def test_execute_success(self, manual_trigger_node):
        """Test executing manual trigger."""
        result = manual_trigger_node.execute({})

        assert result.success is True
        assert result.data == {}
        assert result.error is None
        assert result.duration_seconds >= 0  # Duration may be 0 for very fast execution

    def test_execute_with_context(self, manual_trigger_node):
        """Test that context is ignored."""
        context = {"SomeNode": {"data": {"value": 123}}}
        result = manual_trigger_node.execute(context)

        assert result.success is True
        assert result.data == {}

    def test_validate_always_valid(self, manual_trigger_node):
        """Test that manual trigger is always valid."""
        errors = manual_trigger_node.validate()
        assert errors == []


# ============================================================================
# InputNode Tests
# ============================================================================


@pytest.fixture
def input_node():
    """Create an InputNode instance."""
    return InputNode(name="Test Input")


class TestInputNodeInitialization:
    """Tests for InputNode initialization."""

    def test_node_creation(self, input_node):
        """Test creating an input node."""
        assert input_node.name == "Test Input"
        assert input_node.id is not None

    def test_metadata(self, input_node):
        """Test node metadata."""
        metadata = input_node.metadata
        assert metadata.name == "Input"
        assert metadata.node_type == NodeType.TRIGGER
        assert metadata.has_inputs is False
        assert metadata.has_config is True
        assert len(metadata.fields) == 1  # properties

    def test_default_state(self, input_node):
        """Test default state with default properties (like legacy)."""
        state = input_node.state
        assert "properties" in state
        # Should have default properties like legacy implementation
        properties = json.loads(state["properties"])
        assert len(properties) == 2
        assert properties[0]["name"] == "name"
        assert properties[0]["value"] == "John"
        assert properties[1]["name"] == "age"
        assert properties[1]["value"] == "30"


class TestInputNodeExecution:
    """Tests for InputNode execution."""

    def test_execute_empty_properties(self, input_node):
        """Test executing with default properties."""
        # Clear properties to make it actually empty
        input_node.set_state_value("properties", "[]")
        result = input_node.execute({})

        assert result.success is True
        assert result.data == {}

    def test_execute_with_string_property(self, input_node):
        """Test executing with a string property."""
        properties = [{"name": "username", "value": "john_doe", "type": "string"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})

        assert result.success is True
        assert result.data["username"] == "john_doe"

    def test_execute_with_number_property(self, input_node):
        """Test executing with a number property."""
        properties = [{"name": "age", "value": "30", "type": "number"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})

        assert result.success is True
        assert result.data["age"] == 30

    def test_execute_with_float_property(self, input_node):
        """Test executing with a float property."""
        properties = [{"name": "price", "value": "19.99", "type": "number"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})

        assert result.success is True
        assert result.data["price"] == 19.99

    def test_execute_with_boolean_property(self, input_node):
        """Test executing with a boolean property."""
        properties = [{"name": "active", "value": "true", "type": "boolean"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})

        assert result.success is True
        assert result.data["active"] is True

    def test_execute_with_object_property(self, input_node):
        """Test executing with an object property."""
        obj = {"nested": "value", "count": 42}
        properties = [{"name": "config", "value": obj, "type": "object"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})

        assert result.success is True
        assert result.data["config"] == obj

    def test_execute_with_multiple_properties(self, input_node):
        """Test executing with multiple properties."""
        properties = [
            {"name": "name", "value": "Alice", "type": "string"},
            {"name": "age", "value": "25", "type": "number"},
            {"name": "active", "value": "true", "type": "boolean"},
        ]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})

        assert result.success is True
        assert result.data["name"] == "Alice"
        assert result.data["age"] == 25
        assert result.data["active"] is True


class TestInputNodePropertyManagement:
    """Tests for property management methods."""

    def test_add_property(self, input_node):
        """Test adding a property."""
        # Start with empty properties to test adding
        input_node.set_state_value("properties", "[]")
        input_node.add_property("email", "test@example.com", "string")

        properties = json.loads(input_node.get_state_value("properties"))
        assert len(properties) == 1
        assert properties[0]["name"] == "email"
        assert properties[0]["value"] == "test@example.com"

    def test_add_multiple_properties(self, input_node):
        """Test adding multiple properties."""
        # Start with empty properties to test adding
        input_node.set_state_value("properties", "[]")
        input_node.add_property("name", "John", "string")
        input_node.add_property("age", "30", "number")

        properties = json.loads(input_node.get_state_value("properties"))
        assert len(properties) == 2

    def test_remove_property(self, input_node):
        """Test removing a property."""
        # Start with empty properties
        input_node.set_state_value("properties", "[]")
        input_node.add_property("temp", "value", "string")
        input_node.add_property("keep", "value", "string")

        input_node.remove_property("temp")

        properties = json.loads(input_node.get_state_value("properties"))
        assert len(properties) == 1
        assert properties[0]["name"] == "keep"

    def test_remove_nonexistent_property(self, input_node):
        """Test removing a property that doesn't exist."""
        # Start with empty properties
        input_node.set_state_value("properties", "[]")
        input_node.add_property("name", "value", "string")

        input_node.remove_property("nonexistent")

        properties = json.loads(input_node.get_state_value("properties"))
        assert len(properties) == 1  # Original property remains

    def test_get_property_value(self, input_node):
        """Test getting a property value."""
        input_node.add_property("email", "test@example.com", "string")

        value = input_node.get_property_value("email")
        assert value == "test@example.com"

    def test_get_nonexistent_property_value(self, input_node):
        """Test getting a nonexistent property value."""
        value = input_node.get_property_value("nonexistent")
        assert value is None


class TestInputNodeValidation:
    """Tests for InputNode validation."""

    def test_validate_valid_properties(self, input_node):
        """Test validation with valid properties."""
        properties = [{"name": "test", "value": "value", "type": "string"}]
        input_node.set_state_value("properties", json.dumps(properties))

        errors = input_node.validate()
        assert errors == []

    def test_validate_empty_properties(self, input_node):
        """Test validation with empty properties."""
        errors = input_node.validate()
        assert errors == []

    def test_validate_invalid_json(self, input_node):
        """Test validation with invalid JSON."""
        input_node.set_state_value("properties", "invalid json {")

        errors = input_node.validate()
        assert len(errors) > 0
        assert any("JSON" in err for err in errors)

    def test_validate_missing_name(self, input_node):
        """Test validation with missing property name."""
        properties = [
            {"value": "test", "type": "string"}  # Missing name
        ]
        input_node.set_state_value("properties", json.dumps(properties))

        errors = input_node.validate()
        assert len(errors) > 0
        assert any("name" in err.lower() for err in errors)

    def test_validate_missing_value(self, input_node):
        """Test validation with missing property value."""
        properties = [
            {"name": "test", "type": "string"}  # Missing value
        ]
        input_node.set_state_value("properties", json.dumps(properties))

        errors = input_node.validate()
        assert len(errors) > 0
        assert any("value" in err.lower() for err in errors)

    def test_validate_empty_name(self, input_node):
        """Test validation with empty property name."""
        properties = [{"name": "", "value": "test", "type": "string"}]
        input_node.set_state_value("properties", json.dumps(properties))

        errors = input_node.validate()
        assert len(errors) > 0


class TestInputNodeTypeConversion:
    """Tests for type conversion logic."""

    def test_convert_boolean_true_strings(self, input_node):
        """Test converting various true boolean strings."""
        for value in ["true", "True", "TRUE", "yes", "1", "on"]:
            properties = [{"name": "test", "value": value, "type": "boolean"}]
            input_node.set_state_value("properties", json.dumps(properties))
            result = input_node.execute({})
            assert result.data["test"] is True

    def test_convert_boolean_false_strings(self, input_node):
        """Test converting false boolean strings."""
        for value in ["false", "False", "no", "0", "off"]:
            properties = [{"name": "test", "value": value, "type": "boolean"}]
            input_node.set_state_value("properties", json.dumps(properties))
            result = input_node.execute({})
            assert result.data["test"] is False

    def test_convert_number_integer(self, input_node):
        """Test converting integer strings."""
        properties = [{"name": "test", "value": "42", "type": "number"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})
        assert result.data["test"] == 42
        assert isinstance(result.data["test"], int)

    def test_convert_number_float(self, input_node):
        """Test converting float strings."""
        properties = [{"name": "test", "value": "3.14", "type": "number"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})
        assert abs(result.data["test"] - 3.14) < 0.001

    def test_fallback_to_string_on_error(self, input_node):
        """Test that invalid conversions fall back to string."""
        properties = [{"name": "test", "value": "not_a_number", "type": "number"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})
        # Should fall back to string
        assert isinstance(result.data["test"], str)


class TestInputNodeErrorHandling:
    """Tests for error handling."""

    def test_invalid_json_in_properties(self, input_node):
        """Test handling invalid JSON."""
        input_node.set_state_value("properties", "{invalid json")

        result = input_node.execute({})

        assert result.success is False
        assert "JSON" in result.error


class TestInputNodeEdgeCases:
    """Tests for edge cases."""

    def test_property_with_null_value(self, input_node):
        """Test property with null value."""
        properties = [{"name": "test", "value": None, "type": "string"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})
        assert result.data["test"] == ""

    def test_property_without_type(self, input_node):
        """Test property without explicit type (defaults to string)."""
        properties = [{"name": "test", "value": "value"}]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})
        assert result.data["test"] == "value"

    def test_non_dict_in_properties_array(self, input_node):
        """Test handling non-dict items in properties array."""
        properties = [
            {"name": "valid", "value": "test"},
            "invalid_item",  # Not a dict
            {"name": "also_valid", "value": "test2"},
        ]
        input_node.set_state_value("properties", json.dumps(properties))

        result = input_node.execute({})
        # Should skip the invalid item
        assert "valid" in result.data
        assert "also_valid" in result.data
        assert len(result.data) == 2
