use archive/demo.py to check how to implement gui

## 📋 Product Requirements

### 1. Dynamic Node Connection System

#### 1.1 Node Output-to-Input Passing
- **Requirement**: Each node must be able to pass its output data to the input of connected downstream nodes
- **Behavior**: 
  - When nodes are connected via edges in the UI, output data flows automatically to connected nodes
  - Each node should have a standardized output format that can be accessed by downstream nodes
  - Nodes should be able to access outputs from multiple upstream nodes
  - The system should maintain a data context that tracks all node outputs in the execution path

#### 1.2 Node Execution Order
- Nodes should execute in topological order based on their connections
- Upstream nodes must complete execution before downstream nodes begin
- Support for parallel execution of independent node branches

### 2. Dynamic Expression Syntax

#### 2.1 Double Curly Brace Syntax
- **Syntax**: `{{expression}}` similar to N8n
- **Purpose**: Allow dynamic value insertion and JavaScript-like expressions in node fields
- **Examples**:
  - `{{$node["Node1"].data.result}}` - Access output from a specific node
  - `{{$node["PreviousNode"].data.name}}` - Access nested properties
  - `{{$node["Input"].data.value * 2}}` - Perform calculations
  - `{{$node["API"].data.items[0].id}}` - Access array elements

#### 2.2 Expression Resolution
- Expressions should be evaluated at runtime when the node executes
- Support for:
  - Variable references from previous nodes
  - Basic arithmetic operations (+, -, *, /, %)
  - String concatenation
  - Object property access (dot notation and bracket notation)
  - Array indexing
  - Basic JavaScript-like expressions

#### 2.3 Context Variables
- `$node["NodeName"]` - Access output from any node in the workflow by name
- `$node["NodeName"].data` - Access the data output from a node
- Support for accessing nested properties and array elements

### 3. Form Node

#### 3.1 Overview
- **Purpose**: Create dynamic forms that accept inputs from previous nodes using expression syntax
- **Output**: Returns a structured object with form field values as attributes

#### 3.2 Field Types
The Form node should support the following field types:

**String Field**
- Input type: text
- Supports dynamic expressions using `{{}}` syntax
- Example: `{{$node["Input"].data.username}}`

**Number Field**
- Input type: numeric
- Supports dynamic expressions that evaluate to numbers
- Example: `{{$node["Calculator"].data.result}}`

**Boolean Field**
- Input type: checkbox/toggle
- Supports dynamic expressions that evaluate to true/false
- Example: `{{$node["Validator"].data.isValid}}`

**Object Field**
- Input type: JSON or key-value pairs
- Supports dynamic expressions for entire objects or nested properties
- Example: `{{$node["API"].data.response}}`

#### 3.3 Form Configuration
- Each field should have:
  - **Field Name**: Identifier for the output object attribute
  - **Field Type**: string, number, boolean, object
  - **Default Value**: Optional default value (supports expressions)

#### 3.4 Form Output Structure
The Form node outputs an object where each configured field becomes an attribute:

```json
{
  "data": {
    "fieldName1": "evaluated_value",
    "fieldName2": 42,
    "fieldName3": true,
    "fieldName4": {
      "nested": "object"
    }
  }
}
```

#### 3.5 Dynamic Form Population
- Form fields should be editable in the UI
- When a field contains `{{}}` expressions:
  - Display the expression in the input field
  - Evaluate the expression at runtime
  - Show validation errors if expression cannot be resolved
- Support for adding/removing form fields dynamically in the UI

### 4. UI/UX Requirements

#### 4.1 Node Field Editing
- All node input fields should support expression syntax
- Visual indicators for fields containing expressions:
  - Syntax highlighting for `{{}}` expressions
  - Autocomplete for available node references
  - Validation feedback for invalid expressions

#### 4.2 Form Node UI
- Interface to add/remove form fields
- Dropdown to select field type (string, number, boolean, object)
- Input fields for field name, label, and default value
- Support for dynamic expression editing with syntax highlighting

#### 4.3 Expression Editor
- Consider implementing an expression builder/editor tab similar to N8n:
  - Dropdown showing available upstream nodes
  - Tree view of node output structure
  - Click/Drag to insert references into expressions

#### 4.4 Execution Visualization
- Show data flow between nodes during execution
- Display resolved values for expressions
- Error highlighting when expressions fail to resolve

### 5. Implementation Architecture

#### 5.1 Expression Engine
- Create an expression parser to handle `{{}}` syntax
- Implement expression evaluator with access to node context
- Handle errors gracefully with meaningful error messages

#### 5.2 Node Context Manager
- Maintain execution context with all node outputs
- Provide lookup mechanism for `$node["NodeName"]` references
- Clear context between workflow executions

#### 5.3 Form Node Implementation
- Extend base Node class with Form-specific functionality
- Store field configurations as node parameters
- Evaluate all field expressions during execution
- Output structured object with evaluated values

#### 5.4 Data Flow System
- Implement topological sorting for node execution order
- Pass node outputs through context to downstream nodes
- Support for accessing outputs from any node in the workflow path

### 6. Example Workflow

**Node 1: Input Node**
- Output: `{"data": {"name": "John", "age": 30}}`

**Node 2: Calculator Node** **Create This**
- FieldA: `{{$node["Input"].data.age}}`
- FieldB: `5`
- Operation: `+`
- Output: `{"data": {"result": 35}}`

**Node 3: Form Node** **Create This**
- Fields (With text fields to specify property name, dropdown to select type, and text field to hold expression or literal value):
  - `fullName` (string): `{{$node["Input"].data.name}}`
  - `yearsToRetirement` (number): `{{65 - $node["Input"].data.age}}`
  - `isAdult` (boolean): `{{$node["Input"].data.age >= 18}}`
  - `profile` (object): `{{$node["Input"].data}}`
- Output:
```json
{
  "data": {
    "fullName": "John",
    "yearsToRetirement": 35,
    "isAdult": true,
    "profile": {"name": "John", "age": 30}
  }
}
```

## 🔄 Releasing New Versions

```bash
# Create versioned release
pyinstaller --onefile main.py --name lighthouse --add-data "fonts:fonts"
git tag -a v[version] -F CHANGELOG.md
git push origin v[version]
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [DearPyGui](https://github.com/hoffstadt/DearPyGui)
- Inspired by workflow automation platforms like [N8n](https://n8n.io/)
- Thanks to the open-source community for contributions and feedback