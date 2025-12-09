
from src.node_base import *


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


# ============================================================================
# Node Implementations
# ============================================================================


class ManualTriggerNode(NodeBase):
    """
    Manual trigger node for initiating workflows.

    This node has no inputs and serves as a starting point for workflows.
    It can be executed manually to trigger downstream nodes.
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb) -> None:
        """
        Initialize a Manual Trigger node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
        """
        super().__init__(name, parent, exec_cb, delete_cb)

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
            Current node state
        """
        return self.state


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

    def __init__(self, name: str, parent: str, exec_cb, delete_cb) -> None:
        """
        Initialize an HTTP Request node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
        """
        super().__init__(name, parent, exec_cb, delete_cb)

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
        Execute the HTTP request (placeholder implementation).

        Returns:
            Current node state with request configuration
        """
        return self.state


class ExecuteCommandNode(NodeBase):
    """
    Node for executing shell commands.

    Executes system commands and optionally logs output to a file.
    Useful for automation tasks and system integrations.

    Fields:
        command: Shell command to execute
        log_file: Path to log file for command output
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb) -> None:
        """
        Initialize an Execute Command node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
        """
        super().__init__(name, parent, exec_cb, delete_cb)

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
        Execute the shell command (placeholder implementation).

        Returns:
            Current node state with command configuration
        """
        console.print(
            f"[yellow]Executing command: {self.state['command']}\n"
            f"Saving to: {self.state['log_file']}[/yellow]"
        )
        return self.state


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

    def __init__(self, name: str, parent: str, exec_cb, delete_cb) -> None:
        """
        Initialize a Chat Model node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
        """
        super().__init__(name, parent, exec_cb, delete_cb)

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
        Execute the chat model query (placeholder implementation).

        Returns:
            Current node state with model configuration
        """
        return self.state


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
    # Agent_Model = AgentModelNode  # Future implementation


class TriggerNodes(Enum):
    """
    Enumeration of trigger node types.

    Trigger nodes initiate workflows and typically have no input connections.
    They serve as starting points for execution chains.
    """

    Manual_Trigger = ManualTriggerNode
