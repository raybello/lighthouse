"""
Test script to verify expression engine functionality
"""

from src.expression_engine import ExpressionEngine

# Create a test context simulating node outputs
context = {
    "Input": {
        "data": {
            "name": "John",
            "age": 30
        }
    },
    "Calculator": {
        "data": {
            "result": 35
        }
    }
}

# Initialize expression engine
engine = ExpressionEngine(context)

# Test cases
print("=" * 60)
print("Expression Engine Test Cases")
print("=" * 60)

# Test 1: Simple node reference
print("\nTest 1: Simple node reference")
expr1 = '{{$node["Input"].data.name}}'
result1 = engine.resolve(expr1)
print(f"Expression: {expr1}")
print(f"Result: {result1}")
print(f"Expected: John")
print(f"✓ PASS" if result1 == "John" else f"✗ FAIL")

# Test 2: Numeric calculation
print("\nTest 2: Arithmetic expression")
expr2 = '{{65 - $node["Input"].data.age}}'
result2 = engine.resolve(expr2)
print(f"Expression: {expr2}")
print(f"Result: {result2}")
print(f"Expected: 35")
print(f"✓ PASS" if result2 == 35 else f"✗ FAIL")

# Test 3: Comparison expression
print("\nTest 3: Boolean comparison")
expr3 = '{{$node["Input"].data.age >= 18}}'
result3 = engine.resolve(expr3)
print(f"Expression: {expr3}")
print(f"Result: {result3}")
print(f"Expected: True")
print(f"✓ PASS" if result3 == True else f"✗ FAIL")

# Test 4: Node data reference
print("\nTest 4: Node data reference")
expr4 = '{{$node["Input"].data}}'
result4 = engine.resolve(expr4)
print(f"Expression: {expr4}")
print(f"Result: {result4}")
print(f"Expected: {{'name': 'John', 'age': 30}}")
print(f"✓ PASS" if result4 == {"name": "John", "age": 30} else f"✗ FAIL")

# Test 5: Calculator result reference
print("\nTest 5: Calculator result reference")
expr5 = '{{$node["Calculator"].data.result}}'
result5 = engine.resolve(expr5)
print(f"Expression: {expr5}")
print(f"Result: {result5}")
print(f"Expected: 35")
print(f"✓ PASS" if result5 == 35 else f"✗ FAIL")

# Test 6: Mixed string with expression
print("\nTest 6: Mixed string with expression")
expr6 = 'Hello {{$node["Input"].data.name}}, you are {{$node["Input"].data.age}} years old'
result6 = engine.resolve(expr6)
print(f"Expression: {expr6}")
print(f"Result: {result6}")
expected6 = "Hello John, you are 30 years old"
print(f"Expected: {expected6}")
print(f"✓ PASS" if result6 == expected6 else f"✗ FAIL")

# Test 7: String without expression
print("\nTest 7: String without expression")
expr7 = "Just a plain string"
result7 = engine.resolve(expr7)
print(f"Expression: {expr7}")
print(f"Result: {result7}")
print(f"Expected: Just a plain string")
print(f"✓ PASS" if result7 == expr7 else f"✗ FAIL")

# Test 8: Complex arithmetic
print("\nTest 8: Complex arithmetic")
expr8 = '{{$node["Input"].data.age * 2 + 5}}'
result8 = engine.resolve(expr8)
print(f"Expression: {expr8}")
print(f"Result: {result8}")
print(f"Expected: 65")
print(f"✓ PASS" if result8 == 65 else f"✗ FAIL")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
