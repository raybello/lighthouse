import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json


# ============================================================================
# STATE AND DATA STRUCTURES
# ============================================================================


@dataclass
class NodeData:
    """Stores data for a GUI node"""

    node_id: str
    node_type: str
    position: tuple
    value: Any = None
    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)
    result: Any = None
    gui_tag: str = ""


class NodeFlowGUI:
    """Main GUI application for LangGraph Lighthouses"""

    def __init__(self):
        self.nodes: Dict[str, NodeData] = {}
        self.links: List[tuple] = []  # List of (source_attr, target_attr) tuples
        self.node_counter = 0
        self.execution_results = None

        dpg.create_context()
        width, height, channels, data = dpg.load_image("output.png")

        with dpg.texture_registry(show=False):
            dpg.add_static_texture(
                width=width, height=height, default_value=data, tag="texture_tag"
            )

        self.setup_themes()
        self.setup_gui()

    def setup_themes(self):
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
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 10)
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

        # Node theme - rounded nodes with better colors
        # with dpg.theme(tag="node_theme"):
        #     with dpg.theme_component(dpg.mvAll):
        #         dpg.add_theme_style(dpg.mvNodeStyleVar_NodeCornerRounding, 8)
        #         dpg.add_theme_style(dpg.mvNodeStyleVar_NodePadding, 10, 10, 10, 10)
        #         dpg.add_theme_color(dpg.mvNodeCol_NodeBackground, (40, 45, 55, 240))
        #         dpg.add_theme_color(
        #             dpg.mvNodeCol_NodeBackgroundHovered, (50, 55, 70, 255)
        #         )
        #         dpg.add_theme_color(
        #             dpg.mvNodeCol_NodeBackgroundSelected, (60, 100, 180, 255)
        #         )
        #         dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, (70, 80, 100, 255))
        #         dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (55, 95, 170, 255))
        #         dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (65, 105, 190, 255))
        #         dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (75, 115, 210, 255))
        #         dpg.add_theme_color(dpg.mvNodeCol_Link, (100, 150, 220, 255))
        #         dpg.add_theme_color(dpg.mvNodeCol_LinkHovered, (120, 170, 240, 255))
        #         dpg.add_theme_color(dpg.mvNodeCol_LinkSelected, (140, 190, 255, 255))
        #         dpg.add_theme_color(dpg.mvNodeCol_Pin, (180, 200, 230, 255))
        #         dpg.add_theme_color(dpg.mvNodeCol_PinHovered, (200, 220, 245, 255))

        # Apply global theme
        dpg.bind_theme("global_theme")

    def setup_gui(self):
        """Initialize the GUI components"""
        dpg.create_viewport(title="Lighthouse", width=1400, height=900)

        # Main window
        with dpg.window(label="Lighthouse", tag="primary_window"):
            # Menu bar
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="New Graph", callback=self.clear_graph)
                    dpg.add_menu_item(
                        label="Execute Graph", callback=self.execute_graph
                    )

                with dpg.menu(label="Edit"):
                    dpg.add_menu_item(
                        label="Integer Node",
                        callback=lambda: self.add_value_node("int"),
                    )
                    dpg.add_menu_item(
                        label="Float Node",
                        callback=lambda: self.add_value_node("float"),
                    )
                    dpg.add_menu_item(
                        label="Text Node", callback=lambda: self.add_value_node("text")
                    )
                    dpg.add_separator()
                    dpg.add_menu_item(
                        label="Add Node",
                        callback=lambda: self.add_operation_node("add"),
                    )
                    dpg.add_menu_item(
                        label="Subtract Node",
                        callback=lambda: self.add_operation_node("subtract"),
                    )
                    dpg.add_menu_item(
                        label="Multiply Node",
                        callback=lambda: self.add_operation_node("multiply"),
                    )
                    dpg.add_menu_item(
                        label="Divide Node",
                        callback=lambda: self.add_operation_node("divide"),
                    )
                    dpg.add_separator()
                    dpg.add_menu_item(
                        label="Conditional Node",
                        callback=lambda: self.add_conditional_node(),
                    )

                with dpg.menu(label="View"):
                    dpg.add_menu_item(
                        label="Show demo",
                        callback=lambda: demo.show_demo(),
                    )

            # Horizontal layout
            with dpg.group(horizontal=True):
                # Node editor (main canvas)
                with dpg.child_window(width=1000, height=800):
                    with dpg.node_editor(
                        callback=self.link_callback,
                        delink_callback=self.delink_callback,
                        minimap=True,
                        minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
                        tag="node_editor",
                    ):
                        pass

                # Right panel for results and controls
                with dpg.child_window(width=-1, height=800):
                    with dpg.tab_bar():
                        with dpg.tab(label="Controls"):
                            dpg.add_text("Execution Controls", color=(120, 180, 255))
                            dpg.add_separator()

                            dpg.add_button(
                                label="Execute Graph",
                                callback=self.execute_graph,
                                width=-1,
                                height=40,
                                tag="execute_button",
                            )
                            dpg.bind_item_theme(
                                "execute_button", "execute_button_theme"
                            )

                            dpg.add_separator()
                            with dpg.collapsing_header(
                                label="Execution Results:", default_open=True
                            ):
                                dpg.add_text("No execution yet", tag="results_text", wrap=400)

                            dpg.add_separator()
                            with dpg.collapsing_header(label="Node Values:"):
                                dpg.add_text(
                                    "Execute graph to see values", tag="values_text", wrap=400
                                )

                        with dpg.tab(label="Settings"):
                            with dpg.collapsing_header(label="Graph Settings"):
                                dpg.add_image("texture_tag", width=75, height=400)
                            dpg.add_separator()

        # Create context menu for right-click on node editor
        with dpg.window(
            label="Add Node",
            modal=False,
            show=False,
            tag="context_menu",
            no_title_bar=True,
            popup=True,
        ):
            dpg.add_text("Add Node:", color=(120, 180, 255))
            dpg.add_separator()
            dpg.add_text("Data-types", color=(150, 150, 155))
            dpg.add_button(
                label="Integer Node",
                callback=lambda: self.add_value_node_from_context("int"),
                width=150,
                tag="ctx_int",
            )
            dpg.bind_item_theme("ctx_int", "context_button_theme")
            dpg.add_button(
                label="Float Node",
                callback=lambda: self.add_value_node_from_context("float"),
                width=150,
                tag="ctx_float",
            )
            dpg.bind_item_theme("ctx_float", "context_button_theme")
            dpg.add_button(
                label="Text Node",
                callback=lambda: self.add_value_node_from_context("text"),
                width=150,
                tag="ctx_text",
            )
            dpg.bind_item_theme("ctx_text", "context_button_theme")
            dpg.add_separator()
            dpg.add_text("Operations", color=(150, 150, 155))
            dpg.add_button(
                label="Add Node",
                callback=lambda: self.add_operation_node_from_context("add"),
                width=150,
                tag="ctx_add",
            )
            dpg.bind_item_theme("ctx_add", "context_button_theme")
            dpg.add_button(
                label="Subtract Node",
                callback=lambda: self.add_operation_node_from_context("subtract"),
                width=150,
                tag="ctx_sub",
            )
            dpg.bind_item_theme("ctx_sub", "context_button_theme")
            dpg.add_button(
                label="Multiply Node",
                callback=lambda: self.add_operation_node_from_context("multiply"),
                width=150,
                tag="ctx_mul",
            )
            dpg.bind_item_theme("ctx_mul", "context_button_theme")
            dpg.add_button(
                label="Divide Node",
                callback=lambda: self.add_operation_node_from_context("divide"),
                width=150,
                tag="ctx_div",
            )
            dpg.bind_item_theme("ctx_div", "context_button_theme")
            dpg.add_separator()
            dpg.add_text("Branching", color=(150, 150, 155))
            dpg.add_button(
                label="Conditional Node",
                callback=lambda: self.add_conditional_node_from_context(),
                width=150,
                tag="ctx_cond",
            )
            dpg.bind_item_theme("ctx_cond", "context_button_theme")

        # Register right-click handler
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(
                button=dpg.mvMouseButton_Right, callback=self.show_context_menu
            )

        dpg.setup_dearpygui()
        dpg.set_primary_window("primary_window", True)

    def show_context_menu(self, sender, app_data):
        """Show context menu on right-click"""
        mouse_pos = dpg.get_mouse_pos(local=False)
        dpg.configure_item("context_menu", show=True, pos=mouse_pos)

    def add_value_node_from_context(self, value_type: str):
        """Add a value node from context menu"""
        dpg.configure_item("context_menu", show=False)
        self.add_value_node(value_type)

    def add_operation_node_from_context(self, operation: str):
        """Add an operation node from context menu"""
        dpg.configure_item("context_menu", show=False)
        self.add_operation_node(operation)

    def add_conditional_node_from_context(self):
        """Add a conditional node from context menu"""
        dpg.configure_item("context_menu", show=False)
        self.add_conditional_node()

    def get_next_node_id(self) -> str:
        """Generate a unique node ID"""
        self.node_counter += 1
        return f"node_{self.node_counter}"

    def delete_node(self, node_id: str):
        """Delete a node and its connections"""
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        # Remove links connected to this node
        links_to_remove = []
        for link in self.links:
            source_attr, target_attr = link
            if node.gui_tag in source_attr or node.gui_tag in target_attr:
                links_to_remove.append(link)

        for link in links_to_remove:
            self.links.remove(link)

        # Update other nodes' connections
        for other_node in self.nodes.values():
            if node_id in other_node.outputs:
                other_node.outputs.remove(node_id)

            inputs_to_remove = [k for k, v in other_node.inputs.items() if v == node_id]
            for k in inputs_to_remove:
                del other_node.inputs[k]

        # Delete GUI element
        if dpg.does_item_exist(node.gui_tag):
            dpg.delete_item(node.gui_tag)

        del self.nodes[node_id]

    def add_value_node(self, value_type: str):
        """Add a value node (int, float, or text)"""
        node_id = self.get_next_node_id()
        node_tag = f"{node_id}_gui"

        import random

        pos = [random.randint(50, 400), random.randint(50, 400)]

        node_data = NodeData(
            node_id=node_id, node_type=value_type, position=pos, gui_tag=node_tag
        )
        self.nodes[node_id] = node_data

        # Create GUI node
        with dpg.node(
            label=f"{value_type.capitalize()} Node",
            pos=pos,
            tag=node_tag,
            parent="node_editor",
        ):
            dpg.bind_item_theme(node_tag, "node_theme")

            with dpg.node_attribute(tag=f"{node_tag}_delete_attr", shape=-1):
                dpg.add_button(
                    label="Delete",
                    callback=lambda: self.delete_node(node_id),
                    width=150,
                    tag=f"{node_tag}_delete_btn",
                )
                dpg.bind_item_theme(dpg.last_item(), "delete_button_theme")

            with dpg.node_attribute(tag=f"{node_tag}_config"):
                if value_type == "int":
                    dpg.add_input_int(
                        label="Value",
                        width=150,
                        default_value=0,
                        callback=lambda s, a: self.update_node_value(node_id, a),
                        tag=f"{node_tag}_input",
                    )
                elif value_type == "float":
                    dpg.add_input_float(
                        label="Value",
                        width=150,
                        default_value=0.0,
                        callback=lambda s, a: self.update_node_value(node_id, a),
                        tag=f"{node_tag}_input",
                    )
                else:  # text
                    dpg.add_input_text(
                        label="Value",
                        width=150,
                        default_value="",
                        callback=lambda s, a: self.update_node_value(node_id, a),
                        tag=f"{node_tag}_input",
                    )

            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output, tag=f"{node_tag}_output"
            ):
                dpg.add_text("Output ->")

    def add_operation_node(self, operation: str):
        """Add an operation node (add, subtract, multiply, divide)"""
        node_id = self.get_next_node_id()
        node_tag = f"{node_id}_gui"

        import random

        pos = [random.randint(300, 700), random.randint(50, 400)]

        node_data = NodeData(
            node_id=node_id, node_type=operation, position=pos, gui_tag=node_tag
        )
        self.nodes[node_id] = node_data

        # Create GUI node
        with dpg.node(
            label=f"{operation.capitalize()} Node",
            pos=pos,
            tag=node_tag,
            parent="node_editor",
        ):
            dpg.bind_item_theme(node_tag, "node_theme")

            with dpg.node_attribute(tag=f"{node_tag}_delete_attr", shape=-1):
                dpg.add_button(
                    label="Delete",
                    callback=lambda: self.delete_node(node_id),
                    width=150,
                    tag=f"{node_tag}_delete_btn",
                )
                dpg.bind_item_theme(dpg.last_item(), "delete_button_theme")

            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Input, tag=f"{node_tag}_input_a"
            ):
                dpg.add_text("<- Input A")

            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Input, tag=f"{node_tag}_input_b"
            ):
                dpg.add_text("<- Input B")

            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output, tag=f"{node_tag}_output"
            ):
                dpg.add_text("Output ->")
                
            with dpg.node_attribute(tag=f"{node_tag}_result", shape=-1):
                dpg.add_text("Result: N/A", tag=f"{node_tag}_result_text", wrap=400)
                # dpg.add_input_text(multiline=True, default_value="Result: N/A", height=100, width=200, tag=f"{node_tag}_result_text", tab_input=True, readonly=True)
                

    def add_conditional_node(self):
        """Add a conditional node"""
        node_id = self.get_next_node_id()
        node_tag = f"{node_id}_gui"

        import random

        pos = [random.randint(300, 700), random.randint(50, 400)]

        node_data = NodeData(
            node_id=node_id,
            node_type="conditional",
            position=pos,
            value=0.0,
            gui_tag=node_tag,
        )
        self.nodes[node_id] = node_data

        with dpg.node(
            label="Conditional Node", pos=pos, tag=node_tag, parent="node_editor"
        ):
            dpg.bind_item_theme(node_tag, "node_theme")

            with dpg.node_attribute(tag=f"{node_tag}_delete_attr", shape=-1):
                dpg.add_button(
                    label="Delete",
                    callback=lambda: self.delete_node(node_id),
                    width=150,
                    tag=f"{node_tag}_delete_btn",
                )
                dpg.bind_item_theme(dpg.last_item(), "delete_button_theme")

            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Input, tag=f"{node_tag}_input"
            ):
                dpg.add_text("<- Input")

            with dpg.node_attribute(tag=f"{node_tag}_config"):
                dpg.add_input_float(
                    label="Threshold",
                    width=150,
                    default_value=0.0,
                    callback=lambda s, a: self.update_node_value(node_id, a),
                    tag=f"{node_tag}_threshold",
                )
                
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output, tag=f"{node_tag}_output"
            ):
                dpg.add_text("Output ->")

            with dpg.node_attribute(tag=f"{node_tag}_result", shape=-1):
                dpg.add_text("Result: N/A", tag=f"{node_tag}_result_text", wrap=400)


    def update_node_value(self, node_id: str, value: Any):
        """Update a node's stored value"""
        if node_id in self.nodes:
            self.nodes[node_id].value = value

    def link_callback(self, sender, app_data):
        """Handle node linking"""
        source_attr, target_attr = app_data

        source_attr = dpg.get_item_alias(source_attr)
        target_attr = dpg.get_item_alias(target_attr)

        print((sender, source_attr, target_attr))
        self.links.append((source_attr, target_attr))
        dpg.add_node_link(source_attr, target_attr, parent=sender)

        # Parse node IDs from attribute tags
        source_node_id = self.get_node_id_from_attr(source_attr)
        target_node_id = self.get_node_id_from_attr(target_attr)

        if source_node_id and target_node_id:
            input_name = self.get_input_name_from_attr(target_attr)

            if target_node_id in self.nodes:
                self.nodes[target_node_id].inputs[input_name] = source_node_id
            if source_node_id in self.nodes:
                if target_node_id not in self.nodes[source_node_id].outputs:
                    self.nodes[source_node_id].outputs.append(target_node_id)

    def delink_callback(self, sender, app_data):
        """Handle node delinking"""
        link_id = app_data
        dpg.delete_item(app_data)

    def get_node_id_from_attr(self, attr_tag: str) -> Optional[str]:
        """Extract node ID from attribute tag"""
        print(attr_tag)
        parts = attr_tag.split("_")
        if len(parts) >= 3 and parts[0] == "node":
            return f"{parts[0]}_{parts[1]}"
        return None

    def get_input_name_from_attr(self, attr_tag: str) -> str:
        """Extract input name from attribute tag"""
        if "input_a" in attr_tag:
            return "input_a"
        elif "input_b" in attr_tag:
            return "input_b"
        elif "input" in attr_tag:
            return "condition_input"
        return "input"

    def execute_graph(self):
        """Execute the node graph"""
        try:
            execution_order = self.topological_sort()

            node_values = {}
            results_text = "Execution Order:\n" + "=" * 40 + "\n"

            for i, node_id in enumerate(execution_order, 1):
                node = self.nodes[node_id]
                results_text += f"{i}. {node_id} ({node.node_type})\n"

                if node.node_type in ["int", "float", "text"]:
                    value = (
                        node.value
                        if node.value is not None
                        else (0 if node.node_type in ["int", "float"] else "")
                    )
                    node_values[node_id] = value
                    node.result = value

                elif node.node_type in ["add", "subtract", "multiply", "divide"]:
                    input_a_node = node.inputs.get("input_a")
                    input_b_node = node.inputs.get("input_b")

                    if not input_a_node or not input_b_node:
                        results_text += f"   ERROR: Missing inputs\n"
                        continue

                    a = node_values.get(input_a_node, 0)
                    b = node_values.get(input_b_node, 0)

                    if node.node_type == "add":
                        result = a + b
                    elif node.node_type == "subtract":
                        result = a - b
                    elif node.node_type == "multiply":
                        result = a * b
                    else:  # divide
                        result = a / b if b != 0 else float("inf")

                    node_values[node_id] = result
                    node.result = result
                    results_text += f"   Result: {result}\n"

                    # Update GUI
                    result_tag = f"{node.gui_tag}_result_text"
                    if dpg.does_item_exist(result_tag):
                        dpg.set_value(result_tag, f"Result: {result}")

                elif node.node_type == "conditional":
                    input_node = node.inputs.get("condition_input")
                    if not input_node:
                        results_text += f"   ERROR: Missing input\n"
                        continue

                    value = node_values.get(input_node, 0)
                    threshold = node.value if node.value is not None else 0
                    result = value > threshold

                    node_values[node_id] = result
                    node.result = result
                    results_text += f"   {value} > {threshold} = {result}\n"

                    # Update GUI
                    result_tag = f"{node.gui_tag}_result_text"
                    if dpg.does_item_exist(result_tag):
                        dpg.set_value(result_tag, f"Result: {result}")

            # Display results
            results_text += "\n" + "=" * 40 + "\nNode Values:\n" + "=" * 40 + "\n"
            values_text = ""

            for node_id, value in node_values.items():
                node = self.nodes[node_id]
                results_text += f"{node_id}: {value}\n"
                values_text += f"{node_id} ({node.node_type}): {value}\n"

            dpg.set_value("results_text", results_text)
            dpg.set_value("values_text", values_text)

            self.execution_results = node_values

        except Exception as e:
            error_msg = f"Execution Error:\n{str(e)}"
            dpg.set_value("results_text", error_msg)

    def topological_sort(self) -> List[str]:
        """Perform topological sort to determine execution order"""
        in_degree = {node_id: len(node.inputs) for node_id, node in self.nodes.items()}
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for output_node_id in self.nodes[current].outputs:
                in_degree[output_node_id] -= 1
                if in_degree[output_node_id] == 0:
                    queue.append(output_node_id)

        if len(result) != len(self.nodes):
            raise ValueError("Graph contains cycles!")

        return result

    def clear_graph(self):
        """Clear all nodes and links"""
        self.nodes.clear()
        self.links.clear()
        dpg.delete_item("node_editor", children_only=True)
        dpg.set_value("results_text", "No execution yet")
        dpg.set_value("values_text", "Execute graph to see values")

    def run(self):
        """Start the GUI"""
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app = NodeFlowGUI()
    app.run()
