"""
Node renderer for DearPyGui.

Implements the INodeRenderer protocol for rendering nodes in the DearPyGui interface.
"""

import json
from typing import Any, Callable, Dict, Optional

import dearpygui.dearpygui as dpg
from rich.console import Console

from lighthouse.domain.models.field_types import FieldType
from lighthouse.domain.protocols.ui_protocol import INodeRenderer
from lighthouse.nodes.base.base_node import BaseNode

console = Console()


class DearPyGuiNodeRenderer(INodeRenderer):
    """
    DearPyGui implementation of the INodeRenderer protocol.

    Renders workflow nodes in the node editor canvas with:
    - Input/output attributes for connections
    - Node-specific UI elements
    - Inspector windows for configuration
    - State display and editing
    """

    def __init__(self, parent_editor: int):
        """
        Initialize the node renderer.

        Args:
            parent_editor: DearPyGui node editor ID
        """
        self.parent_editor = parent_editor
        self._node_widgets: Dict[str, int] = {}  # node_id -> dpg node ID
        self._callbacks: Dict[str, Dict[str, Callable]] = {}  # node_id -> callbacks
        self._nodes: Dict[str, BaseNode] = {}  # node_id -> node reference
        self._node_positions: Dict[str, tuple] = {}  # node_id -> (x, y) position

    def render_node(
        self,
        node: BaseNode,
        position: tuple = (100, 100),
        callbacks: Optional[Dict[str, Callable]] = None,
    ) -> int:
        """
        Render a node in the editor.

        Args:
            node: Node to render
            position: (x, y) position in the editor
            callbacks: Optional callbacks for node events

        Returns:
            DearPyGui node ID
        """
        callbacks = callbacks or {}
        self._callbacks[node.id] = callbacks
        self._nodes[node.id] = node

        # Store initial position for inspector/popup windows
        self._node_positions[node.id] = position

        with dpg.node(
            label=node.name, parent=self.parent_editor, pos=position, tag=node.id
        ) as node_widget:
            # Input attribute with buttons
            attr_type = (
                dpg.mvNode_Attr_Input if node.metadata.has_inputs else dpg.mvNode_Attr_Static
            )

            with dpg.node_attribute(
                tag=f"{node.id}_input_attr",
                shape=dpg.mvNode_PinShape_Circle,
                attribute_type=attr_type,
            ):
                # Use lambda without parameters, exactly like legacy
                # Capture node.id in closure to avoid late binding issues
                node_id_for_callback = node.id

                # Edit button - opens inspector
                if node.metadata.has_config:
                    edit_btn = dpg.add_button(
                        label="Edit",
                        callback=lambda: self._show_inspector(node_id_for_callback),
                        width=210,
                        tag=f"{node.id}_edit_btn",
                    )
                    dpg.bind_item_theme(edit_btn, "context_button_theme")

                # Delete and Rename buttons row
                with dpg.group(horizontal=True):
                    del_btn = dpg.add_button(
                        label="Delete",
                        callback=callbacks.get("on_delete"),
                        user_data=node.id,
                        width=100,
                        tag=f"{node.id}_delete_btn",
                    )
                    dpg.bind_item_theme(del_btn, "delete_button_theme")

                    # Capture node.id in closure for rename callback too
                    rename_btn = dpg.add_button(
                        label="Rename",
                        callback=lambda: self._show_rename_popup(node_id_for_callback),
                        width=100,
                        tag=f"{node.id}_rename_btn",
                    )
                    dpg.bind_item_theme(rename_btn, "context_button_theme")

                # Execute button
                exec_btn = dpg.add_button(
                    label="Execute",
                    callback=callbacks.get("on_execute"),
                    user_data=node.id,
                    width=210,
                    tag=f"{node.id}_execute_btn",
                )
                dpg.bind_item_theme(exec_btn, "execute_button_theme")

            # Output attribute with status
            with dpg.node_attribute(
                tag=f"{node.id}_output_attr",
                shape=dpg.mvNode_PinShape_Triangle,
                attribute_type=dpg.mvNode_Attr_Output,
            ):
                # State preview text
                dpg.add_text(
                    default_value=self._get_state_preview(node),
                    tag=f"{node.id}_state",
                    color=(86, 145, 193),
                )

                # Status row with ID, loading indicator, and status
                with dpg.group(horizontal=True):
                    dpg.add_text(
                        bullet=True,
                        default_value=node.id,
                        tag=f"{node.id}_id",
                        color=(86, 145, 193),
                    )
                    with dpg.tooltip(parent=f"{node.id}_id"):
                        dpg.add_text(
                            default_value=" Use ID to reference node.",
                            tag=f"{node.id}_id_tooltip",
                        )

                    dpg.add_loading_indicator(
                        style=1,
                        radius=1.5,
                        show=False,
                        tag=f"{node.id}_loading",
                    )

                    status = getattr(node, "status", "PENDING")
                    status_color = self._get_status_color(status)
                    dpg.add_text(
                        default_value=status,
                        color=status_color,
                        tag=f"{node.id}_exec_status",
                    )

        self._node_widgets[node.id] = node_widget

        # Create inspector and rename popup windows
        console.print(f"[yellow]Creating inspector and rename popup for node {node.id}[/yellow]")
        self._create_inspector(node)
        self._create_rename_popup(node)

        # Verify they were created
        if dpg.does_item_exist(f"{node.id}_inspector"):
            console.print(f"[green]  ✓ Inspector created: {node.id}_inspector[/green]")
        else:
            console.print(f"[red]  ✗ Inspector NOT created: {node.id}_inspector[/red]")

        if dpg.does_item_exist(f"{node.id}_rename_popup"):
            console.print(f"[green]  ✓ Rename popup created: {node.id}_rename_popup[/green]")
        else:
            console.print(f"[red]  ✗ Rename popup NOT created: {node.id}_rename_popup[/red]")

        return node_widget

    def _get_state_preview(self, node: BaseNode) -> str:
        """Get a preview string of the node's current state."""
        state = node.state
        if not state:
            return "-"

        # Get first two meaningful values
        previews = []
        for key, value in state.items():
            if key == "input":
                continue
            val_str = str(value)[:30]
            if len(str(value)) > 30:
                val_str += "..."
            previews.append(val_str)
            if len(previews) >= 2:
                break

        return "\n".join(previews) if previews else "-"

    def _get_status_color(self, status: str) -> tuple:
        """Get color for a status string."""
        status_colors = {
            "PENDING": (150, 150, 150),
            "RUNNING": (194, 188, 81),
            "COMPLETED": (83, 202, 74),
            "ERROR": (202, 74, 74),
        }
        return status_colors.get(status, (150, 150, 150))

    def _create_inspector(self, node: BaseNode) -> None:
        """Create the inspector window for a node."""
        # Check for custom inspector types (Input and Form nodes)
        if node.metadata.name == "Input":
            self._create_input_inspector(node)
            return
        elif node.metadata.name == "Form":
            self._create_form_inspector(node)
            return

        # Calculate window size based on field count
        field_count = len(node.metadata.fields)
        base_height = 150  # Header + footer
        field_height = 60  # Per field
        long_field_height = 180  # For multiline fields

        total_height = base_height
        for field_def in node.metadata.fields:
            if field_def.field_type in (FieldType.LONG_STRING, FieldType.OBJECT):
                total_height += long_field_height
            else:
                total_height += field_height

        total_height = min(total_height, 600)  # Cap at 600

        # Get initial position from stored node position
        initial_pos = self._node_positions.get(node.id, (100, 100))

        with dpg.window(
            label=f"{node.name} Inspector",
            modal=True,
            show=False,
            tag=f"{node.id}_inspector",
            no_title_bar=True,
            width=450,
            height=total_height,
            pos=list(initial_pos),  # Set initial position like legacy
        ):
            # Header
            dpg.add_text(f"{node.name} Configuration", color=(120, 180, 255))
            dpg.add_text(
                'Use {{$node["NodeName"].data.field}} for expressions', color=(150, 150, 155)
            )
            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Generate input fields from metadata
            for field_def in node.metadata.fields:
                self._create_field_input(node, field_def)
                dpg.add_spacer(height=5)

            # Footer buttons
            dpg.add_separator()
            with dpg.group(horizontal=True):
                # Capture node.id for callbacks
                node_id_save = node.id
                dpg.add_button(
                    label="Save", callback=lambda: self._save_inspector(node_id_save), width=200
                )
                dpg.add_button(
                    label="Cancel", callback=lambda: self._close_inspector(node_id_save), width=200
                )

    def _create_field_input(self, node: BaseNode, field_def) -> None:
        """Create an input widget for a field definition."""
        field_tag = f"{node.id}_{field_def.name}"
        current_value = node.state.get(field_def.name, field_def.default_value)

        # Add description/hint if available
        if field_def.description:
            dpg.add_text(field_def.description, color=(120, 120, 130))

        if field_def.field_type == FieldType.STRING:
            dpg.add_input_text(
                label=field_def.label,
                tag=field_tag,
                default_value=str(current_value) if current_value else "",
                width=300,
                hint="Enter value or {{expression}}",
            )

        elif field_def.field_type == FieldType.LONG_STRING:
            dpg.add_input_text(
                label=field_def.label,
                tag=field_tag,
                default_value=str(current_value) if current_value else "",
                multiline=True,
                height=150,
                width=300,
            )

        elif field_def.field_type == FieldType.NUMBER:
            # For numbers, use text input to support expressions
            dpg.add_input_text(
                label=field_def.label,
                tag=field_tag,
                default_value=str(current_value) if current_value is not None else "0",
                width=300,
                hint="Number or {{expression}}",
            )

        elif field_def.field_type == FieldType.BOOLEAN:
            # For boolean, use combo to also support expressions
            dpg.add_combo(
                items=["true", "false"],
                label=field_def.label,
                tag=field_tag,
                default_value=str(current_value).lower() if current_value is not None else "false",
                width=300,
            )

        elif field_def.field_type == FieldType.ENUM:
            options = field_def.enum_options or []
            dpg.add_combo(
                items=options,
                label=field_def.label,
                tag=field_tag,
                default_value=str(current_value)
                if current_value
                else (options[0] if options else ""),
                width=300,
            )

        elif field_def.field_type == FieldType.OBJECT:
            # JSON/object fields as multiline text
            val_str = json.dumps(current_value, indent=2) if current_value else "{}"
            dpg.add_input_text(
                label=field_def.label,
                tag=field_tag,
                default_value=val_str,
                multiline=True,
                height=100,
                width=300,
            )

    def _create_input_inspector(self, node: BaseNode) -> None:
        """Create custom inspector for InputNode with dynamic property management."""
        initial_pos = self._node_positions.get(node.id, (100, 100))

        with dpg.window(
            label=f"{node.name} Inspector",
            modal=True,
            show=False,
            tag=f"{node.id}_inspector",
            no_title_bar=True,
            pos=list(initial_pos),
            width=600,
            height=500,
        ):
            # Header
            dpg.add_text(f"{node.name} Configuration", color=(120, 180, 255))
            dpg.add_text("Define properties that will be available as data", color=(150, 150, 155))
            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Scrollable container for properties
            with dpg.child_window(tag=f"{node.id}_properties_container", height=350, border=True):
                # Properties will be rendered dynamically
                pass

            dpg.add_spacer(height=5)

            # Add property button
            node_id_add = node.id
            dpg.add_button(
                label="+ Add Property",
                callback=lambda: self._add_input_property(node_id_add),
                width=580,
                tag=f"{node.id}_add_property_btn",
            )

            dpg.add_spacer(height=5)

            # Validation errors display
            dpg.add_text("", tag=f"{node.id}_validation_errors", color=(255, 100, 100), wrap=580)

            # Footer buttons
            dpg.add_separator()
            with dpg.group(horizontal=True):
                node_id_save = node.id
                dpg.add_button(
                    label="Save",
                    callback=lambda: self._save_input_inspector(node_id_save),
                    width=280,
                )
                dpg.add_button(
                    label="Cancel", callback=lambda: self._close_inspector(node_id_save), width=280
                )

    def _create_form_inspector(self, node: BaseNode) -> None:
        """Create custom inspector for FormNode with dynamic field management."""
        initial_pos = self._node_positions.get(node.id, (100, 100))

        with dpg.window(
            label=f"{node.name} Inspector",
            modal=True,
            show=False,
            tag=f"{node.id}_inspector",
            no_title_bar=True,
            pos=list(initial_pos),
            width=600,
            height=500,
        ):
            # Header
            dpg.add_text(f"{node.name} Configuration", color=(120, 180, 255))
            dpg.add_text(
                "Define form fields with types and values (supports {{}} expressions)",
                color=(150, 150, 155),
            )
            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Scrollable container for form fields
            with dpg.child_window(tag=f"{node.id}_fields_container", height=350, border=True):
                # Fields will be rendered dynamically
                pass

            dpg.add_spacer(height=5)

            # Add field button
            node_id_add = node.id
            dpg.add_button(
                label="+ Add Field",
                callback=lambda: self._add_form_field(node_id_add),
                width=580,
                tag=f"{node.id}_add_field_btn",
            )

            dpg.add_spacer(height=5)

            # Validation errors display
            dpg.add_text("", tag=f"{node.id}_validation_errors", color=(255, 100, 100), wrap=580)

            # Footer buttons
            dpg.add_separator()
            with dpg.group(horizontal=True):
                node_id_save = node.id
                dpg.add_button(
                    label="Save",
                    callback=lambda: self._save_form_inspector(node_id_save),
                    width=280,
                )
                dpg.add_button(
                    label="Cancel", callback=lambda: self._close_inspector(node_id_save), width=280
                )

    def _create_rename_popup(self, node: BaseNode) -> None:
        """Create the rename popup for a node."""
        # Get initial position from stored node position
        initial_pos = self._node_positions.get(node.id, (100, 100))

        with dpg.window(
            label=f"{node.name} Rename",
            popup=True,  # Use popup like legacy (closes on outside click)
            show=False,
            tag=f"{node.id}_rename_popup",
            no_title_bar=True,
            height=80,
            pos=list(initial_pos),  # Set initial position like legacy
        ):
            dpg.add_text("Rename Node", color=(120, 180, 255))
            dpg.add_separator()
            dpg.add_spacer(height=5)

            dpg.add_input_text(
                default_value=node.name,
                tag=f"{node.id}_rename_text",
                label="New Name",
                width=250,
            )

            dpg.add_spacer(height=5)
            dpg.add_separator()

            with dpg.group(horizontal=True):
                # Capture node.id for callbacks
                node_id_rename = node.id
                dpg.add_button(
                    label="Save",
                    tag=f"{node.id}_rename_save_btn",
                    callback=lambda: self._save_rename(node_id_rename),
                    width=150,
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: self._close_rename_popup(node_id_rename),
                    width=150,
                )

    def _show_inspector(self, node_id: str) -> None:
        """Show the inspector window for a node."""
        console.print(f"[cyan]_show_inspector called for: {node_id}[/cyan]")

        node = self._nodes.get(node_id)
        if node:
            console.print(f"[cyan]  Found node: {node.name}[/cyan]")

            # Handle custom inspectors differently
            if node.metadata.name == "Input":
                self._render_input_properties(node)
            elif node.metadata.name == "Form":
                self._render_form_fields(node)
            else:
                # Update field values from current state before showing
                self._update_inspector_fields(node)
        else:
            console.print("[red]  Node not found in self._nodes![/red]")

        if dpg.does_item_exist(node_id):
            node_pos = dpg.get_item_pos(node_id)
            console.print(f"[cyan]  Node position: {node_pos}[/cyan]")
            inspector_tag = f"{node_id}_inspector"
            if dpg.does_item_exist(inspector_tag):
                console.print(f"[green]  Showing inspector: {inspector_tag}[/green]")
                dpg.configure_item(inspector_tag, pos=node_pos, show=True)
            else:
                console.print(f"[red]  Inspector {inspector_tag} does not exist![/red]")
        else:
            console.print(f"[red]  Node {node_id} does not exist in dpg![/red]")

    def _update_inspector_fields(self, node: BaseNode) -> None:
        """Update inspector field values from node state."""
        for field_def in node.metadata.fields:
            field_tag = f"{node.id}_{field_def.name}"
            if dpg.does_item_exist(field_tag):
                value = node.state.get(field_def.name, field_def.default_value)

                if field_def.field_type == FieldType.OBJECT:
                    value = json.dumps(value, indent=2) if value else "{}"
                elif field_def.field_type == FieldType.BOOLEAN:
                    value = str(value).lower() if value is not None else "false"
                elif value is not None:
                    value = str(value)
                else:
                    value = ""

                dpg.set_value(field_tag, value)

    def _close_inspector(self, node_id: str) -> None:
        """Close the inspector window for a node."""
        inspector_tag = f"{node_id}_inspector"
        if dpg.does_item_exist(inspector_tag):
            dpg.configure_item(inspector_tag, show=False)

    def _save_inspector(self, node_id: str) -> None:
        """Save changes from the inspector to the node state."""
        node = self._nodes.get(node_id)
        if not node:
            self._close_inspector(node_id)
            return

        # Collect field values
        new_state = {}
        for field_def in node.metadata.fields:
            field_tag = f"{node.id}_{field_def.name}"
            if dpg.does_item_exist(field_tag):
                value = dpg.get_value(field_tag)

                # Convert types as needed (but keep strings for expression support)
                if field_def.field_type == FieldType.OBJECT:
                    try:
                        value = json.loads(value) if value else {}
                    except json.JSONDecodeError:
                        value = {}
                elif field_def.field_type == FieldType.BOOLEAN:
                    if value in ("true", "True", True):
                        value = True
                    elif value in ("false", "False", False):
                        value = False
                    # Keep as string if it's an expression
                elif field_def.field_type == FieldType.NUMBER:
                    # Keep as string to support expressions
                    # Will be converted during execution
                    pass

                new_state[field_def.name] = value

        # Update node state
        node.update_state(new_state)

        # Update state preview display
        preview = self._get_state_preview(node)
        self.update_node_state_display(node_id, preview)

        # Call save callback if provided
        callbacks = self._callbacks.get(node_id, {})
        on_save = callbacks.get("on_save")
        if on_save:
            on_save(None, None, node_id)

        self._close_inspector(node_id)
        console.print(f"[cyan]Saved node: {node_id}[/cyan]")
        console.print(f"  State: {node.state}")

    def _show_rename_popup(self, node_id: str) -> None:
        """Show the rename popup for a node."""
        console.print(f"[cyan]_show_rename_popup called for: {node_id}[/cyan]")

        node = self._nodes.get(node_id)
        if node:
            # Update the rename text field with current name
            rename_tag = f"{node_id}_rename_text"
            if dpg.does_item_exist(rename_tag):
                dpg.set_value(rename_tag, node.name)

        if dpg.does_item_exist(node_id):
            node_pos = dpg.get_item_pos(node_id)
            console.print(f"[cyan]  Node position: {node_pos}[/cyan]")
            popup_tag = f"{node_id}_rename_popup"
            if dpg.does_item_exist(popup_tag):
                console.print(f"[green]  Showing rename popup: {popup_tag}[/green]")
                dpg.configure_item(popup_tag, pos=node_pos, show=True)
            else:
                console.print(f"[red]  Rename popup {popup_tag} does not exist![/red]")
        else:
            console.print(f"[red]  Node {node_id} does not exist in dpg![/red]")

    def _close_rename_popup(self, node_id: str) -> None:
        """Close the rename popup for a node."""
        popup_tag = f"{node_id}_rename_popup"
        if dpg.does_item_exist(popup_tag):
            dpg.configure_item(popup_tag, show=False)

    def _save_rename(self, node_id: str) -> None:
        """Save the new name from the rename popup."""
        rename_text_tag = f"{node_id}_rename_text"
        if dpg.does_item_exist(rename_text_tag):
            new_name = dpg.get_value(rename_text_tag)

            # Update node reference
            node = self._nodes.get(node_id)
            if node:
                node.name = new_name

            # Update node label in UI
            if dpg.does_item_exist(node_id):
                dpg.configure_item(node_id, label=new_name)

            # Update inspector window label
            inspector_tag = f"{node_id}_inspector"
            if dpg.does_item_exist(inspector_tag):
                dpg.configure_item(inspector_tag, label=f"{new_name} Inspector")

            # Notify callback
            callbacks = self._callbacks.get(node_id, {})
            on_rename = callbacks.get("on_rename")
            if on_rename:
                on_rename(None, None, (node_id, new_name))

            console.print(f"[cyan]Renamed node {node_id} to: {new_name}[/cyan]")

        self._close_rename_popup(node_id)

    # ========================================================================
    # InputNode Custom Inspector Methods
    # ========================================================================

    def _render_input_properties(self, node: BaseNode) -> None:
        """Render all input properties in the inspector."""
        # Parse properties from state
        properties_json = node.state.get("properties", "[]")
        try:
            properties = json.loads(properties_json) if properties_json else []
        except json.JSONDecodeError:
            properties = []

        # Clear existing properties
        container_tag = f"{node.id}_properties_container"
        children = dpg.get_item_children(container_tag, slot=1)
        if children:
            for child in children:
                if dpg.does_item_exist(child):
                    dpg.delete_item(child)

        # Render each property
        for i, prop in enumerate(properties):
            self._render_input_property(node.id, i, prop)

    def _render_input_property(self, node_id: str, index: int, prop: Dict[str, Any]) -> None:
        """Render a single input property row."""
        property_group_tag = f"{node_id}_property_{index}"

        with dpg.group(
            tag=property_group_tag, parent=f"{node_id}_properties_container", horizontal=False
        ):
            # Property row with inputs
            with dpg.group(horizontal=True):
                # Property name input
                dpg.add_input_text(
                    default_value=prop.get("name", ""),
                    hint="Property Name",
                    width=250,
                    tag=f"{node_id}_property_{index}_name",
                    label="",
                )

                # Property value input
                dpg.add_input_text(
                    default_value=prop.get("value", ""),
                    hint="Value (supports {{}} expressions)",
                    width=280,
                    tag=f"{node_id}_property_{index}_value",
                    label="",
                )

                # Delete button
                dpg.add_button(
                    label="X",
                    callback=lambda s, a, u: self._delete_input_property(node_id, u),
                    user_data=index,
                    width=30,
                    tag=f"{node_id}_property_{index}_delete",
                )

            dpg.add_spacer(height=5)

    def _add_input_property(self, node_id: str) -> None:
        """Add a new property to the input node."""
        node = self._nodes.get(node_id)
        if not node:
            return

        # Get current properties
        properties_json = node.state.get("properties", "[]")
        try:
            properties = json.loads(properties_json) if properties_json else []
        except json.JSONDecodeError:
            properties = []

        # Add new empty property
        properties.append({"name": "", "value": ""})

        # Update node state
        node.update_state({"properties": json.dumps(properties)})

        # Re-render
        self._render_input_properties(node)

    def _delete_input_property(self, node_id: str, index: int) -> None:
        """Delete a property from the input node."""
        node = self._nodes.get(node_id)
        if not node:
            return

        # Get current properties
        properties_json = node.state.get("properties", "[]")
        try:
            properties = json.loads(properties_json) if properties_json else []
        except json.JSONDecodeError:
            properties = []

        # Remove property at index
        if 0 <= index < len(properties):
            properties.pop(index)

            # Update node state
            node.update_state({"properties": json.dumps(properties)})

            # Re-render
            self._render_input_properties(node)

    def _save_input_inspector(self, node_id: str) -> None:
        """Save changes from input inspector to node state with validation."""
        node = self._nodes.get(node_id)
        if not node:
            self._close_inspector(node_id)
            return

        # Get current properties count
        properties_json = node.state.get("properties", "[]")
        try:
            properties = json.loads(properties_json) if properties_json else []
        except json.JSONDecodeError:
            properties = []

        # Collect property data from UI
        updated_properties = []
        for i in range(len(properties)):
            name_tag = f"{node_id}_property_{i}_name"
            value_tag = f"{node_id}_property_{i}_value"

            if dpg.does_item_exist(name_tag) and dpg.does_item_exist(value_tag):
                property_data = {
                    "name": dpg.get_value(name_tag).strip(),
                    "value": dpg.get_value(value_tag),
                }
                updated_properties.append(property_data)

        # Validate properties
        errors = []
        property_names = set()

        for i, prop in enumerate(updated_properties):
            prop_name = prop.get("name", "")

            # Validate property name
            if not prop_name:
                errors.append(f"Property {i + 1}: Property name is required")
            elif not prop_name.replace("_", "").isalnum():
                errors.append(
                    f"Property {i + 1}: Property name '{prop_name}' must be alphanumeric (underscores allowed)"
                )
            elif prop_name in property_names:
                errors.append(f"Property {i + 1}: Duplicate property name '{prop_name}'")
            else:
                property_names.add(prop_name)

        if errors:
            # Show validation errors
            error_text = "Validation Errors:\n" + "\n".join(errors)
            dpg.set_value(f"{node_id}_validation_errors", error_text)
            console.print("[red]Input validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]- {error}[/red]")
            return

        # Clear validation errors
        dpg.set_value(f"{node_id}_validation_errors", "")

        # Update state
        node.update_state({"properties": json.dumps(updated_properties)})

        # Update the status display on the node
        property_count = len(updated_properties)
        if property_count > 0:
            preview = f"Input: {property_count} property(ies)"
        else:
            preview = "Input: No properties"

        self.update_node_state_display(node_id, preview)

        # Call save callback if provided
        callbacks = self._callbacks.get(node_id, {})
        on_save = callbacks.get("on_save")
        if on_save:
            on_save(None, None, node_id)

        self._close_inspector(node_id)
        console.print(f"[cyan]Saved input node: {node_id}[/cyan]")
        console.print(f"  Properties: {updated_properties}")

    # ========================================================================
    # FormNode Custom Inspector Methods
    # ========================================================================

    def _render_form_fields(self, node: BaseNode) -> None:
        """Render all form fields in the inspector."""
        # Parse fields from state
        fields_json = node.state.get("form_fields_json", "[]")
        try:
            fields = json.loads(fields_json) if fields_json else []
        except json.JSONDecodeError:
            fields = []

        # Clear existing fields
        container_tag = f"{node.id}_fields_container"
        children = dpg.get_item_children(container_tag, slot=1)
        if children:
            for child in children:
                if dpg.does_item_exist(child):
                    dpg.delete_item(child)

        # Render each field
        for i, field in enumerate(fields):
            self._render_form_field(node.id, i, field)

    def _render_form_field(self, node_id: str, index: int, field: Dict[str, Any]) -> None:
        """Render a single form field row."""
        field_group_tag = f"{node_id}_field_{index}"

        with dpg.group(tag=field_group_tag, parent=f"{node_id}_fields_container", horizontal=False):
            # Field row with inputs
            with dpg.group(horizontal=True):
                # Field name input
                dpg.add_input_text(
                    default_value=field.get("name", ""),
                    hint="Field Name",
                    width=150,
                    tag=f"{node_id}_field_{index}_name",
                    label="",
                )

                # Field type dropdown
                dpg.add_combo(
                    items=["string", "number", "boolean", "object"],
                    default_value=field.get("type", "string"),
                    width=100,
                    tag=f"{node_id}_field_{index}_type",
                    label="",
                )

                # Field value input
                dpg.add_input_text(
                    default_value=field.get("value", ""),
                    hint="Value (supports {{}} expressions)",
                    width=250,
                    tag=f"{node_id}_field_{index}_value",
                    label="",
                )

                # Delete button
                dpg.add_button(
                    label="X",
                    callback=lambda s, a, u: self._delete_form_field(node_id, u),
                    user_data=index,
                    width=30,
                    tag=f"{node_id}_field_{index}_delete",
                )

            dpg.add_spacer(height=5)

    def _add_form_field(self, node_id: str) -> None:
        """Add a new field to the form node."""
        node = self._nodes.get(node_id)
        if not node:
            return

        # Get current fields
        fields_json = node.state.get("form_fields_json", "[]")
        try:
            fields = json.loads(fields_json) if fields_json else []
        except json.JSONDecodeError:
            fields = []

        # Add new empty field
        fields.append({"name": "", "type": "string", "value": ""})

        # Update node state
        node.update_state({"form_fields_json": json.dumps(fields)})

        # Re-render
        self._render_form_fields(node)

    def _delete_form_field(self, node_id: str, index: int) -> None:
        """Delete a field from the form node."""
        node = self._nodes.get(node_id)
        if not node:
            return

        # Get current fields
        fields_json = node.state.get("form_fields_json", "[]")
        try:
            fields = json.loads(fields_json) if fields_json else []
        except json.JSONDecodeError:
            fields = []

        # Remove field at index
        if 0 <= index < len(fields):
            fields.pop(index)

            # Update node state
            node.update_state({"form_fields_json": json.dumps(fields)})

            # Re-render
            self._render_form_fields(node)

    def _save_form_inspector(self, node_id: str) -> None:
        """Save changes from form inspector to node state with validation."""
        node = self._nodes.get(node_id)
        if not node:
            self._close_inspector(node_id)
            return

        # Get current fields count
        fields_json = node.state.get("form_fields_json", "[]")
        try:
            fields = json.loads(fields_json) if fields_json else []
        except json.JSONDecodeError:
            fields = []

        # Collect field data from UI
        updated_fields = []
        for i in range(len(fields)):
            name_tag = f"{node_id}_field_{i}_name"
            type_tag = f"{node_id}_field_{i}_type"
            value_tag = f"{node_id}_field_{i}_value"

            if (
                dpg.does_item_exist(name_tag)
                and dpg.does_item_exist(type_tag)
                and dpg.does_item_exist(value_tag)
            ):
                field_data = {
                    "name": dpg.get_value(name_tag).strip(),
                    "type": dpg.get_value(type_tag),
                    "value": dpg.get_value(value_tag),
                }
                updated_fields.append(field_data)

        # Validate fields
        errors = []
        field_names = set()

        for i, field in enumerate(updated_fields):
            field_name = field.get("name", "")
            field_type = field.get("type", "string")
            value = field.get("value", "")

            # Validate field name
            if not field_name:
                errors.append(f"Field {i + 1}: Field name is required")
            elif not field_name.replace("_", "").isalnum():
                errors.append(
                    f"Field {i + 1}: Field name '{field_name}' must be alphanumeric (underscores allowed)"
                )
            elif field_name in field_names:
                errors.append(f"Field {i + 1}: Duplicate field name '{field_name}'")
            else:
                field_names.add(field_name)

            # Validate value based on type (only if not an expression)
            if value and not value.strip().startswith("{{"):
                if field_type == "number":
                    try:
                        float(value)
                    except ValueError:
                        errors.append(f"Field '{field_name}': Value must be a number or expression")
                elif field_type == "boolean":
                    if value.lower() not in ["true", "false", "1", "0", "yes", "no"]:
                        errors.append(
                            f"Field '{field_name}': Value must be true/false or expression"
                        )
                elif field_type == "object":
                    if not value.startswith("{") and not value.startswith("["):
                        errors.append(
                            f"Field '{field_name}': Value must be valid JSON object/array or expression"
                        )

        if errors:
            # Show validation errors
            error_text = "Validation Errors:\n" + "\n".join(errors)
            dpg.set_value(f"{node_id}_validation_errors", error_text)
            console.print("[red]Form validation failed:[/red]")
            for error in errors:
                console.print(f"  [red]- {error}[/red]")
            return

        # Clear validation errors
        dpg.set_value(f"{node_id}_validation_errors", "")

        # Update state
        node.update_state({"form_fields_json": json.dumps(updated_fields)})

        # Update the status display on the node
        field_count = len(updated_fields)
        if field_count > 0:
            preview = f"Form: {field_count} field(s)"
        else:
            preview = "Form: No fields"

        self.update_node_state_display(node_id, preview)

        # Call save callback if provided
        callbacks = self._callbacks.get(node_id, {})
        on_save = callbacks.get("on_save")
        if on_save:
            on_save(None, None, node_id)

        self._close_inspector(node_id)
        console.print(f"[cyan]Saved form node: {node_id}[/cyan]")
        console.print(f"  Fields: {updated_fields}")

    def update_node_status(self, node_id: str, status: str) -> None:
        """
        Update the displayed status of a node.

        Args:
            node_id: ID of the node to update
            status: New status string
        """
        status_tag = f"{node_id}_exec_status"
        loading_tag = f"{node_id}_loading"

        color = self._get_status_color(status)

        if dpg.does_item_exist(status_tag):
            dpg.set_value(status_tag, status)
            dpg.configure_item(status_tag, color=color)

        if dpg.does_item_exist(loading_tag):
            if status == "RUNNING":
                dpg.configure_item(loading_tag, show=True, color=color)
            else:
                dpg.configure_item(loading_tag, show=False)

    def update_node_state_display(self, node_id: str, preview: str) -> None:
        """
        Update the state preview display on a node.

        Args:
            node_id: ID of the node to update
            preview: New preview string
        """
        state_tag = f"{node_id}_state"
        if dpg.does_item_exist(state_tag):
            dpg.set_value(state_tag, preview)

    def update_inspector_fields(self, node: BaseNode) -> None:
        """
        Update inspector field values from node state.

        Args:
            node: Node to update fields for
        """
        self._update_inspector_fields(node)

    def get_field_values(self, node: BaseNode) -> Dict[str, Any]:
        """
        Get current values from inspector fields.

        Args:
            node: Node to get field values for

        Returns:
            Dictionary of field name -> value
        """
        values = {}
        for field_def in node.metadata.fields:
            field_tag = f"{node.id}_{field_def.name}"
            if dpg.does_item_exist(field_tag):
                value = dpg.get_value(field_tag)

                # Convert types as needed
                if field_def.field_type == FieldType.OBJECT:
                    try:
                        value = json.loads(value) if value else {}
                    except json.JSONDecodeError:
                        value = {}
                elif field_def.field_type == FieldType.BOOLEAN:
                    if value in ("true", "True", True):
                        value = True
                    elif value in ("false", "False", False):
                        value = False

                values[field_def.name] = value

        return values

    def remove_node(self, node_id: str) -> None:
        """
        Remove a node from the editor.

        Args:
            node_id: ID of the node to remove
        """
        # Remove inspector window
        inspector_tag = f"{node_id}_inspector"
        if dpg.does_item_exist(inspector_tag):
            dpg.delete_item(inspector_tag)

        # Remove rename popup
        rename_popup_tag = f"{node_id}_rename_popup"
        if dpg.does_item_exist(rename_popup_tag):
            dpg.delete_item(rename_popup_tag)

        # Remove node
        if dpg.does_item_exist(node_id):
            dpg.delete_item(node_id)

        # Cleanup tracking
        if node_id in self._node_widgets:
            del self._node_widgets[node_id]
        if node_id in self._callbacks:
            del self._callbacks[node_id]
        if node_id in self._nodes:
            del self._nodes[node_id]

        console.print(f"[yellow]Deleted node: {node_id}[/yellow]")

    def get_node_position(self, node_id: str) -> Optional[tuple]:
        """
        Get the current position of a node.

        Args:
            node_id: Node identifier

        Returns:
            (x, y) position or None if node not found
        """
        if dpg.does_item_exist(node_id):
            return dpg.get_item_pos(node_id)
        return None

    def set_node_position(self, node_id: str, position: tuple) -> None:
        """
        Set the position of a node.

        Args:
            node_id: Node identifier
            position: (x, y) position
        """
        if dpg.does_item_exist(node_id):
            dpg.set_item_pos(node_id, position)
