from .executor import *

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

        # Store last outputs for context building
        self.node_last_outputs: Dict[str, Dict[str, Any]] = {}

        self.executor = Executor()

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

        # with dpg.viewport_menu_bar():
        #     with dpg.menu(label="File"):
        #         dpg.add_menu_item(label="Save", callback=print_me)
        #         dpg.add_menu_item(label="Exit", callback=dpg.destroy_context)

        #         with dpg.menu(label="Settings"):
        #             dpg.add_menu_item(label="Setting 1", callback=print_me, check=True)
        #             dpg.add_menu_item(label="Setting 2", callback=print_me)

        #     with dpg.menu(label="Widget Items"):
        #         dpg.add_checkbox(label="Pick Me", callback=print_me)
        #         dpg.add_button(label="Press Me", callback=print_me)
        #         dpg.add_color_picker(label="Color Me", callback=print_me)

        #     with dpg.menu(label="Help"):
        #         dpg.add_text("Usage Tips")
        #         dpg.add_text("  Left-Click to add new nodes")
        #         dpg.add_text("  Ctrl-Click to delete node connection")
        #         dpg.add_separator()
        #         dpg.add_text("About")
        #         dpg.add_text("  RayB - Dec '25")
        #         dpg.add_text("  Version: 0.1")

        # ----------------------------------------------------------------
        # Primary window containing tabs for Node Editor and Execution Logs
        # ----------------------------------------------------------------
        with dpg.window(label=self.title, tag="primary_window"):
            with dpg.tab_bar(tag="main_tab_bar"):
                # ================================================================
                # Node Editor Tab
                # ================================================================
                with dpg.tab(label="Node Editor", tag="node_editor_tab"):
                    # Node editor with minimap enabled
                    with dpg.node_editor(
                        callback=self.link_callback,
                        delink_callback=self.delink_callback,
                        minimap=True,
                        minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
                        tag="node_editor",
                    ):
                        pass

                # ================================================================
                # Execution Logs Tab
                # ================================================================
                with dpg.tab(label="Execution Logs", tag="execution_logs_tab"):
                    self._setup_execution_logs_ui()
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

    def _setup_execution_logs_ui(self) -> None:
        """
        Create the Execution Logs tab UI.
        
        Displays execution history with hierarchical log display,
        real-time status updates, and log filtering capabilities.
        """
        with dpg.group(horizontal=False):
            # ----------------------------------------------------------------
            # Header with controls
            # ----------------------------------------------------------------
            with dpg.group(horizontal=True):
                dpg.add_text("Filter:", color=(150, 150, 155))
                dpg.add_button(
                    label="All",
                    tag="filter_all_btn",
                    callback=lambda: self._filter_executions("ALL"),
                    width=80
                )
                dpg.add_button(
                    label="Running",
                    tag="filter_running_btn",
                    callback=lambda: self._filter_executions("RUNNING"),
                    width=80
                )
                dpg.add_button(
                    label="Completed",
                    tag="filter_completed_btn",
                    callback=lambda: self._filter_executions("COMPLETED"),
                    width=80
                )
                dpg.add_button(
                    label="Failed",
                    tag="filter_failed_btn",
                    callback=lambda: self._filter_executions("FAILED"),
                    width=80
                )
                dpg.add_input_text(
                    label="Search",
                    tag="log_search_input",
                    hint="Search logs...",
                    width=300,
                    callback=lambda: self._search_logs()
                )
                dpg.add_button(
                    label="Refresh",
                    tag="refresh_logs_btn",
                    callback=lambda: self._refresh_execution_logs(),
                    width=80
                )

            dpg.add_separator()

            # ----------------------------------------------------------------
            # Execution logs container (scrollable)
            # ----------------------------------------------------------------
            with dpg.child_window(
                tag="execution_logs_container",
                height=-1,
                border=True
            ):
                dpg.add_text(
                    "No executions yet. Execute a workflow to see logs here.",
                    tag="no_executions_text",
                    color=(150, 150, 155)
                )

    def _filter_executions(self, filter_type: str) -> None:
        """Filter execution logs by status."""
        console.print(f"Filtering executions by: {filter_type}")
        self._refresh_execution_logs(status_filter=filter_type if filter_type != "ALL" else None)

    def _search_logs(self) -> None:
        """Search execution logs."""
        search_term = dpg.get_value("log_search_input")
        console.print(f"Searching logs for: {search_term}")
        # TODO: Implement search functionality

    def _refresh_execution_logs(self, status_filter: str = None) -> None:
        """
        Refresh the execution logs display.
        
        Args:
            status_filter: Optional status filter (RUNNING, COMPLETED, FAILED)
        """
        if not self.executor.logging_service:
            return

        # Clear existing log entries (but keep the header)
        if dpg.does_item_exist("no_executions_text"):
            dpg.delete_item("no_executions_text")

        # Get all children of the container except the filter controls
        children = dpg.get_item_children("execution_logs_container", slot=1)
        if children:
            for child in children:
                if dpg.does_item_exist(child):
                    dpg.delete_item(child)

        # Get execution history
        history = self.executor.logging_service.get_execution_history(
            limit=50,
            status_filter=status_filter
        )

        # Also check for current running execution
        current_session = self.executor.logging_service.get_current_session()
        if current_session:
            history.insert(0, current_session)

        if not history:
            dpg.add_text(
                "No executions found.",
                parent="execution_logs_container",
                tag="no_executions_text",
                color=(150, 150, 155)
            )
            return

        # Display each execution
        for exec_data in history:
            self._create_execution_log_entry(exec_data)

    def _create_execution_log_entry(self, exec_data: Dict[str, Any]) -> None:
        """
        Create a collapsible execution log entry.
        
        Args:
            exec_data: Execution metadata dictionary
        """
        exec_id = exec_data["id"]
        status = exec_data["status"]

        # Status icon and color
        status_icons = {
            "INITIALIZING": "Pause",
            "RUNNING": "Running",
            "COMPLETED": "Completed",
            "FAILED": "Failed",
            "CANCELLED": "Cancelled"
        }
        status_colors = {
            "INITIALIZING": (150, 150, 150),
            "RUNNING": (194, 188, 81),
            "COMPLETED": (83, 202, 74),
            "FAILED": (202, 74, 74),
            "CANCELLED": (150, 150, 150)
        }

        icon = status_icons.get(status, "Pause")
        color = status_colors.get(status, (150, 150, 150))

        # Format duration
        duration_str = "Running..."
        if exec_data.get("duration_seconds"):
            duration = exec_data["duration_seconds"]
            if duration >= 60:
                duration_str = f"{duration/60:.1f}m"
            else:
                duration_str = f"{duration:.1f}s"

        # Create collapsible tree node for execution
        with dpg.tree_node(
            label=f"{icon} {exec_id} | {status} | {duration_str}",
            parent="execution_logs_container",
            tag=f"exec_tree_{exec_id}",
            default_open=False
        ):
            dpg.add_text(
                f"Triggered by: {exec_data['triggered_by']}",
                color=(120, 180, 255)
            )
            dpg.add_text(
                f"Nodes: {exec_data['nodes_executed']}/{exec_data['node_count']} executed",
                color=(120, 180, 255)
            )
            if exec_data.get("nodes_failed", 0) > 0:
                dpg.add_text(
                    f"Failed: {exec_data['nodes_failed']} nodes",
                    color=(202, 74, 74)
                )

            dpg.add_separator()

            # Show node logs if available
            node_logs = exec_data.get("node_logs", [])
            if node_logs:
                dpg.add_text("Node Executions:", color=(150, 150, 155))
                for node_log in node_logs:
                    self._create_node_log_entry(exec_id, node_log)

            dpg.add_separator()

            # Buttons to view logs
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="View Summary Log",
                    callback=lambda: self._view_log_file(exec_id, "execution_summary.log"),
                    width=150
                )
                if exec_data.get("nodes_failed", 0) > 0:
                    dpg.add_button(
                        label="View Errors",
                        callback=lambda: self._view_log_file(exec_id, "errors.log"),
                        width=150
                    )
                dpg.add_button(
                    label="Open Log Directory",
                    callback=lambda: self._open_log_directory(exec_data["log_directory"]),
                    width=150
                )

    def _create_node_log_entry(self, exec_id: str, node_log: Dict[str, Any]) -> None:
        """
        Create a node log entry display.
        
        Args:
            exec_id: Execution ID
            node_log: Node log metadata dictionary
        """
        node_id = node_log["node_id"]
        node_name = node_log["node_name"]
        status = node_log["status"]

        # Status icon and color
        status_icons = {"RUNNING": "Running", "COMPLETED": "Completed", "FAILED": "Failed"}
        icon = status_icons.get(status, "Pause")

        # Format duration
        duration_str = "-"
        if node_log.get("duration_seconds"):
            duration_str = f"{node_log['duration_seconds']:.2f}s"

        with dpg.tree_node(
            label=f"  {icon} {node_name} ({node_id[:8]}) | {duration_str}",
            tag=f"node_log_{exec_id}_{node_id}",
            default_open=False
        ):
            if node_log.get("error_message"):
                dpg.add_text(
                    f"Error: {node_log['error_message']}",
                    color=(202, 74, 74),
                    wrap=600
                )

            dpg.add_button(
                label="View Node Log",
                callback=lambda: self._view_log_file(exec_id, node_log["log_file"]),
                width=150
            )

    def _view_log_file(self, exec_id: str, filename: str) -> None:
        """
        View a log file in a modal window.
        
        Args:
            exec_id: Execution ID
            filename: Name of the log file
        """
        if not self.executor.logging_service:
            return

        # Read log file content
        content = self.executor.logging_service.read_log_file(exec_id, filename)

        # Create or update log viewer window
        viewer_tag = f"log_viewer_{exec_id}_{filename}"

        if dpg.does_item_exist(viewer_tag):
            dpg.delete_item(viewer_tag)

        with dpg.window(
            label=f"Log: {filename}",
            tag=viewer_tag,
            modal=False,
            show=True,
            width=800,
            height=600,
            pos=[200, 100]
        ):
            dpg.add_input_text(
                default_value=content,
                multiline=True,
                readonly=True,
                width=-1,
                height=-50
            )
            dpg.add_button(
                label="Close",
                callback=lambda: dpg.delete_item(viewer_tag),
                width=-1
            )

    def _open_log_directory(self, log_dir: str) -> None:
        """
        Open the log directory in the system file explorer.
        
        Args:
            log_dir: Path to the log directory
        """
        import subprocess
        import sys

        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", log_dir])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["explorer", log_dir])
            else:  # Linux
                subprocess.run(["xdg-open", log_dir])
        except Exception as e:
            console.print(f"[red]Failed to open directory: {e}[/red]")

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
        node = self.nodes[node_id]
        self._set_exec_status(node_id, (194, 188, 81), "RUNNING")

        # Log node execution start
        self.executor.log_node_start(
            node_id,
            node.name,
            node.__class__.__name__
        )

        try:
            # Get expression engine
            expr_engine = self.executor.get_expression_engine()

            # Resolve expressions in node state before execution
            resolved_state = expr_engine.resolve_dict(node.state.copy())

            # Temporarily replace node state with resolved values
            original_state = node.state
            node.state = resolved_state

            # Simulate execution time
            time.sleep(1)

            # Execute the node and capture output
            output = node.execute()

            # Restore original state (with expressions)
            node.state = original_state

            # Store node output in context for downstream nodes
            self.executor.set_node_context(node_id, node.name, output.get("data", {}))

            # Store last output for future context building
            self.node_last_outputs[node_id] = output

            # Log node execution completion
            self.executor.log_node_end(node_id, "COMPLETED", output)
            self._set_exec_status(node_id, (83, 202, 74), "COMPLETED")

        except Exception as e:
            # Log node execution failure
            error_msg = str(e)
            self.executor.log_node_end(node_id, "FAILED", error_message=error_msg)
            self._set_exec_status(node_id, (202, 74, 74), "ERROR")
            console.print(f"[red]Node {node_id} failed: {error_msg}[/red]")

    def _exec_graph(self, node_id):

        # Clear context before starting new execution
        self.executor.clear_context()

        execution_order = self._topo_sort()
        console.print(execution_order)
        execution_nodes = [self.nodes[i] for i in execution_order]

        self.executor.create_execution(execution_nodes, self.connections, node_id)

        # First, build context from all completed nodes
        self._build_context_from_completed_nodes(execution_order)

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

        self.executor.end_execution()

    def _build_context_from_completed_nodes(self, execution_order):
        """
        Build the execution context from all completed nodes.
        
        This ensures that expressions can reference outputs from nodes
        that were executed in previous runs.
        
        Args:
            execution_order: List of node IDs in execution order
        """
        console.print("[cyan]Building context from completed nodes...[/cyan]")

        for nid in execution_order:
            node = self.nodes[nid]

            # If node is completed, use its stored output
            if node.status == "COMPLETED":
                try:
                    # Get the stored last output
                    if nid in self.node_last_outputs:
                        output = self.node_last_outputs[nid]
                        data = output.get("data", {})

                        # Add to context
                        self.executor.set_node_context(nid, node.name, data)

                        console.print(f"[cyan]Added to context: {node.name} ({nid[:8]})[/cyan]")
                    else:
                        # No stored output, try to execute the node
                        output = node.execute()
                        data = output.get("data", {})

                        # Add to context
                        self.executor.set_node_context(nid, node.name, data)

                        # Store the output for future use
                        self.node_last_outputs[nid] = output

                        console.print(f"[cyan]Executed and added to context: {node.name} ({nid[:8]})[/cyan]")

                except Exception as e:
                    console.print(f"[yellow]Warning: Could not get output from {node.name} ({nid[:8]}): {e}[/yellow]")
                    # Add empty data to context to prevent expression errors
                    self.executor.set_node_context(nid, node.name, {})

        console.print(
            f"[cyan]Context built with {len(self.executor.node_context)} nodes - {self.executor.node_context}[/cyan]"
        )

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
