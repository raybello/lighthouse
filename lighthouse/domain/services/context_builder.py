"""
Pure domain service for building execution context.

Manages the construction of context dictionaries that are used
for expression resolution during workflow execution.
"""

from typing import Any, Dict, List

from lighthouse.domain.models.execution import ExecutionSession


class ContextBuilder:
    """
    Pure domain service for building execution context.

    Constructs context dictionaries from node execution outputs,
    enabling downstream nodes to reference upstream results via expressions.

    This is a stateless service - all state is passed as parameters.
    """

    def __init__(self):
        """Initialize the context builder (stateless)."""
        pass

    def build_context(
        self, session: ExecutionSession, completed_nodes: List[str]
    ) -> Dict[str, Any]:
        """
        Build execution context from completed node outputs.

        Creates a context dictionary mapping node names to their outputs,
        which can be used for expression resolution.

        Args:
            session: Current execution session containing node records
            completed_nodes: List of node IDs that have completed

        Returns:
            Context dictionary: {node_name: node_output}
        """
        context = {}

        for node_id in completed_nodes:
            record = session.get_node_record(node_id)
            if record and record.outputs:
                # Use node name as key for expression references
                context[record.node_name] = record.outputs

        return context

    def build_context_from_outputs(self, node_outputs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build context from a simple dictionary of node outputs.

        Useful for testing or simple scenarios where we don't have
        a full ExecutionSession.

        Args:
            node_outputs: Dictionary mapping node names to their outputs

        Returns:
            Context dictionary (same format as input)
        """
        return node_outputs.copy()

    def update_context(
        self,
        context: Dict[str, Any],
        node_name: str,
        output: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update context with a new node's output.

        Creates a new context dictionary with the added output.
        Does not mutate the input context.

        Args:
            context: Existing context dictionary
            node_name: Name of the node to add
            output: Node's output data

        Returns:
            New context dictionary with the update
        """
        new_context = context.copy()
        new_context[node_name] = output
        return new_context

    def merge_contexts(self, *contexts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple context dictionaries.

        Later contexts override earlier ones in case of conflicts.

        Args:
            *contexts: Variable number of context dictionaries to merge

        Returns:
            Merged context dictionary
        """
        merged = {}
        for ctx in contexts:
            merged.update(ctx)
        return merged

    def filter_context(
        self,
        context: Dict[str, Any],
        node_names: List[str],
    ) -> Dict[str, Any]:
        """
        Filter context to include only specific nodes.

        Useful for creating minimal contexts for testing or
        for security/isolation purposes.

        Args:
            context: Full context dictionary
            node_names: List of node names to include

        Returns:
            Filtered context dictionary
        """
        return {name: output for name, output in context.items() if name in node_names}

    def validate_context(self, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate a context dictionary structure.

        Checks that the context is properly formatted and contains
        valid data structures.

        Args:
            context: Context dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not isinstance(context, dict):
            errors.append("Context must be a dictionary")
            return False, errors

        for node_name, output in context.items():
            if not isinstance(node_name, str):
                errors.append(f"Node name must be string, got {type(node_name)}")

            if not isinstance(output, dict):
                errors.append(f"Output for '{node_name}' must be dict, got {type(output)}")

        is_valid = len(errors) == 0
        return is_valid, errors
