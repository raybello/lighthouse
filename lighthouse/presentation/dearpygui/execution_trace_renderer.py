"""
Execution trace renderer for visualizing workflow execution timelines.

Renders Gantt-style charts showing node execution timing using DearPyGui plots.
"""

import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import dearpygui.dearpygui as dpg


@dataclass
class TraceBounds:
    """Bounds for a trace image in plot coordinates."""

    min_x: float  # Start time (seconds)
    max_x: float  # End time (seconds)
    min_y: float  # Level - 0.5
    max_y: float  # Level + 0.5
    node_name: str
    node_type: str
    node_id: str
    duration_seconds: float
    level: int
    success: bool = True
    error: Optional[str] = None


class ExecutionTraceRenderer:
    """
    Renders execution trace graphs using DearPyGui plots.

    Creates a Gantt-style timeline visualization showing:
    - Each node as a colored bar on the timeline
    - Node type indicated by color
    - Execution level on Y-axis
    - Time in seconds on X-axis
    - Hover tooltips with node details
    """

    # Color definitions for node types (RGBA normalized 0-1)
    NODE_TYPE_COLORS: Dict[str, Tuple[float, float, float, float]] = {
        "Input": (0.13, 0.78, 0.13, 1.0),  # Green for triggers
        "ManualTrigger": (0.13, 0.78, 0.13, 1.0),  # Green
        "Calculator": (1.0, 0.78, 0.0, 1.0),  # Yellow/Gold
        "HTTPRequest": (0.0, 0.59, 1.0, 1.0),  # Blue for network
        "Code": (0.78, 0.39, 1.0, 1.0),  # Purple
        "ExecuteCommand": (1.0, 0.5, 0.0, 1.0),  # Orange
        "ChatModel": (0.0, 0.8, 0.8, 1.0),  # Cyan
        "Form": (0.9, 0.4, 0.6, 1.0),  # Pink
        "default": (0.6, 0.6, 0.6, 1.0),  # Gray for unknown
    }

    # Texture size for trace bars
    TEXTURE_SIZE = 32

    def __init__(self):
        """Initialize the execution trace renderer."""
        self._textures: Dict[str, str] = {}
        self._texture_registry_tag: Optional[str] = None
        self._trace_bounds: List[TraceBounds] = []
        self._handler_registry_tag: Optional[str] = None
        self._tooltip_tag: Optional[str] = None
        self._plot_tag: Optional[str] = None
        self._instance_id: Optional[str] = None

    def _generate_unique_id(self) -> str:
        """Generate a unique ID for this render instance."""
        self._instance_id = uuid.uuid4().hex[:8]
        return self._instance_id

    def _create_texture_data(self, color: Tuple[float, float, float, float]) -> List[float]:
        """
        Create texture data for a solid color.

        Args:
            color: RGBA color tuple (0-1 range)

        Returns:
            Flat list of RGBA values for the texture
        """
        size = self.TEXTURE_SIZE
        r, g, b, a = color

        # Create solid color texture
        texture_data = []
        for _ in range(size * size):
            texture_data.extend([r, g, b, a])

        return texture_data

    def _create_textures(self, instance_id: str) -> None:
        """Create static textures for each node type."""
        self._texture_registry_tag = f"trace_texture_registry_{instance_id}"

        if dpg.does_item_exist(self._texture_registry_tag):
            dpg.delete_item(self._texture_registry_tag)

        dpg.add_texture_registry(tag=self._texture_registry_tag)

        # Create texture for each node type
        for node_type, color in self.NODE_TYPE_COLORS.items():
            texture_tag = f"trace_texture_{node_type}_{instance_id}"
            texture_data = self._create_texture_data(color)

            dpg.add_static_texture(
                self.TEXTURE_SIZE,
                self.TEXTURE_SIZE,
                texture_data,
                parent=self._texture_registry_tag,
                tag=texture_tag,
            )
            self._textures[node_type] = texture_tag

    def _get_texture_for_node_type(self, node_type: str) -> str:
        """
        Get the texture tag for a node type.

        Args:
            node_type: The node type name

        Returns:
            Texture tag string
        """
        if node_type in self._textures:
            return self._textures[node_type]
        return self._textures.get("default", "")

    def calculate_trace_bounds(
        self, traces: List[Dict[str, Any]]
    ) -> Tuple[List[TraceBounds], List[str]]:
        """
        Calculate image bounds for each trace in waterfall layout.

        Each node gets its own row. Nodes are sorted by start time, and
        parallel nodes are stacked vertically creating a waterfall effect.

        Args:
            traces: List of trace dictionaries with timing data

        Returns:
            Tuple of (List of TraceBounds, List of node names for Y-axis labels)
        """
        if not traces:
            return [], []

        # Sort traces by start time, then by node name for consistent ordering
        sorted_traces = sorted(
            traces, key=lambda t: (t.get("relative_start_seconds", 0.0), t.get("node_name", ""))
        )

        bounds_list = []
        node_labels = []  # For Y-axis ticks

        # Assign each trace its own row (waterfall style)
        for level, trace in enumerate(sorted_traces):
            start_time = trace.get("relative_start_seconds", 0.0)
            end_time = trace.get("relative_end_seconds", start_time)
            duration = trace.get("duration_seconds", end_time - start_time)
            node_type = trace.get("node_type", "Unknown")
            node_name = trace.get("node_name", "Unknown")

            # Ensure minimum width for visibility
            if end_time - start_time < 0.001:
                end_time = start_time + max(duration, 0.01)

            bounds = TraceBounds(
                min_x=start_time,
                max_x=end_time,
                min_y=level - 0.4,
                max_y=level + 0.4,
                node_name=node_name,
                node_type=node_type,
                node_id=trace.get("node_id", ""),
                duration_seconds=duration,
                level=level,
                success=trace.get("status", "COMPLETED") == "COMPLETED",
                error=trace.get("error_message"),
            )
            bounds_list.append(bounds)
            node_labels.append(node_name)

        return bounds_list, node_labels

    def _is_mouse_over_bounds(
        self, mouse_plot_pos: Tuple[float, float], bounds: TraceBounds
    ) -> bool:
        """Check if mouse position is over a trace bounds."""
        x, y = mouse_plot_pos
        return bounds.min_x <= x <= bounds.max_x and bounds.min_y <= y <= bounds.max_y

    def render(
        self,
        parent_tag: str,
        traces: List[Dict[str, Any]],
        total_duration: float,
        height: int = 200,
        on_cleanup: Optional[Callable[[], None]] = None,
    ) -> Optional[str]:
        """
        Render the execution trace graph.

        Args:
            parent_tag: Tag of parent window/container
            traces: List of trace dictionaries with timing data
            total_duration: Total execution duration in seconds
            height: Height of the plot in pixels
            on_cleanup: Optional callback to run on cleanup

        Returns:
            Plot tag if successful, None otherwise
        """
        if not traces:
            dpg.add_text("No timing data available", parent=parent_tag)
            return None

        instance_id = self._generate_unique_id()

        # Create textures
        self._create_textures(instance_id)

        # Calculate bounds for all traces (waterfall layout - each node on its own row)
        self._trace_bounds, node_labels = self.calculate_trace_bounds(traces)

        if not self._trace_bounds:
            dpg.add_text("No valid trace data", parent=parent_tag)
            return None

        # Determine plot dimensions
        max_level = max(b.level for b in self._trace_bounds)
        max_time = max(b.max_x for b in self._trace_bounds)

        # Create Y-axis ticks with node names (waterfall style)
        level_ticks = tuple((name, i) for i, name in enumerate(node_labels))

        self._plot_tag = f"execution_trace_plot_{instance_id}"
        self._tooltip_tag = f"trace_tooltip_{instance_id}"

        # Collect duration labels to draw after axes are set up
        duration_labels = []

        # Create the plot
        with dpg.plot(
            label="Execution Timeline (hover for details)",
            height=height,
            width=-1,
            parent=parent_tag,
            tag=self._plot_tag,
        ):
            # Legend outside the plot area on the right
            dpg.add_plot_legend(outside=True, location=dpg.mvPlot_Location_NorthEast)

            # Y-axis for execution levels
            with dpg.plot_axis(dpg.mvYAxis, tag=f"trace_yaxis_{instance_id}") as yaxis:
                dpg.set_axis_ticks(yaxis, level_ticks)
                dpg.set_axis_limits(yaxis, -0.5, max_level + 0.5)

                # Add image series for each trace
                for bounds in self._trace_bounds:
                    texture_tag = self._get_texture_for_node_type(bounds.node_type)
                    label = (
                        f"{bounds.node_name}" if bounds.success else f"{bounds.node_name} (FAILED)"
                    )

                    dpg.add_image_series(
                        texture_tag,
                        [bounds.min_x, bounds.min_y],
                        [bounds.max_x, bounds.max_y],
                        label=label,
                    )

                    # Collect duration labels for later (only if wide enough)
                    if bounds.max_x - bounds.min_x > max_time * 0.05:
                        duration_ms = bounds.duration_seconds * 1000
                        text_x = (bounds.min_x + bounds.max_x) / 2
                        text_y = bounds.level
                        duration_text = (
                            f"{duration_ms:.0f}ms" if duration_ms >= 1 else f"{duration_ms:.2f}ms"
                        )
                        duration_labels.append((text_x, text_y, duration_text))

            # X-axis for time
            with dpg.plot_axis(
                dpg.mvXAxis,
                label="Time (seconds)",
                tag=f"trace_xaxis_{instance_id}",
            ) as xaxis:
                dpg.set_axis_limits(xaxis, -0.02 * max_time, max_time * 1.05)

            # Draw duration labels directly on plot (outside axis contexts)
            for text_x, text_y, duration_text in duration_labels:
                dpg.draw_text(
                    (text_x, text_y),
                    duration_text,
                    color=(255, 255, 255, 255),
                    size=0.15,
                )

        # Create tooltip window
        with dpg.window(
            tag=self._tooltip_tag,
            show=False,
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            autosize=True,
        ):
            dpg.add_text("", tag=f"tooltip_name_{instance_id}")
            dpg.add_text("", tag=f"tooltip_type_{instance_id}")
            dpg.add_text("", tag=f"tooltip_duration_{instance_id}")
            dpg.add_text("", tag=f"tooltip_time_{instance_id}")
            dpg.add_text("", tag=f"tooltip_status_{instance_id}")

        # Create mouse handler for tooltips
        self._handler_registry_tag = f"trace_handlers_{instance_id}"

        with dpg.handler_registry(tag=self._handler_registry_tag):
            dpg.add_mouse_move_handler(callback=lambda: self._update_tooltip(instance_id))

        return self._plot_tag

    def _update_tooltip(self, instance_id: str) -> None:
        """Update tooltip based on mouse position over traces."""
        if not dpg.does_item_exist(self._plot_tag):
            return

        # Check if mouse is over the plot
        if not dpg.is_item_hovered(self._plot_tag):
            if dpg.does_item_exist(self._tooltip_tag):
                dpg.configure_item(self._tooltip_tag, show=False)
            return

        mouse_plot_pos = dpg.get_plot_mouse_pos()

        # Check if mouse is over any trace
        tooltip_shown = False
        for bounds in self._trace_bounds:
            if self._is_mouse_over_bounds(mouse_plot_pos, bounds):
                # Update tooltip content
                dpg.set_value(f"tooltip_name_{instance_id}", f"Node: {bounds.node_name}")
                dpg.set_value(f"tooltip_type_{instance_id}", f"Type: {bounds.node_type}")
                dpg.set_value(
                    f"tooltip_duration_{instance_id}",
                    f"Duration: {bounds.duration_seconds * 1000:.2f}ms",
                )
                dpg.set_value(
                    f"tooltip_time_{instance_id}",
                    f"Time: {bounds.min_x:.3f}s - {bounds.max_x:.3f}s",
                )
                status_text = (
                    "Status: COMPLETED" if bounds.success else f"Status: FAILED - {bounds.error}"
                )
                dpg.set_value(f"tooltip_status_{instance_id}", status_text)

                # Position tooltip near mouse
                mouse_pos = dpg.get_mouse_pos(local=False)
                dpg.set_item_pos(self._tooltip_tag, [mouse_pos[0] + 15, mouse_pos[1] + 15])
                dpg.configure_item(self._tooltip_tag, show=True)
                tooltip_shown = True
                break

        if not tooltip_shown:
            dpg.configure_item(self._tooltip_tag, show=False)

    def cleanup(self) -> None:
        """Clean up all DearPyGui resources created by this renderer."""
        # Delete tooltip
        if self._tooltip_tag and dpg.does_item_exist(self._tooltip_tag):
            dpg.delete_item(self._tooltip_tag)

        # Delete handler registry
        if self._handler_registry_tag and dpg.does_item_exist(self._handler_registry_tag):
            dpg.delete_item(self._handler_registry_tag)

        # Delete texture registry (this also deletes all textures in it)
        if self._texture_registry_tag and dpg.does_item_exist(self._texture_registry_tag):
            dpg.delete_item(self._texture_registry_tag)

        # Clear internal state
        self._textures.clear()
        self._trace_bounds.clear()
        self._plot_tag = None
        self._tooltip_tag = None
        self._handler_registry_tag = None
        self._texture_registry_tag = None


def extract_traces_from_exec_data(exec_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract trace data from execution data dictionary.

    Handles both new format (with relative timing) and legacy format
    (calculating from absolute timestamps).

    Args:
        exec_data: Execution data from FileLogger

    Returns:
        List of trace dictionaries suitable for rendering
    """
    traces = []
    node_logs = exec_data.get("node_logs", [])

    if not node_logs:
        return traces

    # Get session start time for calculating relative times if needed
    # session_start_str = exec_data.get("started_at")

    for i, node_log in enumerate(node_logs):
        # Check if new format with relative timing
        if "relative_start_seconds" in node_log and node_log["relative_start_seconds"] is not None:
            trace = {
                "node_id": node_log.get("node_id", ""),
                "node_name": node_log.get("node_name", f"Node {i}"),
                "node_type": node_log.get("node_type", "Unknown"),
                "relative_start_seconds": node_log["relative_start_seconds"],
                "relative_end_seconds": node_log.get(
                    "relative_end_seconds",
                    node_log["relative_start_seconds"] + node_log.get("duration_seconds", 0.1),
                ),
                "duration_seconds": node_log.get("duration_seconds", 0.0),
                "level": node_log.get("level", i),  # Default to sequential levels
                "status": node_log.get("status", "COMPLETED"),
                "error_message": node_log.get("error_message"),
            }
        else:
            # Legacy format - assign sequential levels and estimate timing
            duration = node_log.get("duration_seconds", 0.1) or 0.1
            # For legacy data, stack nodes sequentially
            if traces:
                prev_end = traces[-1]["relative_end_seconds"]
            else:
                prev_end = 0.0

            trace = {
                "node_id": node_log.get("node_id", ""),
                "node_name": node_log.get("node_name", f"Node {i}"),
                "node_type": node_log.get("node_type", "Unknown"),
                "relative_start_seconds": prev_end,
                "relative_end_seconds": prev_end + duration,
                "duration_seconds": duration,
                "level": 0,  # All on same level for legacy data
                "status": node_log.get("status", "COMPLETED"),
                "error_message": node_log.get("error_message"),
            }

        traces.append(trace)

    return traces


def has_timing_data(exec_data: Dict[str, Any]) -> bool:
    """
    Check if execution data has valid timing information.

    Args:
        exec_data: Execution data dictionary

    Returns:
        True if timing data is available for visualization
    """
    node_logs = exec_data.get("node_logs", [])
    if not node_logs:
        return False

    # Check if any node has timing data
    for node_log in node_logs:
        if node_log.get("duration_seconds") is not None:
            return True
        if node_log.get("relative_start_seconds") is not None:
            return True

    return False
