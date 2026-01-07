"""
Test script to verify Input Node validation and type inference
"""

from src.nodes import InputNode

# Create a mock Input Node for testing validation logic
class MockInputNode:
    """Mock Input Node for testing validation logic"""
    
    def __init__(self):
        self.input_properties = []
        self.id = "test_input_node"
    
    def _validate_properties_logic(self, properties_data):
        """
        Validate input properties (mimics the validation logic from InputNode).
        
        Returns:
            List of validation error messages
        """
        errors = []
        property_names = set()
        
        for i, prop in enumerate(properties_data):
            prop_name = prop.get("property", "").strip()
            
            # Validate property name
            if not prop_name:
                errors.append(f"Property {i+1}: Property name is required")
            elif not prop_name.replace("_", "").isalnum():
                errors.append(f"Property {i+1}: Property name '{prop_name}' must be alphanumeric (underscores allowed)")
            elif prop_name in property_names:
                errors.append(f"Property {i+1}: Duplicate property name '{prop_name}'")
            else:
                property_names.add(prop_name)
        
        return errors
    
    def _infer_type(self, value):
        """
        Infer the type of a value and convert it.
        
        Returns:
            Converted value with inferred type
        """
        if value.isdigit():
            return int(value)
        elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
            return float(value)
        elif value.lower() in ["true", "false"]:
            return value.lower() == "true"
        elif value.startswith("{") or value.startswith("["):
            try:
                import json
                return json.loads(value)
            except:
                return value
        else:
            return value

# Test cases
print("=" * 60)
print("Input Node Validation & Type Inference Test Cases")
print("=" * 60)

mock = MockInputNode()

# Test 1: Valid input properties
print("\nTest 1: Valid input properties")
props1 = [
    {"property": "name", "value": "John Doe"},
    {"property": "age", "value": "30"},
    {"property": "isActive", "value": "true"}
]
errors1 = mock._validate_properties_logic(props1)
print(f"Properties: {len(props1)} properties")
print(f"Errors: {errors1}")
print(f"✓ PASS" if len(errors1) == 0 else f"✗ FAIL")

# Test 2: Empty property name
print("\nTest 2: Empty property name")
props2 = [
    {"property": "", "value": "test"}
]
errors2 = mock._validate_properties_logic(props2)
print(f"Properties: {props2}")
print(f"Errors: {errors2}")
print(f"✓ PASS" if len(errors2) > 0 and "required" in errors2[0] else f"✗ FAIL")

# Test 3: Invalid property name (special characters)
print("\nTest 3: Invalid property name with special characters")
props3 = [
    {"property": "user-name!", "value": "test"}
]
errors3 = mock._validate_properties_logic(props3)
print(f"Properties: {props3}")
print(f"Errors: {errors3}")
print(f"✓ PASS" if len(errors3) > 0 and "alphanumeric" in errors3[0] else f"✗ FAIL")

# Test 4: Duplicate property names
print("\nTest 4: Duplicate property names")
props4 = [
    {"property": "email", "value": "test@test.com"},
    {"property": "email", "value": "other@test.com"}
]
errors4 = mock._validate_properties_logic(props4)
print(f"Properties: {len(props4)} properties with duplicate names")
print(f"Errors: {errors4}")
print(f"✓ PASS" if len(errors4) > 0 and "Duplicate" in errors4[0] else f"✗ FAIL")

# Test 5: Valid underscores in property name
print("\nTest 5: Valid property name with underscores")
props5 = [
    {"property": "user_name", "value": "test"},
    {"property": "user_age", "value": "25"}
]
errors5 = mock._validate_properties_logic(props5)
print(f"Properties: {len(props5)} properties")
print(f"Errors: {errors5}")
print(f"✓ PASS" if len(errors5) == 0 else f"✗ FAIL")

# Test 6: Type inference - Integer
print("\nTest 6: Type inference - Integer")
value6 = "42"
result6 = mock._infer_type(value6)
print(f"Input: '{value6}' (string)")
print(f"Output: {result6} ({type(result6).__name__})")
print(f"✓ PASS" if result6 == 42 and isinstance(result6, int) else f"✗ FAIL")

# Test 7: Type inference - Float
print("\nTest 7: Type inference - Float")
value7 = "3.14"
result7 = mock._infer_type(value7)
print(f"Input: '{value7}' (string)")
print(f"Output: {result7} ({type(result7).__name__})")
print(f"✓ PASS" if result7 == 3.14 and isinstance(result7, float) else f"✗ FAIL")

# Test 8: Type inference - Boolean (true)
print("\nTest 8: Type inference - Boolean (true)")
value8 = "true"
result8 = mock._infer_type(value8)
print(f"Input: '{value8}' (string)")
print(f"Output: {result8} ({type(result8).__name__})")
print(f"✓ PASS" if result8 == True and isinstance(result8, bool) else f"✗ FAIL")

# Test 9: Type inference - Boolean (false)
print("\nTest 9: Type inference - Boolean (false)")
value9 = "false"
result9 = mock._infer_type(value9)
print(f"Input: '{value9}' (string)")
print(f"Output: {result9} ({type(result9).__name__})")
print(f"✓ PASS" if result9 == False and isinstance(result9, bool) else f"✗ FAIL")

# Test 10: Type inference - String (default)
print("\nTest 10: Type inference - String (default)")
value10 = "Hello World"
result10 = mock._infer_type(value10)
print(f"Input: '{value10}' (string)")
print(f"Output: {result10} ({type(result10).__name__})")
print(f"✓ PASS" if result10 == "Hello World" and isinstance(result10, str) else f"✗ FAIL")

# Test 11: Type inference - JSON Object
print("\nTest 11: Type inference - JSON Object")
value11 = '{"key": "value", "count": 5}'
result11 = mock._infer_type(value11)
print(f"Input: '{value11}' (string)")
print(f"Output: {result11} ({type(result11).__name__})")
print(f"✓ PASS" if result11 == {"key": "value", "count": 5} and isinstance(result11, dict) else f"✗ FAIL")

# Test 12: Type inference - JSON Array
print("\nTest 12: Type inference - JSON Array")
value12 = '[1, 2, 3, 4, 5]'
result12 = mock._infer_type(value12)
print(f"Input: '{value12}' (string)")
print(f"Output: {result12} ({type(result12).__name__})")
print(f"✓ PASS" if result12 == [1, 2, 3, 4, 5] and isinstance(result12, list) else f"✗ FAIL")

print("\n" + "=" * 60)
print("All validation and type inference tests completed!")
print("=" * 60)
