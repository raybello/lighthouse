"""
Pure domain service for graph topology operations.

Provides topological sorting and cycle detection using Kahn's algorithm.
All methods are pure functions with no side effects.
"""

from typing import List

from lighthouse.domain.exceptions import CycleDetectedError
from lighthouse.domain.models.workflow import Workflow


class TopologyService:
    """
    Pure domain service for workflow graph topology operations.

    Provides algorithms for:
    - Topological sorting (execution order determination)
    - Cycle detection
    - Dependency analysis

    All methods are stateless and side-effect free.
    """

    def __init__(self):
        """Initialize the topology service (stateless)."""
        pass

    def topological_sort(self, workflow: Workflow) -> List[str]:
        """
        Perform topological sort on workflow graph using Kahn's algorithm.

        Returns a linear ordering of nodes such that for every directed edge
        from node A to node B, A comes before B in the ordering.

        Args:
            workflow: Workflow to sort

        Returns:
            List of node IDs in execution order

        Raises:
            CycleDetectedError: If graph contains cycles
        """
        if not workflow.nodes:
            return []

        # Get adjacency list (incoming connections)
        adj_list = workflow.get_topology()

        # Calculate in-degrees
        in_degree = {node_id: len(sources) for node_id, sources in adj_list.items()}

        # Build outgoing edges (reverse of adj_list)
        outgoing = {node_id: [] for node_id in workflow.nodes.keys()}
        for target, sources in adj_list.items():
            for source in sources:
                outgoing[source].append(target)

        # Kahn's algorithm: Start with nodes that have no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

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
        if len(result) != len(workflow.nodes):
            unprocessed = [node_id for node_id, degree in in_degree.items() if degree > 0]
            raise CycleDetectedError(
                f"Cycle detected in workflow. Unprocessed nodes: {unprocessed}"
            )

        return result

    def detect_cycle(self, workflow: Workflow) -> bool:
        """
        Check if workflow contains cycles.

        Args:
            workflow: Workflow to check

        Returns:
            True if cycle exists, False otherwise
        """
        try:
            self.topological_sort(workflow)
            return False
        except CycleDetectedError:
            return True

    def find_dependencies(self, workflow: Workflow, node_id: str) -> List[str]:
        """
        Find all upstream dependencies of a node.

        Performs a depth-first search to find all nodes that must
        execute before the target node.

        Args:
            workflow: Workflow graph
            node_id: Target node ID

        Returns:
            List of node IDs that must execute before target (in topological order)
        """
        if node_id not in workflow.nodes:
            return []

        adj_list = workflow.get_topology()
        visited = set()
        result = []

        def dfs(current_id: str):
            if current_id in visited:
                return
            visited.add(current_id)

            # Visit all dependencies first
            for dependency in adj_list.get(current_id, []):
                dfs(dependency)
                if dependency not in result:
                    result.append(dependency)

        dfs(node_id)
        return result

    def find_dependents(self, workflow: Workflow, node_id: str) -> List[str]:
        """
        Find all downstream dependents of a node.

        Finds all nodes that depend on the given node (directly or indirectly).

        Args:
            workflow: Workflow graph
            node_id: Source node ID

        Returns:
            List of node IDs that depend on source node
        """
        if node_id not in workflow.nodes:
            return []

        # Build reverse adjacency list (node -> dependents)
        dependents_map = {nid: [] for nid in workflow.nodes.keys()}
        for target, sources in workflow.get_topology().items():
            for source in sources:
                dependents_map[source].append(target)

        visited = set()
        result = []

        def dfs(current_id: str):
            if current_id in visited:
                return
            visited.add(current_id)

            for dependent in dependents_map.get(current_id, []):
                if dependent not in result:
                    result.append(dependent)
                dfs(dependent)

        dfs(node_id)
        return result

    def is_reachable(self, workflow: Workflow, from_node: str, to_node: str) -> bool:
        """
        Check if there's a path from one node to another.

        Args:
            workflow: Workflow graph
            from_node: Source node ID
            to_node: Target node ID

        Returns:
            True if target is reachable from source
        """
        if from_node not in workflow.nodes or to_node not in workflow.nodes:
            return False

        if from_node == to_node:
            return True

        # Use BFS to check reachability
        adj_list = workflow.get_topology()

        # Build forward adjacency list
        outgoing = {node_id: [] for node_id in workflow.nodes.keys()}
        for target, sources in adj_list.items():
            for source in sources:
                outgoing[source].append(target)

        visited = set()
        queue = [from_node]

        while queue:
            current = queue.pop(0)
            if current == to_node:
                return True

            if current in visited:
                continue
            visited.add(current)

            for neighbor in outgoing.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)

        return False

    def get_execution_levels(self, workflow: Workflow) -> List[List[str]]:
        """
        Get nodes grouped by execution level.

        Nodes in the same level can potentially be executed in parallel
        (they have no dependencies on each other).

        Args:
            workflow: Workflow to analyze

        Returns:
            List of levels, where each level is a list of node IDs that can execute concurrently

        Raises:
            CycleDetectedError: If workflow contains cycles
        """
        if not workflow.nodes:
            return []

        # Get adjacency list
        adj_list = workflow.get_topology()

        # Calculate in-degrees
        in_degree = {node_id: len(sources) for node_id, sources in adj_list.items()}

        # Build outgoing edges
        outgoing = {node_id: [] for node_id in workflow.nodes.keys()}
        for target, sources in adj_list.items():
            for source in sources:
                outgoing[source].append(target)

        # Level-based topological sort
        levels = []
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        processed = 0

        while queue:
            current_level = list(queue)
            levels.append(current_level)
            queue.clear()
            processed += len(current_level)

            for node_id in current_level:
                for neighbor in outgoing.get(node_id, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        # Check for cycles
        if processed != len(workflow.nodes):
            unprocessed = [node_id for node_id, degree in in_degree.items() if degree > 0]
            raise CycleDetectedError(
                f"Cycle detected in workflow. Unprocessed nodes: {unprocessed}"
            )

        return levels

    def validate_connection(
        self, workflow: Workflow, from_node: str, to_node: str
    ) -> tuple[bool, str]:
        """
        Validate if adding a connection would create a cycle.

        Args:
            workflow: Workflow graph
            from_node: Source node ID
            to_node: Target node ID

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if nodes exist
        if from_node not in workflow.nodes:
            return False, f"Source node '{from_node}' not found"
        if to_node not in workflow.nodes:
            return False, f"Target node '{to_node}' not found"

        # Self-loop check
        if from_node == to_node:
            return False, "Cannot create self-loop connection"

        # Would adding this connection create a cycle?
        # It creates a cycle if there's already a path from to_node to from_node
        if self.is_reachable(workflow, to_node, from_node):
            return (
                False,
                f"Connection would create a cycle: {to_node} already has a path to {from_node}",
            )

        return True, ""
