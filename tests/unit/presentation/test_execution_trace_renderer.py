"""Unit tests for execution trace renderer.

Tests the image bounds calculation, trace data extraction, and
node type color mapping without requiring DearPyGui context.
"""

import pytest

from lighthouse.presentation.dearpygui.execution_trace_renderer import (
    ExecutionTraceRenderer,
    TraceBounds,
    extract_traces_from_exec_data,
    has_timing_data,
)


class TestTraceBoundsDataclass:
    """Tests for the TraceBounds dataclass."""

    def test_trace_bounds_creation(self):
        """Test creating a TraceBounds instance with all fields."""
        bounds = TraceBounds(
            min_x=0.0,
            max_x=1.0,
            min_y=-0.4,
            max_y=0.4,
            node_name="TestNode",
            node_type="Calculator",
            node_id="test-123",
            duration_seconds=1.0,
            level=0,
            success=True,
            error=None,
        )

        assert bounds.min_x == 0.0
        assert bounds.max_x == 1.0
        assert bounds.min_y == -0.4
        assert bounds.max_y == 0.4
        assert bounds.node_name == "TestNode"
        assert bounds.node_type == "Calculator"
        assert bounds.node_id == "test-123"
        assert bounds.duration_seconds == 1.0
        assert bounds.level == 0
        assert bounds.success is True
        assert bounds.error is None

    def test_trace_bounds_with_error(self):
        """Test TraceBounds with failure state."""
        bounds = TraceBounds(
            min_x=0.5,
            max_x=1.5,
            min_y=0.6,
            max_y=1.4,
            node_name="FailedNode",
            node_type="Code",
            node_id="fail-456",
            duration_seconds=1.0,
            level=1,
            success=False,
            error="Division by zero",
        )

        assert bounds.success is False
        assert bounds.error == "Division by zero"
        assert bounds.level == 1


class TestImageBoundsCalculation:
    """Test accurate calculation of image bounds from trace data."""

    @pytest.fixture
    def renderer(self):
        """Create a renderer instance for testing."""
        return ExecutionTraceRenderer()

    def test_bounds_for_single_trace(self, renderer):
        """Single trace should have correct x/y bounds."""
        traces = [
            {
                "node_id": "node-1",
                "node_name": "InputNode",
                "node_type": "Input",
                "relative_start_seconds": 0.0,
                "relative_end_seconds": 0.5,
                "duration_seconds": 0.5,
                "level": 0,
                "status": "COMPLETED",
            }
        ]

        bounds_list, node_labels = renderer.calculate_trace_bounds(traces)

        assert len(bounds_list) == 1
        bounds = bounds_list[0]

        # X bounds should match timing
        assert bounds.min_x == 0.0
        assert bounds.max_x == 0.5

        # Y bounds should be centered on level 0 (waterfall - first node)
        assert bounds.min_y == -0.4
        assert bounds.max_y == 0.4

        # Metadata should be preserved
        assert bounds.node_name == "InputNode"
        assert bounds.node_type == "Input"
        assert bounds.duration_seconds == 0.5
        assert bounds.level == 0
        assert bounds.success is True

        # Node labels for Y-axis
        assert node_labels == ["InputNode"]

    def test_bounds_waterfall_layout(self, renderer):
        """Traces should be arranged in waterfall layout (each node on its own row)."""
        traces = [
            {
                "node_id": "node-1",
                "node_name": "InputNode",
                "node_type": "Input",
                "relative_start_seconds": 0.0,
                "relative_end_seconds": 0.3,
                "duration_seconds": 0.3,
                "level": 0,
                "status": "COMPLETED",
            },
            {
                "node_id": "node-2",
                "node_name": "CalcNode",
                "node_type": "Calculator",
                "relative_start_seconds": 0.3,
                "relative_end_seconds": 0.6,
                "duration_seconds": 0.3,
                "level": 1,
                "status": "COMPLETED",
            },
            {
                "node_id": "node-3",
                "node_name": "CodeNode",
                "node_type": "Code",
                "relative_start_seconds": 0.6,
                "relative_end_seconds": 1.0,
                "duration_seconds": 0.4,
                "level": 2,
                "status": "COMPLETED",
            },
        ]

        bounds_list, node_labels = renderer.calculate_trace_bounds(traces)

        assert len(bounds_list) == 3

        # Each node gets its own row, sorted by start time
        assert node_labels == ["InputNode", "CalcNode", "CodeNode"]

        # First node (level 0) bounds
        assert bounds_list[0].min_y == -0.4
        assert bounds_list[0].max_y == 0.4
        assert bounds_list[0].level == 0
        assert bounds_list[0].node_name == "InputNode"

        # Second node (level 1) bounds
        assert bounds_list[1].min_y == 0.6
        assert bounds_list[1].max_y == 1.4
        assert bounds_list[1].level == 1
        assert bounds_list[1].node_name == "CalcNode"

        # Third node (level 2) bounds
        assert bounds_list[2].min_y == 1.6
        assert bounds_list[2].max_y == 2.4
        assert bounds_list[2].level == 2
        assert bounds_list[2].node_name == "CodeNode"

    def test_bounds_scale_with_duration(self, renderer):
        """Trace width should scale proportionally with duration."""
        traces = [
            {
                "node_id": "short",
                "node_name": "ShortNode",
                "node_type": "Input",
                "relative_start_seconds": 0.0,
                "relative_end_seconds": 0.1,
                "duration_seconds": 0.1,
                "level": 0,
                "status": "COMPLETED",
            },
            {
                "node_id": "long",
                "node_name": "LongNode",
                "node_type": "HTTPRequest",
                "relative_start_seconds": 0.1,
                "relative_end_seconds": 1.1,
                "duration_seconds": 1.0,
                "level": 0,
                "status": "COMPLETED",
            },
        ]

        bounds_list, _ = renderer.calculate_trace_bounds(traces)

        short_width = bounds_list[0].max_x - bounds_list[0].min_x
        long_width = bounds_list[1].max_x - bounds_list[1].min_x

        # Long node should be 10x wider than short node
        assert pytest.approx(long_width / short_width, rel=0.01) == 10.0

    def test_bounds_for_parallel_traces_waterfall(self, renderer):
        """Parallel traces should be on separate rows (waterfall style)."""
        traces = [
            {
                "node_id": "parallel-1",
                "node_name": "ParallelA",
                "node_type": "Calculator",
                "relative_start_seconds": 0.5,
                "relative_end_seconds": 1.0,
                "duration_seconds": 0.5,
                "level": 1,
                "status": "COMPLETED",
            },
            {
                "node_id": "parallel-2",
                "node_name": "ParallelB",
                "node_type": "Calculator",
                "relative_start_seconds": 0.5,
                "relative_end_seconds": 0.8,
                "duration_seconds": 0.3,
                "level": 1,
                "status": "COMPLETED",
            },
        ]

        bounds_list, node_labels = renderer.calculate_trace_bounds(traces)

        # Each node gets its own row in waterfall layout
        assert node_labels == ["ParallelA", "ParallelB"]
        assert len(bounds_list) == 2

        # Different Y levels (separate rows)
        assert bounds_list[0].level == 0
        assert bounds_list[1].level == 1
        assert bounds_list[0].min_y != bounds_list[1].min_y

        # Same start time (parallel execution)
        assert bounds_list[0].min_x == bounds_list[1].min_x

        # Different end times
        assert bounds_list[0].max_x != bounds_list[1].max_x

    def test_bounds_minimum_width_for_visibility(self, renderer):
        """Very short durations should have minimum width for visibility."""
        traces = [
            {
                "node_id": "instant",
                "node_name": "InstantNode",
                "node_type": "Input",
                "relative_start_seconds": 0.0,
                "relative_end_seconds": 0.0,  # Zero duration
                "duration_seconds": 0.0,
                "level": 0,
                "status": "COMPLETED",
            },
        ]

        bounds_list, _ = renderer.calculate_trace_bounds(traces)

        # Should have minimum width for visibility
        width = bounds_list[0].max_x - bounds_list[0].min_x
        assert width >= 0.01

    def test_bounds_with_failed_node(self, renderer):
        """Failed node should have success=False in bounds."""
        traces = [
            {
                "node_id": "failed",
                "node_name": "FailedNode",
                "node_type": "Code",
                "relative_start_seconds": 0.0,
                "relative_end_seconds": 0.5,
                "duration_seconds": 0.5,
                "level": 0,
                "status": "FAILED",
                "error_message": "Runtime error",
            },
        ]

        bounds_list, _ = renderer.calculate_trace_bounds(traces)

        assert bounds_list[0].success is False
        assert bounds_list[0].error == "Runtime error"


class TestTraceDataExtraction:
    """Test extraction of trace data from node_logs."""

    def test_extracts_timing_from_node_logs_new_format(self):
        """Should extract timing data from new format with relative times."""
        exec_data = {
            "status": "COMPLETED",
            "duration_seconds": 1.5,
            "started_at": "2024-01-01T10:00:00",
            "node_logs": [
                {
                    "node_id": "node-1",
                    "node_name": "InputNode",
                    "node_type": "Input",
                    "status": "COMPLETED",
                    "duration_seconds": 0.3,
                    "relative_start_seconds": 0.0,
                    "relative_end_seconds": 0.3,
                    "level": 0,
                },
                {
                    "node_id": "node-2",
                    "node_name": "CalcNode",
                    "node_type": "Calculator",
                    "status": "COMPLETED",
                    "duration_seconds": 0.5,
                    "relative_start_seconds": 0.3,
                    "relative_end_seconds": 0.8,
                    "level": 1,
                },
            ],
        }

        traces = extract_traces_from_exec_data(exec_data)

        assert len(traces) == 2

        # First trace
        assert traces[0]["node_name"] == "InputNode"
        assert traces[0]["relative_start_seconds"] == 0.0
        assert traces[0]["relative_end_seconds"] == 0.3
        assert traces[0]["level"] == 0

        # Second trace
        assert traces[1]["node_name"] == "CalcNode"
        assert traces[1]["relative_start_seconds"] == 0.3
        assert traces[1]["relative_end_seconds"] == 0.8
        assert traces[1]["level"] == 1

    def test_extracts_timing_from_legacy_format(self):
        """Should handle legacy format without relative timing."""
        exec_data = {
            "status": "COMPLETED",
            "duration_seconds": 1.0,
            "started_at": "2024-01-01T10:00:00",
            "node_logs": [
                {
                    "node_id": "node-1",
                    "node_name": "InputNode",
                    "node_type": "Input",
                    "status": "COMPLETED",
                    "duration_seconds": 0.3,
                },
                {
                    "node_id": "node-2",
                    "node_name": "CalcNode",
                    "node_type": "Calculator",
                    "status": "COMPLETED",
                    "duration_seconds": 0.5,
                },
            ],
        }

        traces = extract_traces_from_exec_data(exec_data)

        assert len(traces) == 2

        # Legacy format stacks nodes sequentially
        assert traces[0]["relative_start_seconds"] == 0.0
        assert traces[0]["relative_end_seconds"] == 0.3

        assert traces[1]["relative_start_seconds"] == 0.3
        assert traces[1]["relative_end_seconds"] == 0.8

    def test_handles_empty_node_logs(self):
        """Should return empty list for empty node_logs."""
        exec_data = {
            "status": "COMPLETED",
            "node_logs": [],
        }

        traces = extract_traces_from_exec_data(exec_data)

        assert traces == []

    def test_handles_missing_node_logs(self):
        """Should return empty list when node_logs is missing."""
        exec_data = {
            "status": "COMPLETED",
        }

        traces = extract_traces_from_exec_data(exec_data)

        assert traces == []

    def test_extracts_error_message(self):
        """Should extract error message from failed nodes."""
        exec_data = {
            "status": "FAILED",
            "node_logs": [
                {
                    "node_id": "node-1",
                    "node_name": "FailedNode",
                    "node_type": "Code",
                    "status": "FAILED",
                    "duration_seconds": 0.1,
                    "relative_start_seconds": 0.0,
                    "relative_end_seconds": 0.1,
                    "level": 0,
                    "error_message": "Division by zero",
                },
            ],
        }

        traces = extract_traces_from_exec_data(exec_data)

        assert traces[0]["status"] == "FAILED"
        assert traces[0]["error_message"] == "Division by zero"


class TestHasTimingData:
    """Test the has_timing_data utility function."""

    def test_returns_true_with_duration(self):
        """Should return True when duration_seconds is present."""
        exec_data = {
            "node_logs": [
                {"node_id": "node-1", "duration_seconds": 0.5},
            ],
        }

        assert has_timing_data(exec_data) is True

    def test_returns_true_with_relative_timing(self):
        """Should return True when relative_start_seconds is present."""
        exec_data = {
            "node_logs": [
                {"node_id": "node-1", "relative_start_seconds": 0.0},
            ],
        }

        assert has_timing_data(exec_data) is True

    def test_returns_false_without_timing(self):
        """Should return False when no timing data is present."""
        exec_data = {
            "node_logs": [
                {"node_id": "node-1", "node_name": "Test"},
            ],
        }

        assert has_timing_data(exec_data) is False

    def test_returns_false_for_empty_node_logs(self):
        """Should return False for empty node_logs."""
        exec_data = {"node_logs": []}

        assert has_timing_data(exec_data) is False

    def test_returns_false_for_missing_node_logs(self):
        """Should return False when node_logs is missing."""
        exec_data = {}

        assert has_timing_data(exec_data) is False


class TestNodeTypeColors:
    """Test node type to color mapping."""

    def test_known_node_types_have_colors(self):
        """Each known node type should have a defined color."""
        renderer = ExecutionTraceRenderer()

        known_types = [
            "Input",
            "ManualTrigger",
            "Calculator",
            "HTTPRequest",
            "Code",
            "ExecuteCommand",
            "ChatModel",
            "Form",
        ]

        for node_type in known_types:
            assert node_type in renderer.NODE_TYPE_COLORS
            color = renderer.NODE_TYPE_COLORS[node_type]
            assert len(color) == 4  # RGBA
            # RGB should be 0-255, Alpha should be 0-1
            assert all(0 <= c <= 255 for c in color[:3])  # RGB
            assert 0 <= color[3] <= 1  # Alpha

    def test_default_color_exists(self):
        """Should have a default color for unknown types."""
        renderer = ExecutionTraceRenderer()

        assert "default" in renderer.NODE_TYPE_COLORS
        default_color = renderer.NODE_TYPE_COLORS["default"]
        assert len(default_color) == 4


class TestTextureDataCreation:
    """Test texture data creation for trace bars."""

    def test_texture_data_has_correct_size(self):
        """Texture data should have correct number of elements."""
        renderer = ExecutionTraceRenderer()
        color = (255, 128, 0, 1.0)  # RGB 0-255, Alpha 0-1

        data = renderer._create_texture_data(color)

        # TEXTURE_SIZE x TEXTURE_SIZE pixels, 4 components each (RGBA)
        expected_size = renderer.TEXTURE_SIZE * renderer.TEXTURE_SIZE * 4
        assert len(data) == expected_size

    def test_texture_data_is_solid_color(self):
        """Texture should be solid color throughout."""
        renderer = ExecutionTraceRenderer()
        color = (255, 128, 77, 1.0)  # RGB 0-255, Alpha 0-1

        data = renderer._create_texture_data(color)

        # First pixel (top-left corner)
        corner_r = data[0]
        corner_g = data[1]
        corner_b = data[2]
        corner_a = data[3]

        # Center pixel
        center_idx = (
            renderer.TEXTURE_SIZE // 2 * renderer.TEXTURE_SIZE + renderer.TEXTURE_SIZE // 2
        ) * 4
        center_r = data[center_idx]
        center_g = data[center_idx + 1]
        center_b = data[center_idx + 2]
        center_a = data[center_idx + 3]

        # All pixels should be the same solid color (normalized to 0-1)
        expected_r = color[0] / 255.0
        expected_g = color[1] / 255.0
        expected_b = color[2] / 255.0
        expected_a = color[3]

        assert corner_r == center_r == expected_r
        assert corner_g == center_g == expected_g
        assert corner_b == center_b == expected_b
        assert corner_a == center_a == expected_a


class TestBoundsAccuracy:
    """Additional tests to ensure bounds accuracy for the UI."""

    @pytest.fixture
    def renderer(self):
        return ExecutionTraceRenderer()

    def test_bounds_x_coordinates_match_timing_exactly(self, renderer):
        """X coordinates should exactly match relative timing values."""
        traces = [
            {
                "node_id": "precise-1",
                "node_name": "PreciseNode",
                "node_type": "Input",
                "relative_start_seconds": 0.123456,
                "relative_end_seconds": 0.789012,
                "duration_seconds": 0.665556,
                "level": 0,
                "status": "COMPLETED",
            },
        ]

        bounds_list, _ = renderer.calculate_trace_bounds(traces)

        assert bounds_list[0].min_x == 0.123456
        assert bounds_list[0].max_x == 0.789012

    def test_bounds_y_height_is_consistent(self, renderer):
        """All traces should have the same Y height (0.8 units)."""
        traces = [
            {
                "node_id": f"node-{i}",
                "node_name": f"Node{i}",
                "node_type": f"Type{i}",
                "relative_start_seconds": float(i),
                "relative_end_seconds": float(i) + 0.5,
                "duration_seconds": 0.5,
                "level": i,
                "status": "COMPLETED",
            }
            for i in range(5)
        ]

        bounds_list, _ = renderer.calculate_trace_bounds(traces)

        for bounds in bounds_list:
            height = bounds.max_y - bounds.min_y
            assert pytest.approx(height, abs=0.001) == 0.8

    def test_bounds_rows_do_not_overlap(self, renderer):
        """Bounds for different nodes should not overlap in Y (waterfall)."""
        traces = [
            {
                "node_id": "node-1",
                "node_name": "InputNode",
                "node_type": "Input",
                "relative_start_seconds": 0.0,
                "relative_end_seconds": 0.5,
                "duration_seconds": 0.5,
                "level": 0,
                "status": "COMPLETED",
            },
            {
                "node_id": "node-2",
                "node_name": "CalcNode",
                "node_type": "Calculator",
                "relative_start_seconds": 0.5,
                "relative_end_seconds": 1.0,
                "duration_seconds": 0.5,
                "level": 1,
                "status": "COMPLETED",
            },
        ]

        bounds_list, node_labels = renderer.calculate_trace_bounds(traces)

        # Each node gets its own row
        assert node_labels == ["InputNode", "CalcNode"]

        input_max_y = bounds_list[0].max_y
        calc_min_y = bounds_list[1].min_y

        # CalcNode row should start above where InputNode row ends
        assert calc_min_y > input_max_y

    def test_bounds_width_equals_duration(self, renderer):
        """Bounds width should equal the relative time span."""
        traces = [
            {
                "node_id": "test",
                "node_name": "TestNode",
                "node_type": "Code",
                "relative_start_seconds": 0.25,
                "relative_end_seconds": 0.75,
                "duration_seconds": 0.5,
                "level": 0,
                "status": "COMPLETED",
            },
        ]

        bounds_list, _ = renderer.calculate_trace_bounds(traces)

        width = bounds_list[0].max_x - bounds_list[0].min_x
        assert pytest.approx(width, abs=0.001) == 0.5
