"""Unit tests for FormNode."""

import pytest
import json
from lighthouse.nodes.execution.form_node import FormNode


@pytest.fixture
def form_node():
    """Create a FormNode instance."""
    return FormNode(name="Test Form")


class TestFormNodeInitialization:
    """Tests for node initialization."""

    def test_node_creation(self, form_node):
        """Test creating form node."""
        assert form_node.name == "Test Form"
        assert form_node.id is not None

    def test_metadata(self, form_node):
        """Test node metadata."""
        metadata = form_node.metadata
        assert metadata.name == "Form"
        assert len(metadata.fields) == 1  # form_fields_json

    def test_default_state(self, form_node):
        """Test default state values."""
        state = form_node.state
        assert "form_fields_json" in state
        # Parse default fields
        fields = json.loads(state["form_fields_json"])
        assert len(fields) == 3
        assert fields[0]["name"] == "fullName"
        assert fields[1]["name"] == "age"
        assert fields[2]["name"] == "isActive"

    def test_default_form_fields(self, form_node):
        """Test default form fields."""
        assert len(form_node.form_fields) == 3
        assert form_node.form_fields[0]["type"] == "string"
        assert form_node.form_fields[1]["type"] == "number"
        assert form_node.form_fields[2]["type"] == "boolean"


class TestFormExecution:
    """Tests for form execution."""

    def test_execute_with_string_field(self, form_node):
        """Test executing form with string field."""
        form_node.update_form_fields([
            {"name": "username", "type": "string", "value": "Alice"}
        ])

        result = form_node.execute({})

        assert result.success is True
        assert result.data["username"] == "Alice"

    def test_execute_with_number_field(self, form_node):
        """Test executing form with number field."""
        form_node.update_form_fields([
            {"name": "age", "type": "number", "value": "30"}
        ])

        result = form_node.execute({})

        assert result.success is True
        assert result.data["age"] == 30

    def test_execute_with_float_field(self, form_node):
        """Test executing form with float field."""
        form_node.update_form_fields([
            {"name": "price", "type": "number", "value": "19.99"}
        ])

        result = form_node.execute({})

        assert result.success is True
        assert result.data["price"] == 19.99

    def test_execute_with_boolean_field(self, form_node):
        """Test executing form with boolean field."""
        form_node.update_form_fields([
            {"name": "isActive", "type": "boolean", "value": "true"}
        ])

        result = form_node.execute({})

        assert result.success is True
        assert result.data["isActive"] is True

    def test_execute_with_object_field(self, form_node):
        """Test executing form with object field."""
        form_node.update_form_fields([
            {"name": "config", "type": "object", "value": '{"key": "value"}'}
        ])

        result = form_node.execute({})

        assert result.success is True
        assert result.data["config"] == {"key": "value"}

    def test_execute_with_multiple_fields(self, form_node):
        """Test executing form with multiple fields."""
        form_node.update_form_fields([
            {"name": "name", "type": "string", "value": "Bob"},
            {"name": "age", "type": "number", "value": "25"},
            {"name": "active", "type": "boolean", "value": "true"}
        ])

        result = form_node.execute({})

        assert result.success is True
        assert result.data["name"] == "Bob"
        assert result.data["age"] == 25
        assert result.data["active"] is True

    def test_execute_result_includes_all_fields(self, form_node):
        """Test that result includes all non-empty field names."""
        form_node.update_form_fields([
            {"name": "field1", "type": "string", "value": "value1"},
            {"name": "field2", "type": "number", "value": "42"},
            {"name": "", "type": "string", "value": "ignored"},  # Empty name
        ])

        result = form_node.execute({})

        assert result.success is True
        assert "field1" in result.data
        assert "field2" in result.data
        assert len(result.data) == 2  # Empty name field should be skipped


class TestFieldTypeParsing:
    """Tests for field type parsing."""

    def test_parse_number_integer(self, form_node):
        """Test parsing integer numbers."""
        assert form_node._parse_number("42") == 42
        assert form_node._parse_number(42) == 42

    def test_parse_number_float(self, form_node):
        """Test parsing float numbers."""
        assert form_node._parse_number("3.14") == 3.14
        assert form_node._parse_number(3.14) == 3.14

    def test_parse_number_invalid(self, form_node):
        """Test parsing invalid numbers."""
        assert form_node._parse_number("not a number") == 0
        assert form_node._parse_number("") == 0

    def test_parse_boolean_true_values(self, form_node):
        """Test parsing true boolean values."""
        assert form_node._parse_boolean("true") is True
        assert form_node._parse_boolean("TRUE") is True
        assert form_node._parse_boolean("1") is True
        assert form_node._parse_boolean("yes") is True

    def test_parse_boolean_false_values(self, form_node):
        """Test parsing false boolean values."""
        assert form_node._parse_boolean("false") is False
        assert form_node._parse_boolean("FALSE") is False
        assert form_node._parse_boolean("0") is False
        assert form_node._parse_boolean("no") is False
        assert form_node._parse_boolean("anything else") is False

    def test_parse_object_valid_json(self, form_node):
        """Test parsing valid JSON objects."""
        result = form_node._parse_object('{"key": "value"}')
        assert result == {"key": "value"}

        result = form_node._parse_object('["a", "b", "c"]')
        assert result == ["a", "b", "c"]

    def test_parse_object_invalid_json(self, form_node):
        """Test parsing invalid JSON objects."""
        result = form_node._parse_object("not json")
        assert result == "not json"

    def test_parse_object_already_parsed(self, form_node):
        """Test parsing already-parsed objects."""
        obj = {"key": "value"}
        result = form_node._parse_object(obj)
        assert result == obj


class TestFormFieldManagement:
    """Tests for form field management."""

    def test_update_form_fields(self, form_node):
        """Test updating form fields."""
        new_fields = [
            {"name": "email", "type": "string", "value": "test@example.com"}
        ]

        form_node.update_form_fields(new_fields)

        assert form_node.form_fields == new_fields

    def test_json_serialization(self, form_node):
        """Test JSON serialization of form fields."""
        fields = [
            {"name": "test", "type": "string", "value": "value"}
        ]
        form_node.form_fields = fields

        json_str = form_node._fields_to_json()
        assert isinstance(json_str, str)

        # Parse back and verify
        parsed = json.loads(json_str)
        assert parsed == fields

    def test_json_deserialization(self, form_node):
        """Test JSON deserialization of form fields."""
        fields = [
            {"name": "test", "type": "number", "value": "42"}
        ]
        json_str = json.dumps(fields)

        form_node._json_to_fields(json_str)

        assert form_node.form_fields == fields

    def test_json_deserialization_invalid(self, form_node):
        """Test JSON deserialization with invalid JSON."""
        form_node._json_to_fields("invalid json")

        assert form_node.form_fields == []


class TestErrorHandling:
    """Tests for error handling."""

    def test_no_fields_error(self, form_node):
        """Test error when no fields are defined."""
        form_node.update_form_fields([])

        result = form_node.execute({})

        assert result.success is False
        assert "no fields" in result.error.lower()

    def test_empty_json_error(self, form_node):
        """Test error with empty form fields."""
        form_node.update_form_fields([])

        result = form_node.execute({})

        assert result.success is False
        assert "no fields" in result.error.lower()

    def test_invalid_json_during_execution(self, form_node):
        """Test execution with empty form_fields_json in state."""
        # Set state to empty array
        form_node.update_state({"form_fields_json": "[]"})

        result = form_node.execute({})

        # Should error because form_fields is empty
        assert result.success is False
        assert "no fields" in result.error.lower()


class TestValidation:
    """Tests for configuration validation."""

    def test_validate_valid_config(self, form_node):
        """Test validation with valid configuration."""
        errors = form_node.validate()
        assert errors == []

    def test_validate_invalid_json(self, form_node):
        """Test validation with manually corrupted form_fields."""
        # Manually corrupt form_fields to a non-list
        form_node.form_fields = "not a list"

        errors = form_node.validate()

        assert len(errors) > 0
        assert any("list" in err.lower() for err in errors)

    def test_validate_not_array(self, form_node):
        """Test validation catches non-list form_fields."""
        form_node.form_fields = {"not": "a list"}

        errors = form_node.validate()

        assert len(errors) > 0
        assert any("list" in err.lower() for err in errors)

    def test_validate_empty_field_name(self, form_node):
        """Test validation catches empty field names."""
        form_node.update_form_fields([
            {"name": "", "type": "string", "value": "test"}
        ])

        errors = form_node.validate()

        assert len(errors) > 0
        assert any("name is required" in err.lower() for err in errors)

    def test_validate_invalid_field_name(self, form_node):
        """Test validation catches invalid field names."""
        form_node.update_form_fields([
            {"name": "field-name!", "type": "string", "value": "test"}
        ])

        errors = form_node.validate()

        assert len(errors) > 0
        assert any("alphanumeric" in err.lower() for err in errors)

    def test_validate_duplicate_field_names(self, form_node):
        """Test validation catches duplicate field names."""
        form_node.update_form_fields([
            {"name": "field1", "type": "string", "value": "a"},
            {"name": "field1", "type": "number", "value": "1"}
        ])

        errors = form_node.validate()

        assert len(errors) > 0
        assert any("duplicate" in err.lower() for err in errors)

    def test_validate_invalid_field_type(self, form_node):
        """Test validation catches invalid field types."""
        form_node.update_form_fields([
            {"name": "field1", "type": "invalid_type", "value": "test"}
        ])

        errors = form_node.validate()

        assert len(errors) > 0
        assert any("invalid type" in err.lower() for err in errors)

    def test_validate_number_field_invalid_value(self, form_node):
        """Test validation catches invalid number values."""
        form_node.update_form_fields([
            {"name": "age", "type": "number", "value": "not a number"}
        ])

        errors = form_node.validate()

        assert len(errors) > 0
        assert any("number" in err.lower() for err in errors)

    def test_validate_boolean_field_invalid_value(self, form_node):
        """Test validation catches invalid boolean values."""
        form_node.update_form_fields([
            {"name": "active", "type": "boolean", "value": "maybe"}
        ])

        errors = form_node.validate()

        assert len(errors) > 0
        assert any("true/false" in err.lower() for err in errors)

    def test_validate_object_field_invalid_value(self, form_node):
        """Test validation catches invalid object values."""
        form_node.update_form_fields([
            {"name": "config", "type": "object", "value": "not json"}
        ])

        errors = form_node.validate()

        assert len(errors) > 0
        assert any("json" in err.lower() for err in errors)

    def test_validate_expression_values_skip_validation(self, form_node):
        """Test that expression values skip type validation."""
        form_node.update_form_fields([
            {"name": "age", "type": "number", "value": "{{$node['Input'].data.age}}"},
            {"name": "active", "type": "boolean", "value": "{{$node['Input'].data.active}}"}
        ])

        errors = form_node.validate()

        # Should have no errors because values are expressions
        assert errors == []


class TestStateManagement:
    """Tests for state management."""

    def test_state_persistence(self, form_node):
        """Test that form fields persist across updates."""
        new_fields = [
            {"name": "email", "type": "string", "value": "test@example.com"}
        ]

        form_node.update_form_fields(new_fields)

        # Verify form_fields are updated
        assert form_node.form_fields == new_fields

    def test_field_name_with_underscores(self, form_node):
        """Test that field names with underscores are valid."""
        form_node.update_form_fields([
            {"name": "first_name", "type": "string", "value": "Alice"},
            {"name": "last_name", "type": "string", "value": "Bob"}
        ])

        errors = form_node.validate()
        assert errors == []


class TestExecutionResult:
    """Tests for execution result properties."""

    def test_result_has_duration(self, form_node):
        """Test that result includes execution duration."""
        form_node.update_form_fields([
            {"name": "test", "type": "string", "value": "value"}
        ])

        result = form_node.execute({})

        assert result.duration_seconds >= 0

    def test_successful_result_structure(self, form_node):
        """Test structure of successful result."""
        form_node.update_form_fields([
            {"name": "test", "type": "string", "value": "value"}
        ])

        result = form_node.execute({})

        assert result.success is True
        assert result.error is None
        assert isinstance(result.data, dict)

    def test_failed_result_structure(self, form_node):
        """Test structure of failed result."""
        form_node.update_form_fields([])

        result = form_node.execute({})

        assert result.success is False
        assert result.error is not None
        assert isinstance(result.error, str)


class TestComplexScenarios:
    """Tests for complex scenarios."""

    def test_mixed_field_types(self, form_node):
        """Test form with all field types."""
        form_node.update_form_fields([
            {"name": "name", "type": "string", "value": "Alice"},
            {"name": "age", "type": "number", "value": "30"},
            {"name": "score", "type": "number", "value": "95.5"},
            {"name": "active", "type": "boolean", "value": "true"},
            {"name": "tags", "type": "object", "value": '["a", "b", "c"]'},
            {"name": "config", "type": "object", "value": '{"key": "value"}'}
        ])

        result = form_node.execute({})

        assert result.success is True
        assert result.data["name"] == "Alice"
        assert result.data["age"] == 30
        assert result.data["score"] == 95.5
        assert result.data["active"] is True
        assert result.data["tags"] == ["a", "b", "c"]
        assert result.data["config"] == {"key": "value"}

    def test_many_fields(self, form_node):
        """Test form with many fields."""
        fields = [
            {"name": f"field{i}", "type": "string", "value": f"value{i}"}
            for i in range(20)
        ]

        form_node.update_form_fields(fields)

        result = form_node.execute({})

        assert result.success is True
        assert len(result.data) == 20
        assert result.data["field0"] == "value0"
        assert result.data["field19"] == "value19"

    def test_nested_json_objects(self, form_node):
        """Test form with nested JSON objects."""
        form_node.update_form_fields([
            {
                "name": "user",
                "type": "object",
                "value": '{"name": "Alice", "address": {"city": "NYC", "zip": "10001"}}'
            }
        ])

        result = form_node.execute({})

        assert result.success is True
        assert result.data["user"]["name"] == "Alice"
        assert result.data["user"]["address"]["city"] == "NYC"
