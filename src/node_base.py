import dearpygui.dearpygui as dpg
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from typing import Dict, Any, List
import time
import os
import sys


from rich.console import Console

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
                # Status text showing node ID (last 8 characters)
                dpg.add_text(
                    default_value="-", tag=f"{self.id}_state", color=(86, 145, 193)
                )
                with dpg.group(horizontal=True):
                    dpg.add_text(
                        bullet=True,
                        default_value=f"{self.id}",
                        tag=f"{self.id}_id",
                        color=(86, 145, 193),
                    )
                    dpg.add_loading_indicator(
                        style=1,
                        radius=1.5,
                        show=False,
                        tag=f"{self.id}_loading",
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
