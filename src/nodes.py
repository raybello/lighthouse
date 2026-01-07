
from .node_base import *


# ============================================================================
# Enums
# ============================================================================

class HTTPRequestType(Enum):
    """
    Supported HTTP request methods.

    These values are used in the HTTPRequestNode to configure
    the type of HTTP request to be made.
    """

    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"
    DELETE = "DELETE"


class OperationType(Enum):
    """
    Supported arithmetic operations for Calculator Node.
    """
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"


class FieldType(Enum):
    """
    Supported field types for Form Node.
    """
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"


# ============================================================================
# Node Implementations
# ============================================================================


class ManualTriggerNode(NodeBase):
    """
    Manual trigger node for initiating workflows.

    This node has no inputs and serves as a starting point for workflows.
    It can be executed manually to trigger downstream nodes.
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb, log_cb=None) -> None:
        """
        Initialize a Manual Trigger node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
            log_cb: Callback for logging during execution
        """
        super().__init__(name, parent, exec_cb, delete_cb, log_cb)

        # Define node fields
        self.fields = {
            "status": {
                "value": "PENDING",
                "type": str,
                "label": "Status",
            },
        }

        # Initialize the node UI and configuration
        self.node_ui(has_inputs=False, has_config=False)
        self.node_configure()
        self.setup_node_inspector()

    def save(self) -> None:
        """Save method (no-op for trigger nodes with no config)."""
        pass

    def execute(self) -> Dict[str, Any]:
        """
        Execute the manual trigger.

        Returns:
            Empty data dict
        """
        return {"data": {}}


class InputNode(NodeBase):
    """
    Input node for providing static data to workflows.

    This node allows you to define data that can be referenced by
    downstream nodes using expressions like {{$node["Input"].data.name}}

    Uses individual property/value fields for better UX.
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb, log_cb=None) -> None:
        """
        Initialize an Input node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
            log_cb: Callback for logging during execution
        """
        super().__init__(name, parent, exec_cb, delete_cb, log_cb)
        
        # Store input properties as a list of dicts
        self.input_properties = [
            {"property": "name", "value": "John"},
            {"property": "age", "value": "30"}
        ]
        
        # Track validation errors
        self.validation_errors = []
        
        # Define node fields (we'll store the properties as JSON internally)
        self.fields = {
            "input_properties_json": {
                "value": self._properties_to_json(),
                "type": str,
                "label": "Input Properties (Internal)",
            },
        }
        
        # Initialize the node UI and configuration
        self.node_ui(has_inputs=False)
        self.node_configure()
        # Override the default inspector setup
        self.setup_input_inspector()
    
    def _properties_to_json(self) -> str:
        """Convert input properties list to JSON string."""
        import json
        return json.dumps(self.input_properties)
    
    def _json_to_properties(self, json_str: str) -> None:
        """Parse JSON string to input properties list."""
        import json
        try:
            self.input_properties = json.loads(json_str)
        except:
            self.input_properties = []
    
    def setup_input_inspector(self) -> None:
        """
        Create a custom inspector window for the input node with dynamic property management.
        """
        with dpg.window(
            label=f"{self.name} Inspector",
            modal=True,
            show=False,
            tag=f"{self.id}_inspector",
            no_title_bar=True,
            pos=self.pos,
            width=600,
            height=500,
        ):
            # Header
            dpg.add_text(f"{self.name} Configuration", color=(120, 180, 255))
            dpg.add_text("Define properties that will be available as data", color=(150, 150, 155))
            dpg.add_separator()
            dpg.add_spacer(height=5)
            
            # Scrollable container for properties
            with dpg.child_window(
                tag=f"{self.id}_properties_container",
                height=350,
                border=True
            ):
                self._render_properties()
            
            dpg.add_spacer(height=5)
            
            # Add property button
            dpg.add_button(
                label="+ Add Property",
                callback=lambda: self._add_property(),
                width=580,
                tag=f"{self.id}_add_property_btn"
            )
            
            dpg.add_spacer(height=5)
            
            # Validation errors display
            dpg.add_text(
                "",
                tag=f"{self.id}_validation_errors",
                color=(255, 100, 100),
                wrap=580
            )
            
            # Footer buttons
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=lambda: self.save(), width=280)
                dpg.add_button(
                    label="Cancel", callback=lambda: self.close_inspector(), width=280
                )
        
        # Also setup the rename popup
        with dpg.window(
            label=f"{self.name} Rename",
            popup=True,
            show=False,
            tag=f"{self.id}_rename_popup",
            height=30,
            no_title_bar=True,
            pos=self.pos,
        ):
            dpg.add_input_text(
                default_value=self.name,
                tag=f"{self.id}_rename_text",
                label="Enter New Name",
            )
            dpg.add_button(
                label="Save",
                tag=f"{self.id}_rename_save_btn",
                callback=lambda: self.close_rename_popup(),
            )
    
    def _render_properties(self) -> None:
        """Render all input properties in the inspector."""
        # Clear existing properties
        children = dpg.get_item_children(f"{self.id}_properties_container", slot=1)
        if children:
            for child in children:
                if dpg.does_item_exist(child):
                    dpg.delete_item(child)
        
        # Render each property
        for i, prop in enumerate(self.input_properties):
            self._render_property(i, prop)
    
    def _render_property(self, index: int, prop: Dict[str, str]) -> None:
        """
        Render a single property row.
        
        Args:
            index: Index of the property in the input_properties list
            prop: Property dictionary with property name and value
        """
        property_group_tag = f"{self.id}_property_{index}"
        
        with dpg.group(
            tag=property_group_tag,
            parent=f"{self.id}_properties_container",
            horizontal=False
        ):
            # Property row with inputs
            with dpg.group(horizontal=True):
                # Property name input
                dpg.add_input_text(
                    default_value=prop.get("property", ""),
                    hint="Property Name",
                    width=250,
                    tag=f"{self.id}_property_{index}_name",
                    label=""
                )
                
                # Property value input
                dpg.add_input_text(
                    default_value=prop.get("value", ""),
                    hint="Value",
                    width=280,
                    tag=f"{self.id}_property_{index}_value",
                    label=""
                )
                
                # Delete button
                dpg.add_button(
                    label="X",
                    callback=lambda s, a, u: self._delete_property(u),
                    user_data=index,
                    width=30,
                    tag=f"{self.id}_property_{index}_delete"
                )
            
            dpg.add_spacer(height=5)
    
    def _add_property(self) -> None:
        """Add a new property to the input."""
        self.input_properties.append({"property": "", "value": ""})
        self._render_properties()
    
    def _delete_property(self, index: int) -> None:
        """
        Delete a property from the input.
        
        Args:
            index: Index of the property to delete
        """
        if 0 <= index < len(self.input_properties):
            self.input_properties.pop(index)
            self._render_properties()
    
    def _validate_properties(self) -> List[str]:
        """
        Validate all input properties.
        
        Returns:
            List of validation error messages
        """
        errors = []
        property_names = set()
        
        for i, prop in enumerate(self.input_properties):
            # Get current values from UI
            prop_name = dpg.get_value(f"{self.id}_property_{i}_name").strip()
            prop_value = dpg.get_value(f"{self.id}_property_{i}_value")
            
            # Validate property name
            if not prop_name:
                errors.append(f"Property {i+1}: Property name is required")
            elif not prop_name.replace("_", "").isalnum():
                errors.append(f"Property {i+1}: Property name '{prop_name}' must be alphanumeric (underscores allowed)")
            elif prop_name in property_names:
                errors.append(f"Property {i+1}: Duplicate property name '{prop_name}'")
            else:
                property_names.add(prop_name)
            
            # Value can be anything (no validation needed for input data)
        
        return errors
    
    def save(self) -> None:
        """
        Save changes from inspector inputs back to node state with validation.
        """
        # Collect property data from UI
        updated_properties = []
        for i in range(len(self.input_properties)):
            property_data = {
                "property": dpg.get_value(f"{self.id}_property_{i}_name").strip(),
                "value": dpg.get_value(f"{self.id}_property_{i}_value")
            }
            updated_properties.append(property_data)
        
        # Update input properties
        self.input_properties = updated_properties
        
        # Validate properties
        errors = self._validate_properties()
        
        if errors:
            # Show validation errors
            error_text = "Validation Errors:\n" + "\n".join(errors)
            dpg.set_value(f"{self.id}_validation_errors", error_text)
            console.print(f"[red]Input validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]- {error}[/red]")
            return
        
        # Clear validation errors
        dpg.set_value(f"{self.id}_validation_errors", "")
        self.validation_errors = []
        
        # Update state
        self.state["input_properties_json"] = self._properties_to_json()
        
        # Update the status display on the node
        property_count = len(self.input_properties)
        if property_count > 0:
            status_text = f"Input: {property_count} property(ies)"
            dpg.set_value(f"{self.id}_state", value=status_text)
            dpg.configure_item(f"{self.id}_state", color=(86, 145, 193))
        else:
            status_text = "Input: No properties"
            dpg.set_value(f"{self.id}_state", value=status_text)
            dpg.configure_item(f"{self.id}_state", color=(86, 145, 193))
        
        # Debug output
        console.print(f"[cyan]Saved input node: {self.id[-8:]}[/cyan]")
        console.print(f"  Properties: {self.input_properties}")
        
        # Close the inspector
        self.close_inspector()
    
    def node_configure(self) -> None:
        """
        Initialize node state from field definitions.
        Override to load input properties from JSON.
        """
        # Create state dictionary from field values
        state = {key: field["value"] for key, field in self.fields.items()}
        
        # Preserve existing input connection if present
        if "input" in self.state:
            state["input"] = self.state["input"]
        else:
            state["input"] = []
        
        self.state = state
        
        # Load input properties from state if available
        if "input_properties_json" in self.state:
            self._json_to_properties(self.state["input_properties_json"])
        
        # Debug output
        console.print(f"[green]Configured node: {self.name}[/green]")
        console.print(f"  Input properties: {len(self.input_properties)} property(ies)")
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute the input node - build and return the data object from properties.
        
        Returns:
            Dictionary with input data
        """
        try:
            # Parse the input properties
            self._json_to_properties(self.state.get("input_properties_json", "[]"))
            
            # Validate before execution
            if not self.input_properties:
                # Update node status to show error
                dpg.set_value(f"{self.id}_state", value="Input: No properties defined")
                dpg.configure_item(f"{self.id}_state", color=(255, 100, 100))
                return {"data": {}}
            
            # Build the output data from properties
            output_data = {}
            
            for prop in self.input_properties:
                prop_name = prop.get("property", "")
                prop_value = prop.get("value", "")
                
                if not prop_name:
                    continue
                
                # Try to infer the type from the value
                # If it looks like a number, convert it
                if prop_value.isdigit():
                    output_data[prop_name] = int(prop_value)
                elif prop_value.replace(".", "", 1).isdigit() and prop_value.count(".") == 1:
                    output_data[prop_name] = float(prop_value)
                elif prop_value.lower() in ["true", "false"]:
                    output_data[prop_name] = prop_value.lower() == "true"
                elif prop_value.startswith("{") or prop_value.startswith("["):
                    # Try to parse as JSON
                    try:
                        import json
                        output_data[prop_name] = json.loads(prop_value)
                    except:
                        output_data[prop_name] = prop_value
                else:
                    # Default to string
                    output_data[prop_name] = prop_value
            
            console.print(f"[green]Input data: {output_data}[/green]")
            
            # Update node status to success
            dpg.set_value(f"{self.id}_state", value=f"Input: {len(output_data)} property(ies)")
            dpg.configure_item(f"{self.id}_state", color=(86, 145, 193))
            
            return {"data": output_data}
        
        except Exception as e:
            console.print(f"[red]Input node error: {e}[/red]")
            # Update node status to show error
            dpg.set_value(f"{self.id}_state", value=f"Input Error: {str(e)[:30]}")
            dpg.configure_item(f"{self.id}_state", color=(255, 100, 100))
            return {"data": {"error": str(e)}}


class HTTPRequestNode(NodeBase):
    """
    Node for configuring and executing HTTP requests.

    Supports various HTTP methods (GET, POST, PUT, PATCH, DELETE) with
    configurable URL, request body, and timeout parameters.

    Fields:
        url: Target URL for the HTTP request
        type: HTTP method (GET, POST, etc.)
        body: Request body content (JSON format)
        timeout: Request timeout in seconds
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb, log_cb=None) -> None:
        """
        Initialize an HTTP Request node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
            log_cb: Callback for logging during execution
        """
        super().__init__(name, parent, exec_cb, delete_cb, log_cb)

        # Define the fields for this node type
        self.fields = {
            "url": {
                "value": "https://api.example.com/endpoint",
                "type": str,
                "label": "URL",
            },
            "type": {
                "value": HTTPRequestType.POST.value,
                "type": HTTPRequestType,
                "label": "Method",
            },
            "body": {
                "value": "{}",
                "type": LongString,
                "label": "Request Body",
            },
            "timeout": {
                "value": 30,
                "type": int,
                "label": "Timeout (seconds)",
            },
        }

        # Initialize the node UI and configuration
        self.node_ui()
        self.node_configure()
        self.setup_node_inspector()

    def save(self) -> None:
        """
        Save changes from inspector inputs back to node state.

        Updates the state dictionary with values from UI inputs
        and refreshes the status display on the node.
        """
        # Update state from UI input values
        for field_key in self.fields.keys():
            input_tag = f"{self.id}_{field_key}"
            self.state[field_key] = dpg.get_value(item=input_tag)

        # Update the status display on the node
        status_text = f"{self.state['type']}\n{self.state['url']}"
        dpg.set_value(f"{self.id}_state", value=status_text)

        # Debug output
        console.print(f"[cyan]Saved node: {self.id[-8:]}[/cyan]")
        console.print(f"  State: {self.state}")

        # Close the inspector
        self.close_inspector()

    def execute(self) -> Dict[str, Any]:
        """
        Execute the HTTP request.

        Returns:
            Dictionary with response data including status_code, headers, body, url
        """
        import requests
        import json as json_module

        url = self.state.get("url", "")
        method = self.state.get("type", "GET")
        body = self.state.get("body", "{}")
        timeout = self.state.get("timeout", 30)

        self.log("INFO", f"Starting {method} request to {url}")

        try:
            # Parse body as JSON for POST/PUT/PATCH
            json_body = None
            if method in ["POST", "PUT", "PATCH"] and body and body.strip() != "{}":
                try:
                    json_body = json_module.loads(body)
                    self.log("DEBUG", f"Request body: {json_body}")
                except json_module.JSONDecodeError as e:
                    self.log("WARN", f"Invalid JSON body, sending as raw: {e}")

            response = requests.request(
                method=method,
                url=url,
                json=json_body,
                timeout=timeout
            )

            self.log("INFO", f"Response status: {response.status_code}")

            # Try to parse JSON response
            try:
                response_data = response.json()
            except:
                response_data = response.text
                self.log("DEBUG", "Response is not JSON, returning as text")

            return {
                "data": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_data,
                    "url": response.url
                }
            }

        except requests.Timeout:
            self.log("ERROR", f"Request timed out after {timeout}s")
            return {"data": {"error": "Timeout", "status_code": None, "body": None}}
        except requests.ConnectionError as e:
            self.log("ERROR", f"Connection error: {str(e)}")
            return {"data": {"error": f"Connection error: {str(e)}", "status_code": None, "body": None}}
        except Exception as e:
            self.log("ERROR", f"Request failed: {str(e)}")
            return {"data": {"error": str(e), "status_code": None, "body": None}}


class ExecuteCommandNode(NodeBase):
    """
    Node for executing shell commands.

    Executes system commands and optionally logs output to a file.
    Useful for automation tasks and system integrations.

    Fields:
        command: Shell command to execute
        log_file: Path to log file for command output
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb, log_cb=None) -> None:
        """
        Initialize an Execute Command node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
            log_cb: Callback for logging during execution
        """
        super().__init__(name, parent, exec_cb, delete_cb, log_cb)

        # Define node fields with default command
        self.fields = {
            "command": {
                "value": "echo Hello World",
                "type": str,
                "label": "Execute Command",
            },
            "log_file": {
                "value": f"{self.id[-8:]}.log",
                "type": str,
                "label": "Log-file Path",
            },
        }

        # Initialize the node UI and configuration
        self.node_ui()
        self.node_configure()
        self.setup_node_inspector()

    def save(self) -> None:
        """
        Save changes from inspector inputs back to node state.

        Updates command and log file path from UI inputs.
        """
        # Update state from UI input values
        for field_key in self.fields.keys():
            input_tag = f"{self.id}_{field_key}"
            self.state[field_key] = dpg.get_value(item=input_tag)

        # Update the status display on the node
        status_text = f"{self.state['command']}\n{self.state['log_file']}"
        dpg.set_value(f"{self.id}_state", value=status_text)

        # Debug output
        console.print(f"[cyan]Saved node: {self.id[-8:]}[/cyan]")
        console.print(f"  State: {self.state}")

        # Close the inspector
        self.close_inspector()

    def execute(self) -> Dict[str, Any]:
        """
        Execute the shell command.

        Returns:
            Dictionary with stdout, stderr, exit_code, and success status
        """
        import subprocess

        command = self.state.get("command", "")
        log_file = self.state.get("log_file", "")

        self.log("INFO", f"Executing command: {command}")

        try:
            # Run command with shell=True for full shell support
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )

            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode

            self.log("INFO", f"Command completed with exit code: {exit_code}")
            if stdout:
                # Log first 500 chars of stdout
                self.log("DEBUG", f"stdout: {stdout[:500]}")
            if stderr:
                # Log first 500 chars of stderr
                self.log("WARN", f"stderr: {stderr[:500]}")

            # Optionally write to log file
            if log_file:
                try:
                    with open(log_file, 'w') as f:
                        f.write(f"=== COMMAND ===\n{command}\n\n")
                        f.write(f"=== EXIT CODE ===\n{exit_code}\n\n")
                        f.write(f"=== STDOUT ===\n{stdout}\n\n")
                        f.write(f"=== STDERR ===\n{stderr}\n")
                    self.log("INFO", f"Output saved to: {log_file}")
                except Exception as e:
                    self.log("WARN", f"Failed to write log file: {e}")

            return {
                "data": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "success": exit_code == 0
                }
            }

        except subprocess.TimeoutExpired:
            self.log("ERROR", "Command timed out after 60 seconds")
            return {"data": {"error": "Timeout", "exit_code": -1, "success": False, "stdout": "", "stderr": ""}}
        except Exception as e:
            self.log("ERROR", f"Command failed: {str(e)}")
            return {"data": {"error": str(e), "exit_code": -1, "success": False, "stdout": "", "stderr": ""}}


class CalculatorNode(NodeBase):
    """
    Node for performing arithmetic calculations with expression support.

    Supports dynamic input from previous nodes using {{}} expression syntax.
    Can perform basic arithmetic operations: +, -, *, /, %

    Fields:
        field_a: First operand (supports expressions)
        field_b: Second operand (supports expressions)
        operation: Arithmetic operation to perform
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb, log_cb=None) -> None:
        """
        Initialize a Calculator node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
            log_cb: Callback for logging during execution
        """
        super().__init__(name, parent, exec_cb, delete_cb, log_cb)
        
        # Define node fields
        self.fields = {
            "field_a": {
                "value": "10",
                "type": str,
                "label": "Field A",
            },
            "field_b": {
                "value": "5",
                "type": str,
                "label": "Field B",
            },
            "operation": {
                "value": OperationType.ADD.value,
                "type": OperationType,
                "label": "Operation",
            },
        }
        
        # Initialize the node UI and configuration
        self.node_ui()
        self.node_configure()
        self.setup_node_inspector()
    
    def save(self) -> None:
        """
        Save changes from inspector inputs back to node state.
        """
        # Update state from UI input values
        for field_key in self.fields.keys():
            input_tag = f"{self.id}_{field_key}"
            self.state[field_key] = dpg.get_value(item=input_tag)
        
        # Update the status display on the node
        status_text = f"{self.state['field_a']} {self.state['operation']} {self.state['field_b']}"
        dpg.set_value(f"{self.id}_state", value=status_text)
        
        # Debug output
        console.print(f"[cyan]Saved node: {self.id[-8:]}[/cyan]")
        console.print(f"  State: {self.state}")
        
        # Close the inspector
        self.close_inspector()
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute the calculation.
        
        Returns:
            Dictionary with calculation result: {"data": {"result": value}}
        """
        try:
            # Get the values (may contain expressions)
            field_a_raw = self.state.get("field_a", "0")
            field_b_raw = self.state.get("field_b", "0")
            operation = self.state.get("operation", "+")
            
            # Convert to numbers - if they're already numbers, use them directly
            # If they're strings, try to parse them
            if isinstance(field_a_raw, str):
                field_a = float(field_a_raw) if '.' in field_a_raw else int(field_a_raw)
            else:
                field_a = field_a_raw
            
            if isinstance(field_b_raw, str):
                field_b = float(field_b_raw) if '.' in field_b_raw else int(field_b_raw)
            else:
                field_b = field_b_raw
            
            # Perform the calculation
            if operation == "+":
                result = field_a + field_b
            elif operation == "-":
                result = field_a - field_b
            elif operation == "*":
                result = field_a * field_b
            elif operation == "/":
                result = field_a / field_b if field_b != 0 else 0
            elif operation == "%":
                result = field_a % field_b if field_b != 0 else 0
            else:
                result = 0
            
            console.print(f"[green]Calculator: {field_a} {operation} {field_b} = {result}[/green]")
            
            return {"data": {"result": result}}
        
        except Exception as e:
            console.print(f"[red]Calculator error: {e}[/red]")
            return {"data": {"result": 0, "error": str(e)}}


class FormNode(NodeBase):
    """
    Node for creating dynamic forms with fields that accept expressions.

    Supports multiple field types: string, number, boolean, object
    Each field can contain {{}} expressions to reference previous node outputs.

    Uses individual text fields and dropdowns for better UX.
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb, log_cb=None) -> None:
        """
        Initialize a Form node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
            log_cb: Callback for logging during execution
        """
        super().__init__(name, parent, exec_cb, delete_cb, log_cb)
        
        # Store form fields as a list of dicts
        self.form_fields = [
            {"name": "fullName", "type": "string", "value": ""},
            {"name": "age", "type": "number", "value": "0"},
            {"name": "isActive", "type": "boolean", "value": "true"}
        ]
        
        # Track validation errors
        self.validation_errors = []
        
        # Define node fields (we'll store the form fields as JSON internally)
        self.fields = {
            "form_fields_json": {
                "value": self._fields_to_json(),
                "type": str,
                "label": "Form Fields (Internal)",
            },
        }
        
        # Initialize the node UI and configuration
        self.node_ui()
        self.node_configure()
        # Override the default inspector setup
        self.setup_form_inspector()
    
    def _fields_to_json(self) -> str:
        """Convert form fields list to JSON string."""
        import json
        return json.dumps(self.form_fields)
    
    def _json_to_fields(self, json_str: str) -> None:
        """Parse JSON string to form fields list."""
        import json
        try:
            self.form_fields = json.loads(json_str)
        except:
            self.form_fields = []
    
    def setup_form_inspector(self) -> None:
        """
        Create a custom inspector window for the form node with dynamic field management.
        """
        with dpg.window(
            label=f"{self.name} Inspector",
            modal=True,
            show=False,
            tag=f"{self.id}_inspector",
            no_title_bar=True,
            pos=self.pos,
            width=600,
            height=500,
        ):
            # Header
            dpg.add_text(f"{self.name} Configuration", color=(120, 180, 255))
            dpg.add_separator()
            dpg.add_spacer(height=5)
            
            # Scrollable container for form fields
            with dpg.child_window(
                tag=f"{self.id}_fields_container",
                height=350,
                border=True
            ):
                self._render_form_fields()
            
            dpg.add_spacer(height=5)
            
            # Add field button
            dpg.add_button(
                label="+ Add Field",
                callback=lambda: self._add_field(),
                width=580,
                tag=f"{self.id}_add_field_btn"
            )
            
            dpg.add_spacer(height=5)
            
            # Validation errors display
            dpg.add_text(
                "",
                tag=f"{self.id}_validation_errors",
                color=(255, 100, 100),
                wrap=580
            )
            
            # Footer buttons
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=lambda: self.save(), width=280)
                dpg.add_button(
                    label="Cancel", callback=lambda: self.close_inspector(), width=280
                )
        
        # Also setup the rename popup
        with dpg.window(
            label=f"{self.name} Rename",
            popup=True,
            show=False,
            tag=f"{self.id}_rename_popup",
            height=30,
            no_title_bar=True,
            pos=self.pos,
        ):
            dpg.add_input_text(
                default_value=self.name,
                tag=f"{self.id}_rename_text",
                label="Enter New Name",
            )
            dpg.add_button(
                label="Save",
                tag=f"{self.id}_rename_save_btn",
                callback=lambda: self.close_rename_popup(),
            )
    
    def _render_form_fields(self) -> None:
        """Render all form fields in the inspector."""
        # Clear existing fields
        children = dpg.get_item_children(f"{self.id}_fields_container", slot=1)
        if children:
            for child in children:
                if dpg.does_item_exist(child):
                    dpg.delete_item(child)
        
        # Render each field
        for i, field in enumerate(self.form_fields):
            self._render_field(i, field)
    
    def _render_field(self, index: int, field: Dict[str, str]) -> None:
        """
        Render a single form field row.
        
        Args:
            index: Index of the field in the form_fields list
            field: Field dictionary with name, type, value
        """
        field_group_tag = f"{self.id}_field_{index}"
        
        with dpg.group(
            tag=field_group_tag,
            parent=f"{self.id}_fields_container",
            horizontal=False
        ):
            # Field row with inputs
            with dpg.group(horizontal=True):
                # Field name input
                dpg.add_input_text(
                    default_value=field.get("name", ""),
                    hint="Field Name",
                    width=150,
                    tag=f"{self.id}_field_{index}_name",
                    label=""
                )
                
                # Field type dropdown
                dpg.add_combo(
                    items=["string", "number", "boolean", "object"],
                    default_value=field.get("type", "string"),
                    width=100,
                    tag=f"{self.id}_field_{index}_type",
                    label=""
                )
                
                # Field value input
                dpg.add_input_text(
                    default_value=field.get("value", ""),
                    hint="Value (supports {{}} expressions)",
                    width=250,
                    tag=f"{self.id}_field_{index}_value",
                    label=""
                )
                
                # Delete button
                dpg.add_button(
                    label="X",
                    callback=lambda s, a, u: self._delete_field(u),
                    user_data=index,
                    width=30,
                    tag=f"{self.id}_field_{index}_delete"
                )
            
            dpg.add_spacer(height=5)
    
    def _add_field(self) -> None:
        """Add a new field to the form."""
        self.form_fields.append({"name": "", "type": "string", "value": ""})
        self._render_form_fields()
    
    def _delete_field(self, index: int) -> None:
        """
        Delete a field from the form.
        
        Args:
            index: Index of the field to delete
        """
        if 0 <= index < len(self.form_fields):
            self.form_fields.pop(index)
            self._render_form_fields()
    
    def _validate_fields(self) -> List[str]:
        """
        Validate all form fields.
        
        Returns:
            List of validation error messages
        """
        errors = []
        field_names = set()
        
        for i, field in enumerate(self.form_fields):
            # Get current values from UI
            name = dpg.get_value(f"{self.id}_field_{i}_name").strip()
            field_type = dpg.get_value(f"{self.id}_field_{i}_type")
            value = dpg.get_value(f"{self.id}_field_{i}_value")
            
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
    
    def save(self) -> None:
        """
        Save changes from inspector inputs back to node state with validation.
        """
        # Collect field data from UI
        updated_fields = []
        for i in range(len(self.form_fields)):
            field_data = {
                "name": dpg.get_value(f"{self.id}_field_{i}_name").strip(),
                "type": dpg.get_value(f"{self.id}_field_{i}_type"),
                "value": dpg.get_value(f"{self.id}_field_{i}_value")
            }
            updated_fields.append(field_data)
        
        # Update form fields
        self.form_fields = updated_fields
        
        # Validate fields
        errors = self._validate_fields()
        
        if errors:
            # Show validation errors
            error_text = "Validation Errors:\n" + "\n".join(errors)
            dpg.set_value(f"{self.id}_validation_errors", error_text)
            console.print(f"[red]Form validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]- {error}[/red]")
            return
        
        # Clear validation errors
        dpg.set_value(f"{self.id}_validation_errors", "")
        self.validation_errors = []
        
        # Update state
        self.state["form_fields_json"] = self._fields_to_json()
        
        # Update the status display on the node
        field_count = len(self.form_fields)
        if field_count > 0:
            status_text = f"Form: {field_count} field(s)"
            dpg.set_value(f"{self.id}_state", value=status_text)
            dpg.configure_item(f"{self.id}_state", color=(86, 145, 193))
        else:
            status_text = "Form: No fields"
            dpg.set_value(f"{self.id}_state", value=status_text)
            dpg.configure_item(f"{self.id}_state", color=(86, 145, 193))
        
        # Debug output
        console.print(f"[cyan]Saved form node: {self.id[-8:]}[/cyan]")
        console.print(f"  Fields: {self.form_fields}")
        
        # Close the inspector
        self.close_inspector()
    
    def node_configure(self) -> None:
        """
        Initialize node state from field definitions.
        Override to load form fields from JSON.
        """
        # Create state dictionary from field values
        state = {key: field["value"] for key, field in self.fields.items()}
        
        # Preserve existing input connection if present
        if "input" in self.state:
            state["input"] = self.state["input"]
        else:
            state["input"] = []
        
        self.state = state
        
        # Load form fields from state if available
        if "form_fields_json" in self.state:
            self._json_to_fields(self.state["form_fields_json"])
        
        # Debug output
        console.print(f"[green]Configured node: {self.name}[/green]")
        console.print(f"  Form fields: {len(self.form_fields)} field(s)")
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute the form node - evaluate all field expressions and return structured output.
        
        Returns:
            Dictionary with form data: {"data": {field_name: evaluated_value, ...}}
        """
        try:
            # Parse the form fields
            self._json_to_fields(self.state.get("form_fields_json", "[]"))
            
            # Validate before execution
            if not self.form_fields:
                # Update node status to show error
                dpg.set_value(f"{self.id}_state", value="Form: No fields defined")
                dpg.configure_item(f"{self.id}_state", color=(255, 100, 100))
                return {"data": {"error": "No fields defined"}}
            
            # Build the output data
            output_data = {}
            
            for field in self.form_fields:
                field_name = field.get("name", "")
                field_type = field.get("type", "string")
                field_value = field.get("value", "")
                
                if not field_name:
                    continue
                
                # The value will be evaluated during execution (expressions resolved)
                # For now, just pass through the raw values
                if field_type == "string":
                    output_data[field_name] = str(field_value)
                elif field_type == "number":
                    try:
                        output_data[field_name] = float(field_value) if '.' in str(field_value) else int(field_value)
                    except:
                        output_data[field_name] = 0
                elif field_type == "boolean":
                    output_data[field_name] = str(field_value).lower() in ["true", "1", "yes"]
                elif field_type == "object":
                    try:
                        import json
                        output_data[field_name] = json.loads(field_value) if isinstance(field_value, str) else field_value
                    except:
                        output_data[field_name] = field_value
                else:
                    output_data[field_name] = field_value
            
            console.print(f"[green]Form output: {output_data}[/green]")
            
            # Update node status to success (will be overridden by executor status)
            dpg.set_value(f"{self.id}_state", value=f"Form: {len(output_data)} field(s)")
            dpg.configure_item(f"{self.id}_state", color=(86, 145, 193))
            
            return {"data": output_data}
        
        except Exception as e:
            console.print(f"[red]Form error: {e}[/red]")
            # Update node status to show error
            dpg.set_value(f"{self.id}_state", value=f"Form Error: {str(e)[:30]}")
            dpg.configure_item(f"{self.id}_state", color=(255, 100, 100))
            return {"data": {"error": str(e)}}


class ChatModelNode(NodeBase):
    """
    Node for interfacing with chat/language models.

    Configures and executes queries to language models (e.g., Gemma, GPT)
    with customizable parameters like temperature and token limits.

    Fields:
        model: Model identifier (e.g., "gemma-3")
        base_url: API endpoint URL
        temperature: Model temperature (0.0 - 1.0)
        max_tokens: Maximum output tokens
        timeout: Request timeout in seconds
        system_prompt: System prompt for model behavior
        query: User query to send to the model
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb, log_cb=None) -> None:
        """
        Initialize a Chat Model node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
            log_cb: Callback for logging during execution
        """
        super().__init__(name, parent, exec_cb, delete_cb, log_cb)

        # Define node fields with model configuration
        self.fields = {
            "model": {
                "value": "gemma-3",
                "type": str,
                "label": "Model to use",
            },
            "base_url": {
                "value": "http://localhost:8080",
                "type": str,
                "label": "API Base-URL",
            },
            "temperature": {
                "value": 0.1,
                "type": float,
                "label": "Model Temperature",
            },
            "max_tokens": {
                "value": 500,
                "type": int,
                "label": "Max Output tokens",
            },
            "timeout": {
                "value": 30,
                "type": int,
                "label": "Timeout",
            },
            "system_prompt": {
                "value": (
                    "You are a highly capable AI assistant designed to help with \n"
                    "coding, technical problems, and general inquiries.\n"
                    "Your core strengths are problem-solving, clear explanations, \n"
                    "and writing high-quality code."
                ),
                "type": LongString,
                "label": "System prompt",
            },
            "query": {
                "value": "Tell me about yourself",
                "type": str,
                "label": "Specify query",
            },
        }

        # Initialize the node UI and configuration
        self.node_ui()
        self.node_configure()
        self.setup_node_inspector()

    def save(self) -> None:
        """
        Save changes from inspector inputs back to node state.

        Updates all model configuration parameters from UI inputs.
        """
        # Update state from UI input values
        for field_key in self.fields.keys():
            input_tag = f"{self.id}_{field_key}"
            self.state[field_key] = dpg.get_value(item=input_tag)

        # Update the status display on the node
        status_text = f"{self.state['model']}\n{self.state['base_url']}"
        dpg.set_value(f"{self.id}_state", value=status_text)

        # Debug output
        console.print(f"[cyan]Saved node: {self.id[-8:]}[/cyan]")
        console.print(f"  State: {self.state}")

        # Close the inspector
        self.close_inspector()

    def execute(self) -> Dict[str, Any]:
        """
        Execute the chat model query using OpenAI-compatible API.

        Works with local LLMs (Ollama, LM Studio) and cloud providers.

        Returns:
            Dictionary with response text, model info, and usage stats
        """
        import requests

        model = self.state.get("model", "gemma-3")
        base_url = self.state.get("base_url", "http://localhost:8080")
        temperature = self.state.get("temperature", 0.1)
        max_tokens = self.state.get("max_tokens", 500)
        timeout = self.state.get("timeout", 30)
        system_prompt = self.state.get("system_prompt", "")
        query = self.state.get("query", "")

        self.log("INFO", f"Calling model {model} at {base_url}")

        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": query})

            self.log("DEBUG", f"Query: {query[:100]}...")

            # Make API call (OpenAI-compatible format)
            response = requests.post(
                f"{base_url.rstrip('/')}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=timeout
            )

            response.raise_for_status()
            result = response.json()

            # Extract response text
            response_text = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})

            self.log("INFO", f"Model response received ({len(response_text)} chars)")
            self.log("DEBUG", f"Usage: {usage}")

            return {
                "data": {
                    "response": response_text,
                    "model": model,
                    "usage": usage
                }
            }

        except requests.Timeout:
            self.log("ERROR", f"Model request timed out after {timeout}s")
            return {"data": {"error": "Timeout", "response": None, "model": model}}
        except requests.ConnectionError as e:
            self.log("ERROR", f"Connection error: {str(e)}")
            return {"data": {"error": f"Connection error: {str(e)}", "response": None, "model": model}}
        except requests.HTTPError as e:
            self.log("ERROR", f"HTTP error: {str(e)}")
            return {"data": {"error": f"HTTP error: {str(e)}", "response": None, "model": model}}
        except KeyError as e:
            self.log("ERROR", f"Unexpected response format: missing {e}")
            return {"data": {"error": f"Unexpected response format", "response": None, "model": model}}
        except Exception as e:
            self.log("ERROR", f"Model request failed: {str(e)}")
            return {"data": {"error": str(e), "response": None, "model": model}}


# ============================================================================
# Safe Builtins for CodeNode
# ============================================================================

CODE_NODE_SAFE_BUILTINS = {
    # Type conversions
    'int': int,
    'float': float,
    'str': str,
    'bool': bool,
    'list': list,
    'dict': dict,
    'tuple': tuple,
    'set': set,
    # Built-in functions
    'len': len,
    'range': range,
    'sum': sum,
    'min': min,
    'max': max,
    'abs': abs,
    'round': round,
    'sorted': sorted,
    'reversed': reversed,
    'enumerate': enumerate,
    'zip': zip,
    'any': any,
    'all': all,
    'print': print,
    'isinstance': isinstance,
    'type': type,
    # Iteration
    'map': map,
    'filter': filter,
    # Constants
    'True': True,
    'False': False,
    'None': None,
}


class CodeNode(NodeBase):
    """
    Node for executing sandboxed Python code with expression support.

    Code can reference previous node outputs using {{$node["Name"].data.property}}.
    Execution is sandboxed with limited builtins and timeout protection.

    The code should set a 'result' variable to return output.
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb, log_cb=None) -> None:
        """
        Initialize a Code node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
            log_cb: Callback for logging during execution
        """
        super().__init__(name, parent, exec_cb, delete_cb, log_cb)

        self.fields = {
            "code": {
                "value": "# Write Python code here\n# Use 'result' variable for output\n# Example: result = sum([1, 2, 3, 4, 5])\n\nresult = 42",
                "type": LongString,
                "label": "Python Code",
            },
        }

        self.node_ui()
        self.node_configure()
        self.setup_node_inspector()

    def save(self) -> None:
        """Save changes from inspector inputs back to node state."""
        for field_key in self.fields.keys():
            input_tag = f"{self.id}_{field_key}"
            self.state[field_key] = dpg.get_value(item=input_tag)

        # Show code preview in node
        code = self.state.get("code", "")
        lines = [l for l in code.strip().split('\n') if l.strip() and not l.strip().startswith('#')]
        preview = lines[0][:25] + "..." if lines else "Empty"
        dpg.set_value(f"{self.id}_state", value=f"Code: {preview}")

        console.print(f"[cyan]Saved code node: {self.id[-8:]}[/cyan]")
        self.close_inspector()

    def _validate_code_safety(self, code: str):
        """
        Parse and validate code safety using AST.

        Args:
            code: Python code string to validate

        Returns:
            AST tree if valid

        Raises:
            ValueError: If code contains unsafe operations
            SyntaxError: If code has syntax errors
        """
        import ast

        tree = ast.parse(code)

        for node in ast.walk(tree):
            # Reject imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise ValueError("Imports not allowed in CodeNode")

            # Reject dangerous function calls
            if isinstance(node, ast.Name) and node.id in ['eval', 'exec', 'compile', 'open', '__import__', 'globals', 'locals', 'vars', 'dir', 'getattr', 'setattr', 'delattr']:
                raise ValueError(f"Function '{node.id}' not allowed in CodeNode")

            # Reject private/dunder attribute access
            if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
                raise ValueError(f"Access to private attribute '{node.attr}' not allowed")

        return tree

    def execute(self) -> Dict[str, Any]:
        """
        Execute the Python code in a sandboxed environment.

        Features:
        - AST validation to reject dangerous operations
        - Whitelisted safe builtins only
        - 30 second timeout protection
        - Returns value via 'result' variable

        Returns:
            Dictionary with result or error
        """
        import ast
        import threading

        code = self.state.get("code", "")

        if not code.strip():
            return {"data": {"result": None, "error": "No code provided"}}

        self.log("INFO", "Starting code execution")

        try:
            # Step 1: Validate code safety
            self.log("DEBUG", "Validating code safety...")
            tree = self._validate_code_safety(code)

            # Step 2: Compile the code
            compiled = compile(tree, '<code>', 'exec')

            # Step 3: Prepare execution context with safe builtins
            exec_context = {
                '__builtins__': CODE_NODE_SAFE_BUILTINS.copy(),
            }

            # Step 4: Execute with timeout (30 seconds)
            result_container = {"completed": False, "error": None}

            def run_code():
                try:
                    exec(compiled, exec_context)
                    result_container["completed"] = True
                except Exception as e:
                    result_container["error"] = str(e)

            thread = threading.Thread(target=run_code)
            thread.daemon = True
            thread.start()
            thread.join(timeout=30)

            if thread.is_alive():
                self.log("ERROR", "Code execution timed out after 30 seconds")
                return {"data": {"result": None, "error": "Execution timeout (30s)"}}

            if result_container["error"]:
                self.log("ERROR", f"Code error: {result_container['error']}")
                return {"data": {"result": None, "error": result_container["error"]}}

            # Step 5: Capture result
            result = exec_context.get('result', None)

            self.log("INFO", f"Code executed successfully, result: {result}")

            return {"data": {"result": result}}

        except SyntaxError as e:
            self.log("ERROR", f"Syntax error: {e}")
            return {"data": {"result": None, "error": f"Syntax error: {e}"}}
        except ValueError as e:
            self.log("ERROR", f"Validation error: {e}")
            return {"data": {"result": None, "error": str(e)}}
        except Exception as e:
            self.log("ERROR", f"Execution failed: {e}")
            return {"data": {"result": None, "error": str(e)}}


# ============================================================================
# Node Type Enums
# ============================================================================


class ExecutionNodes(Enum):
    """
    Enumeration of execution node types.

    Execution nodes perform actions like HTTP requests, command execution,
    or AI model queries. They typically have input connections and can be
    chained in workflows.
    """

    HTTP_Request = HTTPRequestNode
    Execute_Command = ExecuteCommandNode
    Chat_Model = ChatModelNode
    Calculator = CalculatorNode
    Form = FormNode
    Code = CodeNode


class TriggerNodes(Enum):
    """
    Enumeration of trigger node types.

    Trigger nodes initiate workflows and typically have no input connections.
    They serve as starting points for execution chains.
    """

    Manual_Trigger = ManualTriggerNode
    Input = InputNode
