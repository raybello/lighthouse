"""
Execution profiler for analyzing parallel workflow execution.

Provides statistics, traces, and visualization data for execution analysis.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from lighthouse.application.services.execution_manager import ExecutionManager


@dataclass
class ExecutionTrace:
    """Trace data for a single node execution."""

    node_id: str
    node_name: str
    node_type: str
    start_time: float
    end_time: float
    duration: float
    level: int
    thread_id: str
    success: bool = True
    error: Optional[str] = None


@dataclass
class LevelStatistics:
    """Statistics for a single execution level."""

    level: int
    node_count: int
    total_duration: float
    parallel_efficiency: float  # actual time vs sequential time
    nodes: List[str] = field(default_factory=list)


@dataclass
class ExecutionStatistics:
    """Comprehensive execution statistics."""

    session_id: str
    workflow_name: str
    status: str
    total_duration: float
    total_nodes: int
    completed_nodes: int
    failed_nodes: int
    level_count: int
    execution_mode: str
    parallel_speedup: float  # sequential time / actual time
    level_stats: List[LevelStatistics] = field(default_factory=list)
    traces: List[ExecutionTrace] = field(default_factory=list)


class ExecutionProfiler:
    """
    Profiler for analyzing workflow execution performance.

    Provides:
    - Execution traces with timing data
    - Level-based statistics
    - Parallel efficiency metrics
    - Export functionality for visualization
    """

    def __init__(self, execution_manager: ExecutionManager):
        """
        Initialize the profiler.

        Args:
            execution_manager: ExecutionManager to get profiling data from
        """
        self.execution_manager = execution_manager

    def get_statistics(self) -> ExecutionStatistics:
        """
        Get comprehensive execution statistics.

        Returns:
            ExecutionStatistics with all profiling data
        """
        profiling_data = self.execution_manager.get_profiling_data()

        if "error" in profiling_data:
            return ExecutionStatistics(
                session_id="",
                workflow_name="",
                status="NO_DATA",
                total_duration=0.0,
                total_nodes=0,
                completed_nodes=0,
                failed_nodes=0,
                level_count=0,
                execution_mode="unknown",
                parallel_speedup=1.0,
            )

        # Build traces
        traces = []
        for trace_data in profiling_data.get("traces", []):
            traces.append(
                ExecutionTrace(
                    node_id=trace_data["node_id"],
                    node_name=trace_data["node_name"],
                    node_type=trace_data["node_type"],
                    start_time=trace_data["start_time"],
                    end_time=trace_data["end_time"],
                    duration=trace_data["duration"],
                    level=trace_data["level"],
                    thread_id=trace_data["thread_id"] or "unknown",
                    success=trace_data["success"],
                    error=trace_data["error"],
                )
            )

        # Build level statistics
        level_stats = self._calculate_level_stats(traces)

        # Calculate parallel speedup
        sequential_time = sum(t.duration for t in traces)
        actual_time = profiling_data.get("total_duration", sequential_time)
        parallel_speedup = sequential_time / actual_time if actual_time > 0 else 1.0

        return ExecutionStatistics(
            session_id=profiling_data.get("session_id", ""),
            workflow_name=profiling_data.get("workflow_name", ""),
            status=profiling_data.get("status", ""),
            total_duration=actual_time,
            total_nodes=profiling_data.get("total_nodes", 0),
            completed_nodes=profiling_data.get("completed_nodes", 0),
            failed_nodes=profiling_data.get("failed_nodes", 0),
            level_count=profiling_data.get("levels", 0),
            execution_mode="parallel" if parallel_speedup > 1.1 else "sequential",
            parallel_speedup=parallel_speedup,
            level_stats=level_stats,
            traces=traces,
        )

    def _calculate_level_stats(self, traces: List[ExecutionTrace]) -> List[LevelStatistics]:
        """Calculate statistics for each execution level."""
        level_data: Dict[int, List[ExecutionTrace]] = {}

        for trace in traces:
            if trace.level not in level_data:
                level_data[trace.level] = []
            level_data[trace.level].append(trace)

        level_stats = []
        for level in sorted(level_data.keys()):
            level_traces = level_data[level]
            sequential_time = sum(t.duration for t in level_traces)
            # Actual time is max end - min start for the level
            if level_traces:
                min_start = min(t.start_time for t in level_traces)
                max_end = max(t.end_time for t in level_traces)
                actual_time = max_end - min_start
            else:
                actual_time = 0.0

            efficiency = sequential_time / actual_time if actual_time > 0 else 1.0

            level_stats.append(
                LevelStatistics(
                    level=level,
                    node_count=len(level_traces),
                    total_duration=actual_time,
                    parallel_efficiency=efficiency,
                    nodes=[t.node_name for t in level_traces],
                )
            )

        return level_stats

    def export_gantt_data(self) -> Dict[str, Any]:
        """
        Export data in a format suitable for Gantt chart visualization.

        Returns:
            Dictionary with nodes, timing data, and metadata
        """
        stats = self.get_statistics()

        gantt_data = {
            "metadata": {
                "session_id": stats.session_id,
                "workflow_name": stats.workflow_name,
                "total_duration": stats.total_duration,
                "parallel_speedup": stats.parallel_speedup,
                "level_count": stats.level_count,
            },
            "nodes": [],
            "levels": [],
        }

        for trace in stats.traces:
            gantt_data["nodes"].append(
                {
                    "id": trace.node_id,
                    "name": trace.node_name,
                    "type": trace.node_type,
                    "start": trace.start_time,
                    "end": trace.end_time,
                    "duration": trace.duration,
                    "level": trace.level,
                    "thread": trace.thread_id,
                    "success": trace.success,
                }
            )

        for level_stat in stats.level_stats:
            gantt_data["levels"].append(
                {
                    "level": level_stat.level,
                    "node_count": level_stat.node_count,
                    "duration": level_stat.total_duration,
                    "efficiency": level_stat.parallel_efficiency,
                    "nodes": level_stat.nodes,
                }
            )

        return gantt_data

    def export_json(self, filepath: str) -> None:
        """
        Export profiling data to JSON file.

        Args:
            filepath: Path to write JSON file
        """
        gantt_data = self.export_gantt_data()
        with open(filepath, "w") as f:
            json.dump(gantt_data, f, indent=2)

    def print_summary(self) -> str:
        """
        Generate a human-readable summary of execution statistics.

        Returns:
            Formatted summary string
        """
        stats = self.get_statistics()

        lines = [
            "=" * 60,
            "EXECUTION STATISTICS",
            "=" * 60,
            f"Session ID: {stats.session_id}",
            f"Workflow: {stats.workflow_name}",
            f"Status: {stats.status}",
            f"Total Duration: {stats.total_duration:.3f}s",
            f"Execution Mode: {stats.execution_mode}",
            f"Parallel Speedup: {stats.parallel_speedup:.2f}x",
            "",
            f"Nodes: {stats.completed_nodes}/{stats.total_nodes} completed"
            + (f", {stats.failed_nodes} failed" if stats.failed_nodes else ""),
            f"Levels: {stats.level_count}",
            "",
            "Level Statistics:",
        ]

        for level_stat in stats.level_stats:
            lines.append(
                f"  Level {level_stat.level}: {level_stat.node_count} nodes, "
                f"{level_stat.total_duration:.3f}s, "
                f"{level_stat.parallel_efficiency:.2f}x efficiency"
            )
            lines.append(f"    Nodes: {', '.join(level_stat.nodes)}")

        lines.append("")
        lines.append("Node Execution Traces:")
        for trace in sorted(stats.traces, key=lambda t: t.start_time):
            status = "OK" if trace.success else f"FAILED: {trace.error}"
            lines.append(
                f"  [{trace.thread_id}] {trace.node_name} ({trace.node_type}): "
                f"{trace.duration * 1000:.1f}ms - {status}"
            )

        lines.append("=" * 60)
        return "\n".join(lines)
