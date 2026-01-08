"""
Main DearPyGui application for Lighthouse.

Provides the visual node editor interface using the new architecture
with dependency injection and clean separation of concerns.
"""

import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

import dearpygui.dearpygui as dpg
from rich.console import Console

from lighthouse.config import ApplicationConfig
from lighthouse.container import ServiceContainer, create_ui_container
from lighthouse.domain.models.workflow import Workflow
from lighthouse.presentation.dearpygui.node_renderer import DearPyGuiNodeRenderer
from lighthouse.presentation.dearpygui.theme_manager import ThemeManager

console = Console()


class LighthouseUI:
    """
    Main UI application for Lighthouse node editor.

    Uses the new architecture with:
    - Dependency injection via ServiceContainer
    - Clean separation of UI and business logic
    - Protocol-based abstractions
    """

    def __init__(
        self,
        title: str = "Lighthouse",
        width: int = 1400,
        height: int = 900,
        config: Optional[ApplicationConfig] = None,
        container: Optional[ServiceContainer] = None,
    ):
        """
        Initialize the Lighthouse UI.

        Args:
            title: Window title
            width: Viewport width
            height: Viewport height
            config: Application configuration
            container: Optional pre-configured service container
        """
        self.title = title
        self.width = width
        self.height = height
        self.config = config or ApplicationConfig.default()
        self.container = container or create_ui_container()

        # UI state
        self.workflow = Workflow(id="main", name="Main Workflow")
        self.edges: List[tuple] = []
        self.connections: Dict[str, List[str]] = {}
        self.node_positions: Dict[str, tuple] = {}
        self.node_last_outputs: Dict[str, Dict[str, Any]] = {}

        # Node instances (domain nodes mapped to UI)
        self.nodes: Dict[str, Any] = {}

        # Components
        self.theme_manager = ThemeManager()
        self.node_renderer: Optional[DearPyGuiNodeRenderer] = None

        # DearPyGui IDs
        self._editor_id: Optional[int] = None
        self._primary_window: Optional[int] = None

    def setup(self) -> None:
        """
        Initialize the DearPyGui context and UI components.

        Must be called before run().
        """
        # Create DearPyGui context
        dpg.create_context()

        # Setup themes
        self.theme_manager.setup_themes()

        # Setup fonts
        font_path = self._resource_path("fonts/SF-Pro-Display-Regular.otf")
        if os.path.exists(font_path):
            self.theme_manager.setup_fonts(font_path, size=17)

        # Create viewport
        dpg.create_viewport(title=self.title, width=self.width, height=self.height)

        # Setup UI components
        self._setup_ui()
        self._setup_handlers()

    def run(self) -> None:
        """Run the application main loop."""
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self._primary_window, True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def _resource_path(self, relative_path: str) -> str:
        """Get absolute path to resource (works for dev and PyInstaller)."""
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def _setup_ui(self) -> None:
        """Create the main UI layout."""
        with dpg.window(tag="primary_window") as self._primary_window:
            with dpg.tab_bar(tag="main_tab_bar"):
                # Node Editor Tab
                with dpg.tab(label="Node Editor", tag="node_editor_tab"):
                    self._setup_node_editor()

                # Execution Logs Tab
                with dpg.tab(label="Execution Logs", tag="execution_logs_tab"):
                    self._setup_execution_logs_ui()

        # Setup context menu
        self._setup_context_menu()

    def _setup_node_editor(self) -> None:
        """Setup the node editor panel."""
        with dpg.node_editor(
            callback=self._on_link,
            delink_callback=self._on_delink,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            tag="node_editor",
        ) as self._editor_id:
            pass

        # Initialize node renderer
        self.node_renderer = DearPyGuiNodeRenderer(self._editor_id)

    def _setup_context_menu(self) -> None:
        """Setup the right-click context menu for adding nodes."""
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

            # Trigger Nodes Section
            dpg.add_text("Trigger Nodes", color=(150, 150, 155))

            for node_type in self.container.node_factory.get_available_trigger_types():
                btn = dpg.add_button(
                    label=node_type.replace("_", " "),
                    callback=self._on_add_node,
                    user_data=("trigger", node_type),
                    width=200,
                )
                dpg.bind_item_theme(btn, "context_button_theme")

            dpg.add_separator()

            # Execution Nodes Section
            dpg.add_text("Execution Nodes", color=(150, 150, 155))

            for node_type in self.container.node_factory.get_available_execution_types():
                console.print(f"Creating {node_type}")
                btn = dpg.add_button(
                    label=node_type.replace("_", " "),
                    callback=self._on_add_node,
                    user_data=("execution", node_type),
                    width=200,
                )
                dpg.bind_item_theme(btn, "context_button_theme")

    def _setup_execution_logs_ui(self) -> None:
        """
        Create the Execution Logs tab UI.

        Displays execution history with hierarchical log display,
        real-time status updates, and log filtering capabilities.
        """
        with dpg.group(horizontal=False):
            # Header with controls
            with dpg.group(horizontal=True):
                dpg.add_text("Filter:", color=(150, 150, 155))
                dpg.add_button(
                    label="All",
                    tag="filter_all_btn",
                    callback=lambda: self._filter_executions("ALL"),
                    width=80,
                )
                dpg.add_button(
                    label="Running",
                    tag="filter_running_btn",
                    callback=lambda: self._filter_executions("RUNNING"),
                    width=80,
                )
                dpg.add_button(
                    label="Completed",
                    tag="filter_completed_btn",
                    callback=lambda: self._filter_executions("COMPLETED"),
                    width=80,
                )
                dpg.add_button(
                    label="Failed",
                    tag="filter_failed_btn",
                    callback=lambda: self._filter_executions("FAILED"),
                    width=80,
                )
                dpg.add_input_text(
                    label="Search",
                    tag="log_search_input",
                    hint="Search logs...",
                    width=300,
                    callback=lambda: self._search_logs(),
                )
                dpg.add_button(
                    label="Refresh",
                    tag="refresh_logs_btn",
                    callback=lambda: self._refresh_execution_logs(),
                    width=80,
                )
                dpg.add_button(
                    label="Cancel Execution",
                    tag="cancel_execution_btn",
                    callback=lambda: self._cancel_execution(),
                    width=120,
                )

            dpg.add_separator()

            # Execution logs container (scrollable)
            with dpg.child_window(tag="execution_logs_container", height=-1, border=True):
                dpg.add_text(
                    "No executions yet. Execute a workflow to see logs here.",
                    tag="no_executions_text",
                    color=(150, 150, 155),
                )

    def _filter_executions(self, filter_type: str) -> None:
        """Filter execution logs by status."""
        console.print(f"Filtering executions by: {filter_type}")
        self._refresh_execution_logs(status_filter=filter_type if filter_type != "ALL" else None)

    def _search_logs(self) -> None:
        """Search execution logs."""
        search_term = dpg.get_value("log_search_input")
        console.print(f"Searching logs for: {search_term}")

    def _refresh_execution_logs(self, status_filter: Optional[str] = None) -> None:
        """
        Refresh the execution logs display.

        Args:
            status_filter: Optional status filter (RUNNING, COMPLETED, FAILED)
        """
        # Clear existing log entries
        if dpg.does_item_exist("no_executions_text"):
            dpg.delete_item("no_executions_text")

        # Get all children of the container
        children = dpg.get_item_children("execution_logs_container", slot=1)
        if children:
            for child in children:
                if dpg.does_item_exist(child):
                    dpg.delete_item(child)

        # Get logger from container
        logger = self.container.logger
        if not logger:
            dpg.add_text(
                "Logging is disabled.",
                parent="execution_logs_container",
                tag="no_executions_text",
                color=(150, 150, 155),
            )
            return

        # Get execution history from file logger
        history = []
        if hasattr(logger, "get_execution_history"):
            history = logger.get_execution_history(limit=50)

        # Also check current session metadata if exists
        if hasattr(logger, "current_session") and logger.current_session:
            # Add current running session to the top
            current_data = logger.current_session.copy()
            history.insert(0, current_data)

        # Filter by status if specified
        if status_filter:
            history = [e for e in history if e.get("status") == status_filter]

        if not history:
            dpg.add_text(
                "No executions found.",
                parent="execution_logs_container",
                tag="no_executions_text",
                color=(150, 150, 155),
            )
            return

        # Display each execution
        for exec_data in history:
            self._create_execution_log_entry(exec_data)

    def _create_execution_log_entry(self, exec_data: Dict[str, Any]) -> None:
        """
        Create or update a collapsible execution log entry.

        Args:
            exec_data: Execution metadata dictionary
        """
        exec_id = exec_data.get("id", "unknown")
        status = exec_data.get("status", "UNKNOWN")

        # Status icons and colors
        status_icons = {
            "PENDING": "[Pending]",
            "INITIALIZING": "[Init]",
            "RUNNING": "[Running]",
            "COMPLETED": "[Done]",
            "FAILED": "[Failed]",
            "CANCELLED": "[Cancelled]",
        }

        icon = status_icons.get(status, "[?]")

        # Format duration
        duration_str = "Running..."
        if exec_data.get("duration_seconds"):
            duration = exec_data["duration_seconds"]
            if duration >= 60:
                duration_str = f"{duration / 60:.1f}m"
            else:
                duration_str = f"{duration:.1f}s"

        tree_tag = f"exec_tree_{exec_id}"

        # If the tree node already exists, delete it first to avoid conflicts
        if dpg.does_item_exist(tree_tag):
            dpg.delete_item(tree_tag)

        # Create collapsible tree node for execution
        with dpg.tree_node(
            label=f"{icon} {exec_id} | {status} | {duration_str}",
            parent="execution_logs_container",
            tag=tree_tag,
            default_open=True if status == "RUNNING" else False,
        ):
            # Summary info
            dpg.add_text(
                f"Triggered by: {exec_data.get('triggered_by', 'Unknown')[:8]}...",
                color=(120, 180, 255),
            )
            dpg.add_text(
                f"Nodes: {exec_data.get('nodes_executed', 0)}/"
                f"{exec_data.get('node_count', 0)} executed",
                color=(120, 180, 255),
            )
            if exec_data.get("nodes_failed", 0) > 0:
                dpg.add_text(f"Failed: {exec_data['nodes_failed']} nodes", color=(202, 74, 74))

            dpg.add_separator()

            # Show node logs as nested tree nodes
            node_logs = exec_data.get("node_logs", [])
            if node_logs:
                dpg.add_text("Node Executions:", color=(150, 150, 155))
                for node_log in node_logs:
                    self._create_node_log_entry(exec_id, node_log)

            dpg.add_separator()

            # Create callback closures to capture current values
            def make_summary_callback(eid: str, edata: Dict[str, Any]):
                return lambda: self._view_execution_summary(eid, edata)

            def make_errors_callback(eid: str, edata: Dict[str, Any]):
                return lambda: self._view_execution_errors(eid, edata)

            def make_log_dir_callback(ldir: str):
                return lambda: self._open_log_directory(ldir)

            # Action buttons
            with dpg.group(horizontal=True):
                # View execution summary button
                dpg.add_button(
                    label="View Summary",
                    callback=make_summary_callback(exec_id, exec_data),
                    width=120,
                )

                # View errors button (only if there are failures)
                if exec_data.get("nodes_failed", 0) > 0:
                    dpg.add_button(
                        label="View Errors",
                        callback=make_errors_callback(exec_id, exec_data),
                        width=120,
                    )

                # Open log directory button
                log_dir = exec_data.get("log_directory", "")
                if log_dir:
                    dpg.add_button(
                        label="Open Logs Dir", callback=make_log_dir_callback(log_dir), width=120
                    )

    def _create_node_log_entry(self, exec_id: str, node_log: Dict[str, Any]) -> None:
        """
        Create or update a node log entry display as a nested tree node.

        Args:
            exec_id: Execution ID
            node_log: Node log metadata dictionary
        """
        node_id = node_log.get("node_id", "unknown")
        node_name = node_log.get("node_name", "Unknown")
        status = node_log.get("status", "UNKNOWN")

        # Status icon
        status_icons = {"PENDING": "[.]", "RUNNING": "[>]", "COMPLETED": "[+]", "FAILED": "[X]"}
        icon = status_icons.get(status, "[?]")

        # Format duration
        duration_str = "-"
        if node_log.get("duration_seconds"):
            duration_str = f"{node_log['duration_seconds']:.2f}s"

        node_tree_tag = f"node_log_{exec_id}_{node_id}"

        # If the node tree already exists, delete it first to avoid conflicts
        if dpg.does_item_exist(node_tree_tag):
            dpg.delete_item(node_tree_tag)

        # Create nested tree node for node
        with dpg.tree_node(
            label=f"  {icon} {node_name} ({node_id[:8]}) | {duration_str}",
            tag=node_tree_tag,
            default_open=False,
        ):
            # Show error if present
            if node_log.get("error_message"):
                dpg.add_text(f"Error: {node_log['error_message']}", color=(202, 74, 74), wrap=600)

            # Show outputs preview if available
            outputs = node_log.get("outputs")
            if outputs:
                output_preview = str(outputs)[:200]
                if len(str(outputs)) > 200:
                    output_preview += "..."
                dpg.add_text(f"Output: {output_preview}", color=(100, 150, 200), wrap=600)

            # View details button - use closure to capture values
            def make_node_details_callback(eid: str, nlog: Dict[str, Any]):
                return lambda: self._view_node_details(eid, nlog)

            dpg.add_button(
                label="View Node Details",
                callback=make_node_details_callback(exec_id, node_log),
                width=150,
            )

    def _view_execution_summary(self, exec_id: str, exec_data: Dict[str, Any]) -> None:
        """
        View execution summary in a modal window.

        Args:
            exec_id: Execution ID
            exec_data: Execution data dictionary
        """
        viewer_tag = f"exec_summary_{exec_id}"

        if dpg.does_item_exist(viewer_tag):
            dpg.delete_item(viewer_tag)

        # Build summary content
        lines = [
            f"Execution ID: {exec_id}",
            f"Status: {exec_data.get('status', 'UNKNOWN')}",
            f"Triggered by: {exec_data.get('triggered_by', 'Unknown')}",
            "",
            f"Node Count: {exec_data.get('node_count', 0)}",
            f"Nodes Executed: {exec_data.get('nodes_executed', 0)}",
            f"Nodes Failed: {exec_data.get('nodes_failed', 0)}",
            "",
            f"Duration: {exec_data.get('duration_seconds', 0):.2f}s"
            if exec_data.get("duration_seconds")
            else "Duration: Running...",
            "",
            "=" * 50,
            "Node Execution Details:",
            "=" * 50,
        ]

        for node_log in exec_data.get("node_logs", []):
            status = node_log.get("status", "UNKNOWN")
            duration = node_log.get("duration_seconds", 0)
            lines.append("")
            lines.append(
                f"Node: {node_log.get('node_name', 'Unknown')} ({node_log.get('node_id', '')[:8]})"
            )
            lines.append(f"  Status: {status}")
            lines.append(f"  Duration: {duration:.2f}s" if duration else "  Duration: -")
            if node_log.get("error_message"):
                lines.append(f"  Error: {node_log['error_message']}")

        content = "\n".join(lines)

        with dpg.window(
            label=f"Execution Summary: {exec_id}",
            tag=viewer_tag,
            modal=False,
            show=True,
            width=700,
            height=500,
            pos=[200, 100],
        ):
            dpg.add_input_text(
                default_value=content, multiline=True, readonly=True, width=-1, height=-50
            )
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item(viewer_tag), width=-1)

    def _view_execution_errors(self, exec_id: str, exec_data: Dict[str, Any]) -> None:
        """
        View execution errors in a modal window.

        Args:
            exec_id: Execution ID
            exec_data: Execution data dictionary
        """
        viewer_tag = f"exec_errors_{exec_id}"

        if dpg.does_item_exist(viewer_tag):
            dpg.delete_item(viewer_tag)

        # Build error content
        lines = [
            f"Execution Errors for: {exec_id}",
            "",
            "=" * 50,
        ]

        for node_log in exec_data.get("node_logs", []):
            if node_log.get("error_message"):
                lines.append("")
                lines.append(
                    f"Node: {node_log.get('node_name', 'Unknown')} "
                    f"({node_log.get('node_id', '')[:8]})"
                )
                lines.append(f"Error: {node_log['error_message']}")
                lines.append("-" * 30)

        if len(lines) == 3:
            lines.append("")
            lines.append("No errors found.")

        content = "\n".join(lines)

        with dpg.window(
            label=f"Execution Errors: {exec_id}",
            tag=viewer_tag,
            modal=False,
            show=True,
            width=700,
            height=400,
            pos=[250, 150],
        ):
            dpg.add_input_text(
                default_value=content, multiline=True, readonly=True, width=-1, height=-50
            )
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item(viewer_tag), width=-1)

    def _view_node_details(self, exec_id: str, node_log: Dict[str, Any]) -> None:
        """
        View node execution details in a modal window.

        Args:
            exec_id: Execution ID
            node_log: Node log data
        """
        node_id = node_log.get("node_id", "unknown")
        viewer_tag = f"node_details_{exec_id}_{node_id}"

        if dpg.does_item_exist(viewer_tag):
            dpg.delete_item(viewer_tag)

        # Build details content
        import json

        lines = [
            "Node Execution Details",
            "",
            f"Execution ID: {exec_id}",
            f"Node ID: {node_id}",
            f"Node Name: {node_log.get('node_name', 'Unknown')}",
            f"Status: {node_log.get('status', 'UNKNOWN')}",
            f"Duration: {node_log.get('duration_seconds', 0):.2f}s"
            if node_log.get("duration_seconds")
            else "Duration: -",
            "",
        ]

        if node_log.get("error_message"):
            lines.append("=" * 50)
            lines.append("ERROR:")
            lines.append(node_log["error_message"])
            lines.append("")

        if node_log.get("outputs"):
            lines.append("=" * 50)
            lines.append("OUTPUTS:")
            try:
                outputs_str = json.dumps(node_log["outputs"], indent=2)
            except Exception:
                outputs_str = str(node_log["outputs"])
            lines.append(outputs_str)

        content = "\n".join(lines)

        with dpg.window(
            label=f"Node Details: {node_log.get('node_name', 'Unknown')}",
            tag=viewer_tag,
            modal=False,
            show=True,
            width=600,
            height=450,
            pos=[300, 120],
        ):
            dpg.add_input_text(
                default_value=content, multiline=True, readonly=True, width=-1, height=-50
            )
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item(viewer_tag), width=-1)

    def _view_log_file(self, exec_id: str, filename: str) -> None:
        """
        View a log file in a modal window.

        Args:
            exec_id: Execution ID
            filename: Name of the log file
        """
        # Create or update log viewer window
        viewer_tag = f"log_viewer_{exec_id}_{filename}"

        if dpg.does_item_exist(viewer_tag):
            dpg.delete_item(viewer_tag)

        # Try to read log file
        log_dir = os.path.join(".logs", exec_id)
        log_path = os.path.join(log_dir, filename)

        content = "Log file not found."
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                content = f.read()

        with dpg.window(
            label=f"Log: {filename}",
            tag=viewer_tag,
            modal=False,
            show=True,
            width=800,
            height=600,
            pos=[200, 100],
        ):
            dpg.add_input_text(
                default_value=content, multiline=True, readonly=True, width=-1, height=-50
            )
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item(viewer_tag), width=-1)

    def _open_log_directory(self, log_dir: str) -> None:
        """
        Open the log directory in the system file explorer.

        Args:
            log_dir: Path to the log directory
        """
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
        """Setup input handlers."""
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(
                button=dpg.mvMouseButton_Right, callback=self._on_right_click
            )

    def _on_right_click(self, sender, app_data) -> None:
        """Handle right-click for context menu."""
        mouse_pos = dpg.get_mouse_pos(local=False)
        dpg.configure_item("context_menu", show=True, pos=mouse_pos)

    def _on_add_node(self, sender, app_data, user_data) -> None:
        """Handle adding a new node."""
        node_category, node_type = user_data
        dpg.configure_item("context_menu", show=False)

        try:
            # Create node using factory
            node = self.container.node_factory.create_node(node_type)

            # Add to workflow
            self.workflow.add_node(node)

            # Store node reference
            self.nodes[node.id] = node

            # Get position for new node
            mouse_pos = dpg.get_mouse_pos(local=False)
            position = (mouse_pos[0] - 100, mouse_pos[1] - 50)

            # Render in editor
            callbacks = {
                "on_edit": self._on_edit_node,
                "on_execute": self._on_execute_node,
                "on_delete": self._on_delete_node,
                "on_save": self._on_save_node,
                "on_rename": self._on_rename_node,
            }
            self.node_renderer.render_node(node, position, callbacks)

            console.print(f"[green]Added {node_type} node: {node.id[-8:]}[/green]")

        except Exception as e:
            console.print(f"[red]Failed to create node {node_type}: {e}[/red]")

    def _on_link(self, sender, app_data) -> None:
        """Handle node linking."""
        source_attr, target_attr = app_data
        source_attr = dpg.get_item_alias(source_attr)
        target_attr = dpg.get_item_alias(target_attr)

        self.edges.append((source_attr, target_attr))

        # Create visual link
        dpg.add_node_link(
            source_attr, target_attr, parent=sender, tag=f"{source_attr}_{target_attr}"
        )

        # Update connections
        target_node_id = target_attr.split("_")[0]
        source_node_id = source_attr.split("_")[0]

        if target_node_id in self.connections:
            self.connections[target_node_id].append(source_node_id)
        else:
            self.connections[target_node_id] = [source_node_id]

        # Update workflow connections
        self.workflow.add_connection(source_node_id, target_node_id)

    def _on_delink(self, sender, app_data) -> None:
        """Handle node delinking."""
        edge = dpg.get_item_configuration(item=app_data)

        source_full = dpg.get_item_alias(edge["attr_1"])
        source_id = source_full.split("_")[0]
        target_full = dpg.get_item_alias(edge["attr_2"])
        target_id = target_full.split("_")[0]

        # Remove from connections
        if target_id in self.connections:
            self.connections[target_id] = [i for i in self.connections[target_id] if i != source_id]

        # Remove from workflow
        self.workflow.remove_connection(source_id, target_id)

        # Remove edge tracking
        self.edges = [e for e in self.edges if not (e[0] == source_full and e[1] == target_full)]

        dpg.delete_item(app_data)

    def _on_edit_node(self, sender, app_data, user_data) -> None:
        """Handle node edit button click."""
        node_id = user_data
        node = self.nodes.get(node_id)
        if node:
            console.print(f"Edit node: {node.name} ({node_id})")
            # Inspector is opened by the renderer's Edit button callback

    def _on_save_node(self, sender, app_data, user_data) -> None:
        """Handle saving node inspector changes (called after renderer saves)."""
        node_id = user_data
        node = self.nodes.get(node_id)
        if node:
            # Renderer already updated the node state
            # This callback is for any additional app-level processing
            console.print(f"[cyan]App notified of save: {node.name}[/cyan]")

    def _on_rename_node(self, sender, app_data, user_data) -> None:
        """Handle renaming a node."""
        node_id, new_name = user_data
        node = self.nodes.get(node_id)
        if node:
            node.name = new_name
            console.print(f"[cyan]Renamed node {node_id} to: {new_name}[/cyan]")

    def _get_node_state_preview(self, node) -> str:
        """Get a preview string of a node's state for display."""
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

    def _on_execute_node(self, sender, app_data, user_data) -> None:
        """Handle node execute button click."""
        node_id = user_data
        console.print(f"ENGINE: Attempting to start execution from {node_id}")
        self._exec_graph(node_id)

    def _on_delete_node(self, sender, app_data, user_data) -> None:
        """Handle node delete button click."""
        node_id = user_data

        # Remove from workflow
        self.workflow.remove_node(node_id)

        # Remove from local tracking
        self.nodes.pop(node_id, None)
        self.connections.pop(node_id, None)
        self.node_last_outputs.pop(node_id, None)

        # Remove this node from other nodes' connection lists
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

        # Remove from UI
        self.node_renderer.remove_node(node_id)

    def _topo_sort(self) -> List[str]:
        """Perform topological sort on the node graph."""
        in_degree = {}
        for n_id in self.nodes:
            if n_id in self.connections:
                in_degree[n_id] = len(self.connections[n_id])
            else:
                in_degree[n_id] = 0

        # Build adjacency list (outgoing connections)
        outgoing = {n_id: [] for n_id in self.nodes}
        for target_node, source_nodes in self.connections.items():
            for source_node in source_nodes:
                if source_node in outgoing:
                    outgoing[source_node].append(target_node)

        # Start with nodes that have no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # For each node that current points to
            for neighbor in outgoing[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(result) != len(self.nodes):
            console.print("[yellow]Warning: Cycle detected in graph![/yellow]")
            return list(self.nodes.keys())

        return result

    def _set_exec_status(self, node_id: str, color: tuple, status: str) -> None:
        """Set the execution status display for a node."""
        if node_id in self.nodes:
            self.nodes[node_id].status = status

        # Update UI status display
        status_tag = f"{node_id}_exec_status"
        loading_tag = f"{node_id}_loading"

        if dpg.does_item_exist(status_tag):
            dpg.set_value(item=status_tag, value=status)
            dpg.configure_item(item=status_tag, color=color)

        if dpg.does_item_exist(loading_tag):
            if status == "RUNNING":
                dpg.configure_item(item=loading_tag, show=True, color=color)
            else:
                dpg.configure_item(item=loading_tag, show=False)

    def _execute_step(self, node_id: str) -> None:
        """Execute a single node step."""
        node = self.nodes.get(node_id)
        if not node:
            console.print(f"[red]Node {node_id} not found[/red]")
            return

        self._set_exec_status(node_id, (194, 188, 81), "RUNNING")

        # Log node start
        execution_manager = self.container.execution_manager
        try:
            execution_manager.log_node_start(node_id, node.name, node_type=node.__class__.__name__)
        except RuntimeError:
            pass  # No active session

        # Refresh logs to show node started
        self._refresh_execution_logs()

        try:
            # Get expression service for resolving expressions
            expr_service = self.container.expression_service

            # Build context from completed nodes
            context = self._build_execution_context()

            # Resolve expressions in node state
            resolved_state = expr_service.resolve_dict(node.state.copy(), context)

            # Temporarily replace node state with resolved values
            original_state = node.state
            node.state = resolved_state

            # Execute the node
            result = node.execute(context)

            # Restore original state
            node.state = original_state

            if result.success:
                # Store output for context building
                self.node_last_outputs[node_id] = {"data": result.data}
                self._set_exec_status(node_id, (83, 202, 74), "COMPLETED")
                console.print(f"[green]Node {node.name} completed[/green]")

                # Log node success
                try:
                    execution_manager.log_node_end(node_id, "COMPLETED", output_data=result.data)
                    execution_manager.set_node_context(node_id, node.name, result.data)
                except (RuntimeError, KeyError):
                    pass
            else:
                self._set_exec_status(node_id, (202, 74, 74), "ERROR")
                console.print(f"[red]Node {node.name} failed: {result.error}[/red]")

                # Log node failure
                try:
                    execution_manager.log_node_end(node_id, "FAILED", error_message=result.error)
                except (RuntimeError, KeyError):
                    pass

        except Exception as e:
            self._set_exec_status(node_id, (202, 74, 74), "ERROR")
            console.print(f"[red]Node {node_id} failed: {e}[/red]")

            # Log node failure
            try:
                execution_manager.log_node_end(node_id, "FAILED", error_message=str(e))
            except (RuntimeError, KeyError):
                pass

    def _build_execution_context(self) -> Dict[str, Any]:
        """Build execution context from completed nodes."""
        context = {}
        for node_id, output in self.node_last_outputs.items():
            node = self.nodes.get(node_id)
            if node:
                context[node.name] = output
        return context

    def _build_context_from_completed_nodes(self, execution_order: List[str]) -> None:
        """
        Build the execution context from all completed nodes.

        Args:
            execution_order: List of node IDs in execution order
        """
        console.print("[cyan]Building context from completed nodes...[/cyan]")

        for nid in execution_order:
            node = self.nodes.get(nid)
            if not node:
                continue

            # If node is completed, use its stored output
            if node.status == "COMPLETED":
                if nid in self.node_last_outputs:
                    console.print(f"[cyan]Context has: {node.name} ({nid[:8]})[/cyan]")
                else:
                    # Execute to get output
                    try:
                        context = self._build_execution_context()
                        result = node.execute(context)
                        if result.success:
                            self.node_last_outputs[nid] = {"data": result.data}
                            console.print(
                                f"[cyan]Executed and added to context: {node.name} "
                                f"({nid[:8]})[/cyan]"
                            )
                    except Exception as e:
                        console.print(
                            f"[yellow]Warning: Could not get output from {node.name}: {e}[/yellow]"
                        )

        console.print(f"[cyan]Context built with {len(self.node_last_outputs)} nodes[/cyan]")

    def _exec_graph(self, trigger_node_id: str) -> None:
        """Execute the workflow graph starting from a trigger node in a separate thread."""
        console.print(f"ENGINE: Starting async execution from {trigger_node_id}")

        # Check if already executing
        if self.container.workflow_orchestrator.is_executing():
            console.print("[yellow]Execution already in progress. Please wait...[/yellow]")
            return

        try:
            # Execute workflow asynchronously
            self.container.workflow_orchestrator.execute_workflow_async(
                workflow=self.workflow,
                triggered_by=trigger_node_id,
                on_node_start=self._on_async_node_start,
                on_node_complete=self._on_async_node_complete,
                on_node_error=self._on_async_node_error,
                on_complete=self._on_async_execution_complete,
            )

            # Initial log refresh
            self._refresh_execution_logs()

        except Exception as e:
            console.print(f"[red]Failed to start execution: {e}[/red]")

    def _on_async_node_start(self, node_id: str, node_name: str) -> None:
        """
        Callback when a node starts execution (called from worker thread).

        Args:
            node_id: ID of the node starting
            node_name: Name of the node
        """
        console.print(f"[cyan]Node starting: {node_name} ({node_id[:8]})[/cyan]")
        self._set_exec_status(node_id, (194, 188, 81), "RUNNING")

        # Refresh logs to show node started (safe to call from thread)
        if dpg.does_item_exist("execution_logs_tab"):
            dpg.set_frame_callback(
                dpg.get_frame_count() + 1, lambda: self._refresh_execution_logs()
            )

    def _on_async_node_complete(self, node_id: str, result: Any) -> None:
        """
        Callback when a node completes successfully (called from worker thread).

        Args:
            node_id: ID of the completed node
            result: Execution result from the node
        """
        node = self.nodes.get(node_id)
        node_name = node.name if node else node_id[:8]

        console.print(f"[green]Node completed: {node_name} ({node_id[:8]})[/green]")

        # Store output for context building
        if result.success and result.data:
            self.node_last_outputs[node_id] = {"data": result.data}

        # Update UI (must be done on main thread via frame callback)
        self._set_exec_status(node_id, (83, 202, 74), "COMPLETED")

        # Schedule log refresh for next frame
        if dpg.does_item_exist("execution_logs_tab"):
            dpg.set_frame_callback(
                dpg.get_frame_count() + 1, lambda: self._refresh_execution_logs()
            )

    def _on_async_node_error(self, node_id: str, error: str) -> None:
        """
        Callback when a node fails (called from worker thread).

        Args:
            node_id: ID of the failed node
            error: Error message
        """
        node = self.nodes.get(node_id)
        node_name = node.name if node else node_id[:8]

        console.print(f"[red]Node failed: {node_name} ({node_id[:8]}): {error}[/red]")

        # Update UI (must be done on main thread via frame callback)
        self._set_exec_status(node_id, (202, 74, 74), "ERROR")

        # Schedule log refresh for next frame
        if dpg.does_item_exist("execution_logs_tab"):
            dpg.set_frame_callback(
                dpg.get_frame_count() + 1, lambda: self._refresh_execution_logs()
            )

    def _on_async_execution_complete(self, result: Dict[str, Any]) -> None:
        """
        Callback when entire workflow execution completes (called from worker thread).

        Args:
            result: Final execution result
        """
        status = result.get("status", "UNKNOWN")
        session_id = result.get("session_id", "N/A")

        console.print(f"[cyan]Execution complete: {status} (session: {session_id})[/cyan]")

        # Schedule final log refresh for next frame
        if dpg.does_item_exist("execution_logs_tab"):
            dpg.set_frame_callback(
                dpg.get_frame_count() + 1, lambda: self._refresh_execution_logs()
            )

    def _cancel_execution(self) -> None:
        """Cancel the currently running workflow execution."""
        if self.container.workflow_orchestrator.is_executing():
            console.print("[yellow]Cancelling workflow execution...[/yellow]")
            self.container.workflow_orchestrator.cancel_execution()
        else:
            console.print("[yellow]No execution in progress to cancel.[/yellow]")

    def _update_logs(self, result: Dict[str, Any]) -> None:
        """Update the logs panel with execution results."""
        status = result.get("status", "UNKNOWN")
        session_id = result.get("session_id", "N/A")

        log_text = f"[{session_id}] Status: {status}\n"

        for node_id, node_result in result.get("results", {}).items():
            if node_result.success:
                log_text += f"  - {node_id}: SUCCESS\n"
            else:
                log_text += f"  - {node_id}: FAILED - {node_result.error}\n"

        if dpg.does_item_exist("logs_content"):
            current = dpg.get_value("logs_content")
            dpg.set_value("logs_content", log_text + "\n" + current)

    def _log_error(self, error: str) -> None:
        """Log an error to the logs panel."""
        if dpg.does_item_exist("logs_content"):
            current = dpg.get_value("logs_content")
            dpg.set_value("logs_content", f"[ERROR] {error}\n" + current)


def run_app():
    """Entry point for running the new Lighthouse UI."""
    app = LighthouseUI()
    app.setup()
    app.run()


if __name__ == "__main__":
    run_app()
