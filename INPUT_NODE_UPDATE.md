# Input Node Update - Enhanced UI and Type Inference

## Summary

The Input Node has been completely redesigned with a better user interface using individual property/value fields, along with validation and automatic type inference.

## Key Changes

### 1. **New UI Design**

**Before:** Single JSON text area
```json
{
  "name": "John",
  "age": 30
}
```

**After:** Individual property/value pairs
- **Property Name** text input (250px) - The property key
- **Value** text input (280px) - The property value
- **Delete** button (X) for each property
- **Add Property** button at the bottom

### 2. **Validation Features**

The Input Node now validates all properties before saving:

#### Property Name Validation
- ✅ Required (cannot be empty)
- ✅ Must be alphanumeric (underscores allowed)
- ✅ No duplicate property names
- ❌ No special characters like `-`, `!`, `@`, etc.

**Examples:**
- ✅ `name`, `user_name`, `age`, `isActive`
- ❌ `user-name`, `email!`, `first name` (with space)

### 3. **Automatic Type Inference**

The Input Node automatically infers the correct type from string values:

| Input Value | Inferred Type | Output Value | Example |
|-------------|---------------|--------------|---------|
| `"42"` | Integer | `42` | Age, count |
| `"3.14"` | Float | `3.14` | Price, temperature |
| `"true"` | Boolean | `true` | Active status |
| `"false"` | Boolean | `false` | Disabled flag |
| `"Hello"` | String | `"Hello"` | Name, description |
| `'{"key":"value"}'` | Object | `{key: "value"}` | Nested data |
| `'[1,2,3]'` | Array | `[1, 2, 3]` | List of items |

#### Type Inference Rules

1. **Integer Detection**
   - If value contains only digits: `"123"` → `123`
   
2. **Float Detection**
   - If value contains one decimal point: `"12.5"` → `12.5`
   
3. **Boolean Detection**
   - Case-insensitive: `"true"`, `"True"`, `"TRUE"` → `true`
   - Case-insensitive: `"false"`, `"False"`, `"FALSE"` → `false`
   
4. **JSON Object/Array Detection**
   - Starts with `{` → Parse as JSON object
   - Starts with `[` → Parse as JSON array
   - If parsing fails, keep as string
   
5. **Default String**
   - Everything else remains a string

### 4. **Error Display**

#### In Inspector Window
Validation errors appear in red text above the Save/Cancel buttons:
```
Validation Errors:
Property 1: Property name is required
Property 2: Duplicate property name 'email'
Property 3: Property name 'user-name!' must be alphanumeric (underscores allowed)
```

#### On Node Status
When validation fails or execution errors occur:
- Status text displays error in **red color**
- Examples:
  - `"Input: No properties defined"` (red)
  - `"Input Error: JSON parse error"` (red)
- Success shows in **blue color**:
  - `"Input: 3 property(ies)"` (blue)

### 5. **Dynamic Property Management**

- **Add Property**: Click "+ Add Property" button to add a new empty property
- **Delete Property**: Click "X" button next to any property to remove it
- **Reorder**: Properties appear in the order they were added
- **Live Updates**: Property list updates immediately after add/delete

### 6. **Enhanced User Experience**

#### Hints and Placeholders
- Property Name input: Shows "Property Name" as placeholder
- Value input: Shows "Value" as hint

#### Scrollable Container
- Inspector has a scrollable child window (350px height)
- Can handle many properties without window overflow

#### Visual Feedback
- Validation errors prevent saving (stay in inspector)
- Console logs all validation errors with color coding
- Node status updates immediately on successful save

## Example Usage

### Creating Input Data with Auto Type Inference

1. Open Input Node inspector
2. Configure properties:

| Property Name | Value | Inferred Type |
|---------------|-------|---------------|
| name | John | string |
| age | 30 | integer |
| height | 5.9 | float |
| isActive | true | boolean |
| hobbies | ["reading", "coding"] | array |
| address | {"city": "NYC", "zip": "10001"} | object |

3. Click Save
4. If validation passes:
   - Inspector closes
   - Node status shows "Input: 6 property(ies)" in blue
   - Console logs: "[cyan]Saved input node: xxxxxxxx[/cyan]"
   - Execution output:
   ```json
   {
     "data": {
       "name": "John",
       "age": 30,
       "height": 5.9,
       "isActive": true,
       "hobbies": ["reading", "coding"],
       "address": {"city": "NYC", "zip": "10001"}
     }
   }
   ```

5. If validation fails:
   - Inspector stays open
   - Errors shown in red text
   - Console logs: "[red]Input validation failed:[/red]"

## Comparison: Before vs After

### Before (JSON Text Area)
```
Pros:
- Familiar JSON format
- Can paste JSON directly

Cons:
- Easy to make syntax errors (missing comma, quote)
- No validation until execution
- No type safety
- Hard to add/remove properties
- Requires JSON knowledge
```

### After (Property/Value Fields)
```
Pros:
- No JSON syntax errors possible
- Validation before saving
- Automatic type inference
- Easy add/remove with buttons
- Visual feedback for errors
- No JSON knowledge required
- Clean, intuitive interface

Cons:
- Can't paste JSON directly (but could add import feature)
```

## Testing

All 12 validation and type inference tests pass:

**Validation Tests (5):**
- ✅ Valid properties accepted
- ✅ Empty names rejected
- ✅ Invalid characters rejected
- ✅ Duplicates detected
- ✅ Underscores allowed

**Type Inference Tests (7):**
- ✅ Integer detection (`"42"` → `42`)
- ✅ Float detection (`"3.14"` → `3.14`)
- ✅ Boolean true detection (`"true"` → `true`)
- ✅ Boolean false detection (`"false"` → `false`)
- ✅ String default (`"Hello"` → `"Hello"`)
- ✅ JSON object parsing (`'{"key":"value"}'` → `{key: "value"}`)
- ✅ JSON array parsing (`'[1,2,3]'` → `[1, 2, 3]`)

## Technical Implementation

### Data Storage
Properties stored as JSON array in state:
```json
[
  {"property": "name", "value": "John"},
  {"property": "age", "value": "30"}
]
```

### Validation Method
```python
def _validate_properties(self) -> List[str]:
    """Validate all input properties and return error list"""
    errors = []
    property_names = set()
    
    for i, prop in enumerate(self.input_properties):
        prop_name = prop.get("property", "").strip()
        
        # Check required
        if not prop_name:
            errors.append(f"Property {i+1}: Property name is required")
        # Check alphanumeric
        elif not prop_name.replace("_", "").isalnum():
            errors.append(f"Property {i+1}: Property name '{prop_name}' must be alphanumeric")
        # Check duplicates
        elif prop_name in property_names:
            errors.append(f"Property {i+1}: Duplicate property name '{prop_name}'")
        else:
            property_names.add(prop_name)
    
    return errors
```

### Type Inference Method
```python
# Integer detection
if value.isdigit():
    return int(value)

# Float detection
elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
    return float(value)

# Boolean detection
elif value.lower() in ["true", "false"]:
    return value.lower() == "true"

# JSON object/array detection
elif value.startswith("{") or value.startswith("["):
    try:
        return json.loads(value)
    except:
        return value

# Default to string
else:
    return value
```

### Error Handling
```python
if errors:
    # Show in inspector
    dpg.set_value(f"{self.id}_validation_errors", error_text)
    # Log to console
    console.print(f"[red]Input validation failed:[/red]")
    # Don't close inspector
    return
```

## Benefits

1. **Better UX**: Individual fields easier than JSON editing
2. **Validation**: Catches errors before execution
3. **Type Safety**: Automatic type inference prevents type errors
4. **Visual Feedback**: Clear error messages guide users
5. **Flexibility**: Supports all JSON data types
6. **Maintainability**: Easier to modify properties
7. **Beginner Friendly**: No JSON syntax knowledge required

## Workflow Example

Using the enhanced Input Node in a workflow:

```
1. Input Node → 
   Properties:
   - name: "John"
   - age: "30"           (auto-converts to 30)
   - height: "5.9"       (auto-converts to 5.9)
   - isActive: "true"    (auto-converts to true)
   
   Output: {"data": {"name": "John", "age": 30, "height": 5.9, "isActive": true}}

2. Calculator Node →
   Field A: {{$node["Input"].data.age}}     → 30
   Field B: 5
   Operation: +
   
   Output: {"data": {"result": 35}}

3. Form Node →
   Fields:
   - fullName: {{$node["Input"].data.name}}         → "John"
   - yearsToRetirement: {{65 - $node["Input"].data.age}}  → 35
   - isAdult: {{$node["Input"].data.age >= 18}}     → true
   
   Output: {"data": {"fullName": "John", "yearsToRetirement": 35, "isAdult": true}}
```

## Future Enhancements

Possible improvements:
- [ ] Import from JSON (paste JSON to auto-populate fields)
- [ ] Export to JSON (copy current properties as JSON)
- [ ] Property reordering (drag and drop)
- [ ] Type dropdown (manual type selection override)
- [ ] Value templates/examples per type
- [ ] Nested object editor (expandable sub-properties)
- [ ] Array item editor (manage array elements visually)
