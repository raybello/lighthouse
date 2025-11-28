"""
Lighthouse Node Editor Application

A visual node-based editor built with DearPyGui for creating and configuring
workflow nodes with an HTTP request example implementation.
"""

from functools import partial
import uuid
import random
from enum import Enum
from typing import Dict, Any, Optional, Type, List
from abc import ABC, abstractmethod

import dearpygui.dearpygui as dpg
from rich.console import Console

# Initialize console for debug output
console = Console()


# ============================================================================
# Custom Types
# ============================================================================


class LongString(str):
    """Marker class to indicate a string field should use multiline input."""

    pass


# ============================================================================
# Enums
# ============================================================================


class HTTPRequestType(Enum):
    """Supported HTTP request methods."""

    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"
    DELETE = "DELETE"


# ============================================================================
# Base Classes
# ============================================================================


class NodeBase(ABC):
    """
    Abstract base class for all node types in the editor.

    Attributes:
        id: Unique identifier for the node
        name: Display name of the node
        pos: [x, y] position in the editor
        parent: Parent DearPyGui container
        state: Current runtime state of the node
        data: Output data produced by the node
        fields: Field definitions with types and default values
    """

    def __init__(self, name: str, parent: str) -> None:
        """
        Initialize a new node.

        Args:
            name: Display name for the node
            parent: Tag of the parent DearPyGui container
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.pos = [0, 0]
        self.parent = parent
        self.state: Dict[str, Any] = {}
        self.fields: Dict[str, Dict[str, Any]] = {}

    def node_ui(self, has_inputs=True, has_config=True) -> None:
        """Create the visual node in the editor with control buttons."""
        # Generate random initial position
        mouse_pos = dpg.get_mouse_pos(local=False)
        mouse_pos[1] = mouse_pos[1] - 100
        # self.pos = [random.randint(50, 400), random.randint(50, 400)]
        self.pos = mouse_pos

        # Create the main node container
        with dpg.node(
            label=f"{self.name}",
            pos=self.pos,
            tag=self.id,
            parent=self.parent,
        ):
            # Input attribute with delete button
            with dpg.node_attribute(
                tag=f"{self.id}_input_attr",
                shape=dpg.mvNode_PinShape_Circle,
                attribute_type=(
                    dpg.mvNode_Attr_Input if has_inputs else dpg.mvNode_Attr_Static
                ),
            ):
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Delete",
                        callback=lambda: self.delete(),
                        width=100,
                        tag=f"{self.id}_delete_btn",
                    )
                    dpg.add_button(
                        label="Edit",
                        callback=lambda: self.show_inspector(),
                        width=100,
                        tag=f"{self.id}_edit_btn",
                        show=True if has_config else False,
                    )
                    
                dpg.add_button(
                    label="Execute",
                    callback=lambda: self.execute(),
                    width=210,
                    tag=f"{self.id}_execute_btn",
                    show=True,
                )

            # Output attribute with configure button and status text
            with dpg.node_attribute(
                tag=f"{self.id}_output_attr",
                shape=dpg.mvNode_PinShape_Triangle,
                attribute_type=dpg.mvNode_Attr_Output,
            ):

                dpg.add_text(
                    default_value=f"ID: {self.id[-8:]}", tag=f"{self.id}_state"
                )

    def node_configure(self) -> None:
        """Initialize node state from field definitions."""
        # Create state dictionary from field values
        state = {key: field["value"] for key, field in self.fields.items()}

        # Preserve existing input connection if present
        if "input" in self.state:
            state["input"] = self.state["input"]
        else:
            state["input"] = []

        self.state = state

        # Debug output
        console.print(f"[green]Configured node: {self.name}[/green]")
        console.print(f"  State: {self.state}")

    def setup_node_inspector(self) -> None:
        """Create the inspector window for editing node properties."""
        with dpg.window(
            label=f"{self.name} Inspector",
            modal=True,
            show=False,
            # width=400,
            tag=f"{self.id}_inspector",
            no_title_bar=True,
            pos=self.pos,
        ):
            # Header
            dpg.add_text(f"{self.name} Configuration", color=(120, 180, 255))
            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Generate input fields based on field types
            for field_key, field_data in self.fields.items():
                field_type = field_data["type"]
                field_value = field_data["value"]
                field_label = field_data.get("label", field_key.capitalize())
                field_tag = f"{self.id}_{field_key}"

                # String input (single line)
                if field_type == str:
                    dpg.add_input_text(
                        label=field_label,
                        tag=field_tag,
                        default_value=field_value,
                        width=300,
                    )

                # Long string input (multiline)
                elif field_type == LongString:
                    dpg.add_input_text(
                        label=field_label,
                        tag=field_tag,
                        default_value=field_value,
                        multiline=True,
                        height=150,
                        width=300,
                    )

                # Enum (dropdown)
                elif isinstance(field_type, type) and issubclass(field_type, Enum):
                    enum_values = [e.value for e in field_type]
                    dpg.add_combo(
                        items=enum_values,
                        label=field_label,
                        tag=field_tag,
                        default_value=field_value,
                        width=300,
                    )

                # Integer input
                elif field_type == int:
                    dpg.add_input_int(
                        label=field_label,
                        tag=field_tag,
                        default_value=field_value,
                        width=300,
                    )

                dpg.add_spacer(height=5)

            # Footer buttons
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=lambda: self.save(), width=180)
                dpg.add_button(
                    label="Cancel", callback=lambda: self.close_inspector(), width=180
                )

    def show_inspector(self) -> None:
        """Display the inspector window near the node."""
        # Position inspector near the node
        node_pos = dpg.get_item_pos(self.id)
        inspector_pos = [node_pos[0], node_pos[1]]

        dpg.configure_item(item=f"{self.id}_inspector", pos=inspector_pos, show=True)

    def close_inspector(self) -> None:
        """Helper method to close the inspector window."""
        dpg.configure_item(f"{self.id}_inspector", show=False)

    @abstractmethod
    def save(self) -> None:
        """Save changes from the inspector back to the node state."""
        raise NotImplementedError

    @abstractmethod
    def execute(self) -> None:
        """Executes the node and mutate internal state"""
        raise NotImplementedError

    def delete(self) -> None:
        """Delete this node and cleanup resources."""
        # Delete the inspector window if it exists
        if dpg.does_item_exist(f"{self.id}_inspector"):
            dpg.delete_item(f"{self.id}_inspector")

        # Delete the node itself
        if dpg.does_item_exist(self.id):
            dpg.delete_item(self.id)

        console.print(f"[yellow]Deleted node: {self.name} ({self.id[-8:]})[/yellow]")


# ============================================================================
# Node Implementations
# ============================================================================


class ManualTriggerNode(NodeBase):
    def __init__(self, name: str, parent: str) -> None:
        """
        Initialize an Manual Trigger node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
        """
        super().__init__(name, parent)

        self.fields = {
            "status": {
                "value": "PENDING",
                "type": str,
                "label": "Status",
            },
        }

        # Initialize the node
        self.node_ui(has_inputs=False, has_config=False)
        self.node_configure()
        self.setup_node_inspector()

    def save(self) -> None:
        pass

    def execute(self) -> Dict[str, any]:
        return self.state


class HTTPRequestNode(NodeBase):
    """
    Node for configuring and executing HTTP requests.

    Supports various HTTP methods (GET, POST, etc.) with configurable
    URL, body, and timeout parameters.
    """

    def __init__(self, name: str, parent: str) -> None:
        """
        Initialize an HTTP Request node.

        Args:
            name: Display name for the node
            parent: Tag of the parent node editor
        """
        super().__init__(name, parent)

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
            "timeout": {"value": 30, "type": int, "label": "Timeout (seconds)"},
        }

        # Initialize the node
        self.node_ui()
        self.node_configure()
        self.setup_node_inspector()

    def save(self) -> None:
        """Save changes from inspector inputs back to node state."""
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

    def execute(self) -> Dict[str, any]:

        return self.state


class ExecuteCommandNode(NodeBase):
    def __init__(self, name: str, parent: str) -> None:
        super().__init__(name, parent)

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

        # Initialize the node
        self.node_ui()
        self.node_configure()
        self.setup_node_inspector()

    def save(self) -> None:
        """Save changes from inspector inputs back to node state."""
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

    def execute(self) -> Dict[str, any]:
        console.print(
            f"[yellow]Executing command: {self.state['command']}\nSaving to: {self.state['log_file']}[/yellow]"
        )
        return self.state


class ChatModelNode(NodeBase):

    def __init__(self, name: str, parent: str) -> None:
        super().__init__(name, parent)
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
                "label": "Model Temperature"
            },
            "max_tokens": {
                "value": 500,
                "type": int,
                "label": "Max Output tokens"
            },
            "timeout": {
                "value": 30,
                "type": int,
                "label": "Timeout"
            },
            "system_prompt": {
                "value": "You are a highly capable AI assistant designed to help with \ncoding, technical problems, and general inquiries.\nYour core strengths are problem-solving, clear explanations, \nand writing high-quality code.",
                "type": LongString,
                "label": "System prompt",
            },
            "query": {
                "value": "Tell me about yourself",
                "type": str,
                "label": "Specify query",
            },
        }

        # Initialize the node
        self.node_ui()
        self.node_configure()
        self.setup_node_inspector()

    def save(self) -> None:
        """Save changes from inspector inputs back to node state."""
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

    def execute(self) -> Dict[str, any]:
        return self.state


# ============================================================================
# Node Enum
# ============================================================================
class ExecutionNodes(Enum):
    HTTP_Request = HTTPRequestNode
    Execute_Command = ExecuteCommandNode
    Chat_Model = ChatModelNode
    # Agent_Model  = AgentModelNode


class TriggerNodes(Enum):
    Manual_Trigger = ManualTriggerNode


# ============================================================================
# Application Class
# ============================================================================


class LighthouseApp:
    """
    Main application class for the Lighthouse node editor.

    Manages the DearPyGui context, viewport, and node editor interface.
    """

    def __init__(self, title: str = "Lighthouse", width: int = 1400, height: int = 900):
        """
        Initialize the application.

        Args:
            title: Window title
            width: Viewport width in pixels
            height: Viewport height in pixels
        """
        self.title = title
        self.width = width
        self.height = height
        self.nodes: Dict[str, NodeBase] = {}
        self.edge: List[tuple(str, str)]
        self.connections: Dict[str, List[NodeBase]]

        # Initialize DearPyGui
        dpg.create_context()
        dpg.create_viewport(title=self.title, width=self.width, height=self.height)

        self._setup_ui()
        self._setup_handlers()

    def _setup_ui(self) -> None:
        """Create the main UI layout."""
        # Primary window
        with dpg.window(label=self.title, tag="primary_window"):
            # Node editor
            with dpg.node_editor(
                minimap=True,
                minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
                tag="node_editor",
            ):
                pass

        # Context menu for adding nodes
        with dpg.window(
            label="Add Node",
            modal=False,
            show=False,
            tag="context_menu",
            no_title_bar=True,
            popup=True,
        ):
            dpg.add_text("Add Node", color=(120, 180, 255))
            dpg.add_separator()
            dpg.add_text("Trigger Nodes", color=(150, 150, 155))

            trigger_types = [e for e in TriggerNodes]
            # console.print(trigger_types)

            def _make_callback_trig(trig_t):
                def callback(sender, app_data, user_data):
                    self._add_trigger_node(trig_t)

                return callback

            for trigger_type in trigger_types:
                # Manual Trigger
                dpg.add_button(
                    label=f"{trigger_type.name.replace('_', ' ')}",
                    # callback=lambda: self._add_trigger_node(trigger_type),
                    callback=_make_callback_trig(trigger_type),
                    width=200,
                    tag=f"{trigger_type.name}_add_btn",
                )

            dpg.add_separator()
            dpg.add_text("Execution Nodes", color=(150, 150, 155))

            exec_types = [i for i in ExecutionNodes]

            def _make_callback_exec(exec_t):
                def callback(sender, app_data, user_data):
                    self._add_execution_node(exec_t)

                return callback

            for exec_type in exec_types:
                console.print(f"Creating {exec_type}")
                dpg.add_button(
                    label=f"{exec_type.name.replace('_', ' ')}",
                    callback=_make_callback_exec(exec_type),
                    width=200,
                    tag=f"{exec_type.name}_add_btn",
                )

    def _setup_handlers(self) -> None:
        """Setup input handlers for the application."""
        with dpg.handler_registry():
            # Right-click to show context menu
            dpg.add_mouse_click_handler(
                button=dpg.mvMouseButton_Right, callback=self._show_context_menu
            )

    def _show_context_menu(self, sender: Any, app_data: Any) -> None:
        """
        Display the context menu at mouse position.

        Args:
            sender: DearPyGui sender
            app_data: DearPyGui application data
        """
        mouse_pos = dpg.get_mouse_pos(local=False)
        dpg.configure_item("context_menu", show=True, pos=mouse_pos)

    # def _add_http_node(self) -> None:
    #     """Add a new HTTP Request node to the editor."""
    #     node = HTTPRequestNode("HTTP Request", parent="node_editor")
    #     self.nodes[node.id] = node

    #     # Hide context menu
    #     dpg.configure_item("context_menu", show=False)

    #     console.print(f"[green]Added HTTP Request node: {node.id[-8:]}[/green]")

    def _add_execution_node(self, type_name: ExecutionNodes):

        try:
            console.print(type_name)
            node = type_name.value(
                f"{type_name.name.replace('_', ' ')}", parent="node_editor"
            )
            self.nodes[node.id] = node
            console.print(f"[green]Added {type_name.name} node: {node.id[-8:]}[/green]")
        except Exception as e:
            console.print_exception(f"Failed to create nodeType {type_name.name}: {e}")

        dpg.configure_item("context_menu", show=False)

    def _add_trigger_node(self, type_name: TriggerNodes):

        try:
            node = type_name.value(
                f"{type_name.name.replace('_', ' ')}", parent="node_editor"
            )
            self.nodes[node.id] = node
            console.print(f"[green]Added {type_name.name} node: {node.id[-8:]}[/green]")
        except Exception as e:
            console.print_exception(f"Failed to create nodeType {type_name.name}: {e}")

        dpg.configure_item("context_menu", show=False)

    def run(self) -> None:
        """Start the application main loop."""
        dpg.setup_dearpygui()
        dpg.set_primary_window("primary_window", True)
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    app = LighthouseApp()
    app.run()
