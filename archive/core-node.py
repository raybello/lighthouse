"""
Lighthouse Node Editor Application

A visual node-based editor built with DearPyGui for creating and configuring
workflow nodes. Supports various node types including HTTP requests, command
execution, and chat model integration with a drag-and-drop interface.

Author: Visual Workflow Team
Version: 1.0.0
"""

from functools import partial
import uuid
import random
import time
import sys
from collections import deque
from enum import Enum
from typing import Dict, Any, Optional, Type, List
from abc import ABC, abstractmethod

import dearpygui.dearpygui as dpg
from rich.console import Console
from rich import inspect


# Initialize console for debug output
console = Console()


# ============================================================================
# Custom Types
# ============================================================================


class LongString(str):
    """
    Marker class to indicate a string field should use multiline input.

    This allows the node inspector to differentiate between single-line
    and multi-line text input fields in the UI.
    """

    pass


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
# Base Classes
# ============================================================================


class NodeBase(ABC):
    """
    Abstract base class for all node types in the editor.

    This class provides the core functionality for visual nodes including:
    - UI rendering in the node editor
    - Configuration inspector windows
    - State management
    - Execution lifecycle

    Attributes:
        id (str): Unique identifier for the node (UUID)
        name (str): Display name of the node shown in the editor
        pos (List[int]): [x, y] position coordinates in the editor
        parent (str): Tag of the parent DearPyGui container
        state (Dict[str, Any]): Current runtime state of the node
        fields (Dict[str, Dict[str, Any]]): Field definitions with types and defaults
    """

    def __init__(self, name: str, parent: str, exec_cb, delete_cb) -> None:
        """
        Initialize a new node instance.

        Args:
            name: Display name for the node (shown in editor)
            parent: Tag of the parent DearPyGui container (node editor)
        """
        self.id = str(uuid.uuid4())[-8:]
        print(self.id)
        self.name = name
        self.pos = [0, 0]
        self.parent = parent
        self.exec_callback = exec_cb
        self.delete_cb = delete_cb
        self.status = "PENDING"
        self.state: Dict[str, Any] = {}
        self.fields: Dict[str, Dict[str, Any]] = {}

    def node_ui(self, has_inputs: bool = True, has_config: bool = True) -> None:
        """
        Create the visual representation of the node in the editor.

        Generates a node with:
        - Input/output connection points (attributes)
        - Delete and Edit buttons
        - Execute button
        - Status text display

        Args:
            has_inputs: Whether the node accepts input connections
            has_config: Whether the node has configurable fields (shows Edit button)
        """
        # Position node at mouse cursor (offset slightly downward)
        mouse_pos = dpg.get_mouse_pos(local=False)
        mouse_pos[1] = mouse_pos[1] - 100
        mouse_pos[0] = mouse_pos[0] - 100
        self.pos = mouse_pos

        # Create the main node container
        with dpg.node(
            label=f"{self.name}",
            pos=self.pos,
            tag=self.id,
            parent=self.parent,
        ):
            # ----------------------------------------------------------------
            # Input Attribute (top connection point)
            # ----------------------------------------------------------------
            with dpg.node_attribute(
                tag=f"{self.id}_input_attr",
                shape=dpg.mvNode_PinShape_Circle,
                attribute_type=(
                    dpg.mvNode_Attr_Input if has_inputs else dpg.mvNode_Attr_Static
                ),
            ):
                # Action buttons row

                # Execute button - triggers node execution
                dpg.add_button(
                    label="Edit",
                    callback=lambda: self.show_inspector(),
                    width=210,
                    tag=f"{self.id}_edit_btn",
                    show=has_config,
                )
                dpg.bind_item_theme(f"{self.id}_edit_btn", "context_button_theme")

                with dpg.group(horizontal=True):
                    # Delete button - removes this node from the editor
                    dpg.add_button(
                        label="Delete",
                        callback=lambda: self.delete(),
                        width=100,
                        tag=f"{self.id}_delete_btn",
                    )
                    dpg.bind_item_theme(f"{self.id}_delete_btn", "delete_button_theme")

                    dpg.add_button(
                        label="Rename",
                        callback=lambda: self.show_rename_popup(),
                        width=100,
                        tag=f"{self.id}_rename_btn",
                        show=True,
                    )
                    dpg.bind_item_theme(f"{self.id}_rename_btn", "context_button_theme")

                # Execute button - triggers node execution
                dpg.add_button(
                    label="Execute",
                    callback=lambda: self.exec_callback(self.id),
                    width=210,
                    tag=f"{self.id}_execute_btn",
                    show=True,
                )
                dpg.bind_item_theme(f"{self.id}_execute_btn", "execute_button_theme")

            # ----------------------------------------------------------------
            # Output Attribute (bottom connection point)
            # ----------------------------------------------------------------
            with dpg.node_attribute(
                tag=f"{self.id}_output_attr",
                shape=dpg.mvNode_PinShape_Triangle,
                attribute_type=dpg.mvNode_Attr_Output,
            ):
                with dpg.group(horizontal=True):
                    dpg.add_loading_indicator(
                        style=1,
                        radius=1.5,
                        show=False,
                        tag=f"{self.id}_loading",
                    )
                    dpg.add_text(
                        bullet=True,
                        default_value=f"{self.id}",
                        tag=f"{self.id}_id",
                        color=(86, 145, 193),
                    )
                    with dpg.tooltip(parent=f"{self.id}_id"):
                        dpg.add_text(
                            default_value=" Use ID to reference node.",
                            # color=(101, 122, 231),
                            tag=f"{self.id}_id_tooltip",
                        )
                    dpg.add_text(
                        default_value=self.status,
                        color=(101, 122, 231),
                        tag=f"{self.id}_exec_status",
                    )
                # Status text showing node ID (last 8 characters)
                dpg.add_text(
                    default_value="-", tag=f"{self.id}_state", color=(86, 145, 193)
                )

    def node_configure(self) -> None:
        """
        Initialize node state from field definitions.

        Populates the state dictionary with default values from fields.
        Preserves any existing input connections when reconfiguring.
        """
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
        """
        Create the inspector window for editing node properties.

        Dynamically generates UI inputs based on field types:
        - str: Single-line text input
        - LongString: Multi-line text area
        - Enum: Dropdown combo box
        - int: Integer input
        - float: Float input
        """
        with dpg.window(
            label=f"{self.name} Inspector",
            modal=True,
            show=False,
            tag=f"{self.id}_inspector",
            no_title_bar=True,
            pos=self.pos,
        ):
            # ----------------------------------------------------------------
            # Header
            # ----------------------------------------------------------------
            dpg.add_text(f"{self.name} Configuration", color=(120, 180, 255))
            dpg.add_separator()
            dpg.add_spacer(height=5)

            # ----------------------------------------------------------------
            # Generate input fields dynamically based on field types
            # ----------------------------------------------------------------
            for field_key, field_data in self.fields.items():
                field_type = field_data["type"]
                field_value = field_data["value"]
                field_label = field_data.get("label", field_key.capitalize())
                field_tag = f"{self.id}_{field_key}"

                # Single-line string input
                if field_type == str:
                    dpg.add_input_text(
                        label=field_label,
                        tag=field_tag,
                        default_value=field_value,
                        width=300,
                    )

                # Multi-line string input (text area)
                elif field_type == LongString:
                    dpg.add_input_text(
                        label=field_label,
                        tag=field_tag,
                        default_value=field_value,
                        multiline=True,
                        height=150,
                        width=300,
                    )

                # Enum dropdown selector
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

                # Float input
                elif field_type == float:
                    dpg.add_input_float(
                        label=field_label,
                        tag=field_tag,
                        default_value=field_value,
                        width=300,
                    )

                dpg.add_spacer(height=5)

            # ----------------------------------------------------------------
            # Footer buttons
            # ----------------------------------------------------------------
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save", callback=lambda: self.save(), width=180)
                dpg.add_button(
                    label="Cancel", callback=lambda: self.close_inspector(), width=180
                )

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

    def show_inspector(self) -> None:
        """
        Display the inspector window near the node.

        Positions the inspector at the node's current location
        for convenient editing.
        """
        # Get node position and set inspector position
        node_pos = dpg.get_item_pos(self.id)
        inspector_pos = [node_pos[0], node_pos[1]]

        dpg.configure_item(item=f"{self.id}_inspector", pos=inspector_pos, show=True)

    def close_inspector(self) -> None:
        """Hide the inspector window without saving changes."""
        dpg.configure_item(f"{self.id}_inspector", show=False)

    def show_rename_popup(self):
        node_pos = dpg.get_item_pos(self.id)
        popup_pos = [node_pos[0], node_pos[1]]

        dpg.configure_item(item=f"{self.id}_rename_popup", pos=popup_pos, show=True)

    def close_rename_popup(self):

        self.name = dpg.get_value(f"{self.id}_rename_text")
        dpg.configure_item(f"{self.id}", label=self.name)
        dpg.configure_item(f"{self.id}_rename_popup", show=False)

    @abstractmethod
    def save(self) -> None:
        """
        Save changes from the inspector back to the node state.

        Must be implemented by subclasses to handle saving
        field values from UI inputs.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self) -> None:
        """
        Execute the node's primary function.

        Must be implemented by subclasses to define the node's
        behavior when the Execute button is clicked.
        """
        raise NotImplementedError

    def delete(self) -> None:
        """
        Delete this node and cleanup associated resources.

        Removes the inspector window and the node itself from
        the DearPyGui context.
        """
        # Delete the inspector window if it exists
        if dpg.does_item_exist(f"{self.id}_inspector"):
            dpg.delete_item(f"{self.id}_inspector")

        # Delete the node itself
        if dpg.does_item_exist(self.id):
            dpg.delete_item(self.id)

        self.delete_cb(self.id)

        console.print(f"[yellow]Deleted node: {self.name} ({self.id[-8:]})[/yellow]")

    def set_callback(self, callback):
        self.exec_callback = callback


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


# ============================================================================
# Application Class
# ============================================================================


class LighthouseApp:
    """
    Main application class for the Lighthouse node editor.

    Manages the DearPyGui context, viewport, and node editor interface.
    Provides a visual workflow editor with support for creating, configuring,
    and connecting various node types.

    Attributes:
        title (str): Application window title
        width (int): Viewport width in pixels
        height (int): Viewport height in pixels
        nodes (Dict[str, NodeBase]): Dictionary of all active nodes
        edge (List[Tuple[str, str]]): List of connections between nodes
        connections (Dict[str, List[NodeBase]]): Node connection graph
    """

    def __init__(
        self,
        title: str = "Lighthouse",
        width: int = 1400,
        height: int = 900,
    ) -> None:
        """
        Initialize the application.

        Args:
            title: Window title for the application
            width: Viewport width in pixels
            height: Viewport height in pixels
        """
        self.title = title
        self.width = width
        self.height = height
        self.nodes: Dict[str, NodeBase] = {}
        self.edges: List[tuple] = []  # Stores (from_node, to_node) pairs
        self.connections: Dict = {}

        # Initialize DearPyGui context and viewport
        dpg.create_context()

        # Setup Themes
        self._setup_theme()
        # Create Viewport
        dpg.create_viewport(title=self.title, width=self.width, height=self.height)

        # Setup UI and input handlers
        self._setup_ui()
        self._setup_handlers()

    def link_callback(self, sender, app_data):
        """Handle node linking"""
        source_attr, target_attr = app_data
        source_attr = dpg.get_item_alias(source_attr)
        target_attr = dpg.get_item_alias(target_attr)

        # console.print((sender, source_attr, target_attr))
        # inspect((sender, source_attr, target_attr))

        self.edges.append((source_attr, target_attr))
        dpg.add_node_link(
            source_attr, target_attr, parent=sender, tag=f"{source_attr}_{target_attr}"
        )

        target_node_id = target_attr.split("_")[0]
        src_node_id = source_attr.split("_")[0]

        if target_node_id in self.connections.keys():
            self.connections[target_node_id].append(src_node_id)
        else:
            self.connections[target_node_id] = []
            self.connections[target_node_id].append(src_node_id)

        # console.print(f"Link Testing {[source_attr, target_attr]}")
        # console.print(self.connections)
        # console.print(self.edges)
        # inspect([self.connections, self.edges])

    def delink_callback(self, sender, app_data, user_data):
        """Handle node delinking"""
        # source_attr, target_attr = app_data
        # source_attr = dpg.get_item_alias(app_data)
        # target_attr = dpg.get_item_alias(target_attr)

        edge = dpg.get_item_configuration(item=app_data)

        source_full = dpg.get_item_alias(edge["attr_1"])
        source = source_full.split("_")[0]
        target_full = dpg.get_item_alias(edge["attr_2"])
        target = target_full.split("_")[0]

        self.connections[target] = [i for i in self.connections[target] if i != source]

        edges = []
        for src, target in self.edges:
            if src == source_full and target == target_full:
                pass
            elif src == target_full and target == source_full:
                pass
            else:
                edges.append((src, target))
        self.edges = edges

        # console.print(f"Delink Testing {[source_full, target_full]}")
        # console.print(self.connections)
        # console.print(self.edges)
        # inspect([self.connections, self.edges])

        dpg.delete_item(app_data)

    def _setup_theme(self):
        """Setup visual themes for the application"""

        # Global theme with rounded corners
        with dpg.theme(tag="global_theme"):
            with dpg.theme_component(dpg.mvAll):
                # Rounded corners for everything
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 8)

                # Padding and spacing
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)

                # Modern color scheme - dark with blue accents
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (20, 23, 28, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (25, 28, 35, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (35, 40, 50, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (45, 50, 65, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (55, 60, 75, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (25, 28, 35, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (30, 35, 45, 255))
                dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (25, 28, 35, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (60, 100, 180, 80))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (70, 110, 200, 120))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (80, 120, 220, 150))
                dpg.add_theme_color(dpg.mvThemeCol_Tab, (40, 45, 55, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (60, 100, 180, 200))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (55, 95, 170, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (25, 28, 35, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (60, 65, 75, 255))
                dpg.add_theme_color(
                    dpg.mvThemeCol_ScrollbarGrabHovered, (70, 75, 90, 255)
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ScrollbarGrabActive, (80, 85, 100, 255)
                )

        # Delete button theme - rounded red
        with dpg.theme(tag="delete_button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (180, 50, 50, 120))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (200, 60, 60, 180))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (220, 70, 70, 220))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))

        # Execute button theme - rounded green
        with dpg.theme(tag="execute_button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 4)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (50, 150, 80, 200))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 170, 95, 230))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (70, 190, 110, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))

        # Context menu button theme
        with dpg.theme(tag="context_button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (55, 95, 170, 150))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (65, 105, 190, 200))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (75, 115, 210, 255))

        dpg.bind_theme("global_theme")

        # Setup fonts
        with dpg.font_registry():
            # first argument ids the path to the .ttf or .otf file
            # default_font = dpg.add_font("fonts/SF-Pro.ttf", 17)
            default_font = dpg.add_font("fonts/SF-Pro-Display-Regular.otf", 17)

        dpg.bind_font(default_font)

    def _setup_ui(self) -> None:
        """
        Create the main UI layout.

        Sets up:
        - Primary window with node editor
        - Context menu for adding nodes
        - Minimap for navigation
        """
        # ----------------------------------------------------------------
        # Primary menubar
        # ----------------------------------------------------------------
        def print_me(sender):
            print(f"Menu Item: {sender}")

        with dpg.viewport_menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Save", callback=print_me)
                dpg.add_menu_item(label="Exit", callback=dpg.destroy_context)

                with dpg.menu(label="Settings"):
                    dpg.add_menu_item(label="Setting 1", callback=print_me, check=True)
                    dpg.add_menu_item(label="Setting 2", callback=print_me)

            with dpg.menu(label="Widget Items"):
                dpg.add_checkbox(label="Pick Me", callback=print_me)
                dpg.add_button(label="Press Me", callback=print_me)
                dpg.add_color_picker(label="Color Me", callback=print_me)

            with dpg.menu(label="Help"):
                dpg.add_text("Usage Tips")
                dpg.add_text("  Left-Click to add new nodes")
                dpg.add_text("  Ctrl-Click to delete node connection")
                dpg.add_separator()
                dpg.add_text("About")
                dpg.add_text("  RayB - Dec '25")
                dpg.add_text("  Version: 0.1")

        # ----------------------------------------------------------------
        # Primary window containing the node editor
        # ----------------------------------------------------------------
        with dpg.window(label=self.title, tag="primary_window"):

            # Node editor with minimap enabled
            with dpg.node_editor(
                callback=self.link_callback,
                delink_callback=self.delink_callback,
                minimap=True,
                # menubar=True,
                minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
                tag="node_editor",
            ):
                pass
        # ----------------------------------------------------------------
        # Context menu for adding new nodes (shown on right-click)
        # ----------------------------------------------------------------
        with dpg.window(
            label="Add Node",
            modal=False,
            show=False,
            tag="context_menu",
            no_title_bar=True,
            popup=True,
        ):
            # Menu header
            dpg.add_text("Add Node", color=(120, 180, 255))
            dpg.add_separator()

            # ============================================================
            # Trigger Nodes Section
            # ============================================================
            dpg.add_text("Trigger Nodes", color=(150, 150, 155))

            # Get all trigger node types from enum
            trigger_types = [e for e in TriggerNodes]

            # Create a closure to properly capture the trigger type
            def _make_callback_trig(trig_t):
                """
                Create a callback closure for trigger node buttons.

                This is necessary to properly capture the trigger type
                in the lambda function scope.
                """

                def callback(sender, app_data, user_data):
                    self._add_trigger_node(trig_t)

                return callback

            # Add button for each trigger node type
            for trigger_type in trigger_types:
                dpg.add_button(
                    label=f"{trigger_type.name.replace('_', ' ')}",
                    callback=_make_callback_trig(trigger_type),
                    width=200,
                    tag=f"{trigger_type.name}_add_btn",
                )

            dpg.add_separator()

            # ============================================================
            # Execution Nodes Section
            # ============================================================
            dpg.add_text("Execution Nodes", color=(150, 150, 155))

            # Get all execution node types from enum
            exec_types = [i for i in ExecutionNodes]

            # Create a closure to properly capture the execution type
            def _make_callback_exec(exec_t):
                """
                Create a callback closure for execution node buttons.

                This is necessary to properly capture the execution type
                in the lambda function scope.
                """

                def callback(sender, app_data, user_data):
                    self._add_execution_node(exec_t)

                return callback

            # Add button for each execution node type
            for exec_type in exec_types:
                console.print(f"Creating {exec_type}")
                dpg.add_button(
                    label=f"{exec_type.name.replace('_', ' ')}",
                    callback=_make_callback_exec(exec_type),
                    width=200,
                    tag=f"{exec_type.name}_add_btn",
                )

    def _setup_handlers(self) -> None:
        """
        Setup input handlers for the application.

        Registers event handlers for:
        - Right-click to show context menu
        """
        with dpg.handler_registry():
            # Right-click to show context menu for adding nodes
            dpg.add_mouse_click_handler(
                button=dpg.mvMouseButton_Right, callback=self._show_context_menu
            )

    def _show_context_menu(self, sender: Any, app_data: Any) -> None:
        """
        Display the context menu at mouse position.

        Shows the "Add Node" context menu when the user right-clicks
        in the editor, positioned at the cursor location.

        Args:
            sender: DearPyGui sender (unused)
            app_data: DearPyGui application data (unused)
        """
        mouse_pos = dpg.get_mouse_pos(local=False)
        dpg.configure_item("context_menu", show=True, pos=mouse_pos)

    def _add_execution_node(self, type_name: ExecutionNodes) -> None:
        """
        Add a new execution node to the editor.

        Creates a node instance of the specified type and adds it
        to the node editor at the mouse cursor position.

        Args:
            type_name: ExecutionNodes enum member specifying node type
        """
        try:
            console.print(type_name)

            # Instantiate the node class from the enum value
            node = type_name.value(
                f"{type_name.name.replace('_', ' ')}",
                parent="node_editor",
                exec_cb=self._exec_node,
                delete_cb=self._del_node,
            )

            # Register node in the nodes dictionary
            self.nodes[node.id] = node

            console.print(f"[green]Added {type_name.name} node: {node.id[-8:]}[/green]")

        except Exception as e:
            console.print_exception(f"Failed to create nodeType {type_name.name}: {e}")

        # Hide the context menu after adding node
        dpg.configure_item("context_menu", show=False)

    def _add_trigger_node(self, type_name: TriggerNodes) -> None:
        """
        Add a new trigger node to the editor.

        Creates a trigger node instance of the specified type and adds it
        to the node editor at the mouse cursor position.

        Args:
            type_name: TriggerNodes enum member specifying node type
        """
        try:
            # Instantiate the node class from the enum value
            node = type_name.value(
                f"{type_name.name.replace('_', ' ')}",
                parent="node_editor",
                exec_cb=self._exec_node,
                delete_cb=self._del_node,
            )

            # Register node in the nodes dictionary
            self.nodes[node.id] = node

            console.print(f"[green]Added {type_name.name} node: {node.id[-8:]}[/green]")

        except Exception as e:
            console.print_exception(f"Failed to create nodeType {type_name.name}: {e}")

        # Hide the context menu after adding node
        dpg.configure_item("context_menu", show=False)

    def _set_exec_status(self, node_id, color, status):

        self.nodes[node_id].status = status

        dpg.set_value(item=f"{node_id}_exec_status", value=status)
        dpg.configure_item(
            item=f"{node_id}_exec_status",
            color=color,
        )
        if status == "RUNNING":
            dpg.configure_item(
                item=f"{node_id}_loading",
                show=True,
                color=color,
            )
        else:
            dpg.configure_item(item=f"{node_id}_loading", show=False)

    def _topo_sort(self):

        # console.print(self.connections)
        # console.print(self.edges)

        in_degree = {}
        for n_id, _ in self.nodes.items():
            if n_id in self.connections.keys():
                in_degree[n_id] = len(self.connections[n_id])
            else:
                in_degree[n_id] = 0

        # console.print(in_degree)

        # Build adjacency list (outgoing connections)
        # self.connections stores incoming, so we need to reverse it
        outgoing = {n_id: [] for n_id, _ in self.nodes.items()}
        # print(f"nodes: {self.nodes.items()}")
        # print(f"nodes: {self.connections.items()}")
        for target_node, source_nodes in self.connections.items():
            for source_node in source_nodes:
                outgoing[source_node].append(target_node)

        # Start with nodes that have no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        # queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []
        processed = 0

        # while queue:
        #     current_level = list(queue)
        #     result.append(current_level)
        #     queue.clear()

        #     processed += len(current_level)

        #     for node_id in current_level:
        #         if node_id in outgoing:
        #             for child_id in outgoing[node_id]:
        #                 if child_id in in_degree:
        #                     in_degree[child_id] -= 1

        #                     if in_degree[child_id] == 0:
        #                         queue.append(child_id)

        # if processed < len(in_degree):
        #     unprocessed = [
        #         node_id for node_id, degree in in_degree.items() if degree > 0
        #     ]
        #     console.print(
        #         f"[red]Warning: Cycle detected! Unprocessed nodes: {unprocessed}[/red]"
        #     )
        #     return [list(in_degree.keys())]  # Fallback to sequential

        # console.print(
        #     f"[cyan]Topological sort complete: {len(result)} levels, {processed} nodes[/cyan]"
        # )
        # for i, level in enumerate(result):
        #     node_names = [self.nodes[nid].name for nid in level]
        #     console.print(f"  Level {i}: {node_names}")


        while queue:
            current = queue.pop(0)
            result.append(current)

            # For each node that current points to
            for neighbor in outgoing[current]:
                in_degree[neighbor] -= 1
                # If neighbor now has no incoming edges, add to queue
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(self.nodes):
            console.print("Warning: Cycle detected in graph!")
            return list(self.nodes.keys())  # Return original order if cycle exists


        return result

    def _execute_step(self, node_id):
        self._set_exec_status(node_id, (194, 188, 81), "RUNNING")

        time.sleep(3)

        self.nodes[node_id].execute()

        self._set_exec_status(node_id, (83, 202, 74), "COMPLETED")

    def _exec_graph(self, node_id):

        execution_order = self._topo_sort()
        console.print(execution_order)

        # Iterate to execute
        started = False
        for nid in execution_order:

            if self.nodes[nid].status == "PENDING":
                self._execute_step(nid)
            elif self.nodes[nid].status == "ERROR":
                self._execute_step(nid)
            elif self.nodes[nid].status == "COMPLETED" and started == True:
                self._execute_step(nid)
            elif (
                self.nodes[nid].status == "COMPLETED"
                and started == False
                and nid == node_id
            ):
                started = True
                self._execute_step(nid)
            else:
                pass  # Should be unreachable

    def _exec_node(self, node_id):
        console.print(f"ENGINE: Attempting to start execution from {node_id}")
        self._exec_graph(node_id)

    def _del_node(self, node_id):
        self.nodes.pop(node_id, None)
        self.connections.pop(node_id, None)
        # Remove this node from other nodes' connection lists (outgoing edges from this node)
        for target_node in self.connections:
            self.connections[target_node] = [
                src for src in self.connections[target_node] if src != node_id
            ]

        # Remove all edges involving this node
        self.edges = [
            (src, target)
            for src, target in self.edges
            if not (src.startswith(f"{node_id}_") or target.startswith(f"{node_id}_"))
        ]

        # console.print(f"ENGINE: Deleting Node {node_id} from Engine")
        # console.print(self.nodes)

    def run(self) -> None:
        """
        Start the application main loop.

        Initializes DearPyGui, shows the viewport, and starts the
        rendering loop. Blocks until the application is closed.
        """
        # Setup DearPyGui internals
        dpg.setup_dearpygui()

        # Set the primary window (fills viewport)
        dpg.set_primary_window("primary_window", True)

        # Show the viewport window
        dpg.show_viewport()

        # Start the main rendering loop (blocks until window closed)
        dpg.start_dearpygui()

        # Cleanup DearPyGui context after exit
        dpg.destroy_context()


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    # Create and run the application
    app = LighthouseApp()
    app.run()
