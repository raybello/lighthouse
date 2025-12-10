from .nodes import *

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

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        if hasattr(sys, '_MEIPASS'):
            # Running from the bundled exe
            return os.path.join(sys._MEIPASS, relative_path)
        else:
            # Running normally (source code)
            return os.path.join(os.path.abspath("."), relative_path)

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
            default_font = dpg.add_font(
                self.resource_path("fonts/SF-Pro-Display-Regular.otf"), 17
            )

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
