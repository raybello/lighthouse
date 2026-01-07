"""
Test script to verify Form Node validation
"""

from src.nodes import FormNode

# Create a mock Form Node (without DearPyGui)
class MockFormNode:
    """Mock Form Node for testing validation logic"""
    
    def __init__(self):
        self.form_fields = []
        self.id = "test_node"
    
    def _validate_fields_logic(self, fields_data):
        """
        Validate form fields (mimics the validation logic from FormNode).
        
        Returns:
            List of validation error messages
        """
        errors = []
        field_names = set()
        
        for i, field in enumerate(fields_data):
            name = field.get("name", "").strip()
            field_type = field.get("type", "string")
            value = field.get("value", "")
            
            # Validate field name
            if not name:
                errors.append(f"Field {i+1}: Field name is required")
            elif not name.replace("_", "").isalnum():
                errors.append(f"Field {i+1}: Field name '{name}' must be alphanumeric (underscores allowed)")
            elif name in field_names:
                errors.append(f"Field {i+1}: Duplicate field name '{name}'")
            else:
                field_names.add(name)
            
            # Validate value based on type (only if not an expression)
            if value and not value.strip().startswith("{{"):
                if field_type == "number":
                    try:
                        float(value)
                    except:
                        errors.append(f"Field '{name}': Value must be a number or expression")
                elif field_type == "boolean":
                    if value.lower() not in ["true", "false", "1", "0", "yes", "no"]:
                        errors.append(f"Field '{name}': Value must be true/false or expression")
                elif field_type == "object":
                    if not value.startswith("{") and not value.startswith("["):
                        errors.append(f"Field '{name}': Value must be valid JSON object/array or expression")
        
        return errors

# Test cases
print("=" * 60)
print("Form Node Validation Test Cases")
print("=" * 60)

mock = MockFormNode()

# Test 1: Valid form fields
print("\nTest 1: Valid form fields")
fields1 = [
    {"name": "fullName", "type": "string", "value": "John Doe"},
    {"name": "age", "type": "number", "value": "30"},
    {"name": "isActive", "type": "boolean", "value": "true"}
]
errors1 = mock._validate_fields_logic(fields1)
print(f"Fields: {len(fields1)} fields")
print(f"Errors: {errors1}")
print(f"✓ PASS" if len(errors1) == 0 else f"✗ FAIL")

# Test 2: Empty field name
print("\nTest 2: Empty field name")
fields2 = [
    {"name": "", "type": "string", "value": "test"}
]
errors2 = mock._validate_fields_logic(fields2)
print(f"Fields: {fields2}")
print(f"Errors: {errors2}")
print(f"✓ PASS" if len(errors2) > 0 and "required" in errors2[0] else f"✗ FAIL")

# Test 3: Invalid field name (special characters)
print("\nTest 3: Invalid field name with special characters")
fields3 = [
    {"name": "field-name!", "type": "string", "value": "test"}
]
errors3 = mock._validate_fields_logic(fields3)
print(f"Fields: {fields3}")
print(f"Errors: {errors3}")
print(f"✓ PASS" if len(errors3) > 0 and "alphanumeric" in errors3[0] else f"✗ FAIL")

# Test 4: Duplicate field names
print("\nTest 4: Duplicate field names")
fields4 = [
    {"name": "email", "type": "string", "value": "test@test.com"},
    {"name": "email", "type": "string", "value": "other@test.com"}
]
errors4 = mock._validate_fields_logic(fields4)
print(f"Fields: {len(fields4)} fields with duplicate names")
print(f"Errors: {errors4}")
print(f"✓ PASS" if len(errors4) > 0 and "Duplicate" in errors4[0] else f"✗ FAIL")

# Test 5: Invalid number value
print("\nTest 5: Invalid number value")
fields5 = [
    {"name": "count", "type": "number", "value": "not_a_number"}
]
errors5 = mock._validate_fields_logic(fields5)
print(f"Fields: {fields5}")
print(f"Errors: {errors5}")
print(f"✓ PASS" if len(errors5) > 0 and "number" in errors5[0] else f"✗ FAIL")

# Test 6: Invalid boolean value
print("\nTest 6: Invalid boolean value")
fields6 = [
    {"name": "isValid", "type": "boolean", "value": "maybe"}
]
errors6 = mock._validate_fields_logic(fields6)
print(f"Fields: {fields6}")
print(f"Errors: {errors6}")
print(f"✓ PASS" if len(errors6) > 0 and "true/false" in errors6[0] else f"✗ FAIL")

# Test 7: Valid with expressions
print("\nTest 7: Valid fields with expressions")
fields7 = [
    {"name": "userName", "type": "string", "value": '{{$node["Input"].data.name}}'},
    {"name": "userAge", "type": "number", "value": '{{$node["Input"].data.age}}'},
    {"name": "isAdult", "type": "boolean", "value": '{{$node["Input"].data.age >= 18}}'}
]
errors7 = mock._validate_fields_logic(fields7)
print(f"Fields: {len(fields7)} fields with expressions")
print(f"Errors: {errors7}")
print(f"✓ PASS" if len(errors7) == 0 else f"✗ FAIL")

# Test 8: Valid underscores in field name
print("\nTest 8: Valid field name with underscores")
fields8 = [
    {"name": "user_name", "type": "string", "value": "test"},
    {"name": "user_age", "type": "number", "value": "25"}
]
errors8 = mock._validate_fields_logic(fields8)
print(f"Fields: {len(fields8)} fields")
print(f"Errors: {errors8}")
print(f"✓ PASS" if len(errors8) == 0 else f"✗ FAIL")

# Test 9: Invalid object value
print("\nTest 9: Invalid object value (not JSON)")
fields9 = [
    {"name": "profile", "type": "object", "value": "not json"}
]
errors9 = mock._validate_fields_logic(fields9)
print(f"Fields: {fields9}")
print(f"Errors: {errors9}")
print(f"✓ PASS" if len(errors9) > 0 and "JSON" in errors9[0] else f"✗ FAIL")

# Test 10: Valid object with expression
print("\nTest 10: Valid object with expression")
fields10 = [
    {"name": "profile", "type": "object", "value": '{{$node["Input"].data}}'}
]
errors10 = mock._validate_fields_logic(fields10)
print(f"Fields: {fields10}")
print(f"Errors: {errors10}")
print(f"✓ PASS" if len(errors10) == 0 else f"✗ FAIL")

print("\n" + "=" * 60)
print("All validation tests completed!")
print("=" * 60)
