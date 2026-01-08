"""Protocol for UI rendering abstractions."""

from typing import Protocol, Callable, Dict, Any
from lighthouse.domain.models.node import Node


class INodeRenderer(Protocol):
    """
    Protocol for rendering nodes in a UI.

    This abstraction allows swapping UI frameworks
    (DearPyGui → Qt → Web) without changing domain logic.

    The renderer is responsible for ALL UI concerns:
    - Creating visual representation of nodes
    - Handling user interactions (clicks, edits)
    - Updating visual state (status colors, etc.)
    - Managing inspector windows
    """

    def render_node(
        self,
        node: Node,
        on_execute: Callable[[str], None],
        on_delete: Callable[[str], None],
        on_edit: Callable[[str], None],
        on_rename: Callable[[str], None],
    ) -> None:
        """
        Render a node in the UI.

        Creates the visual representation of the node with
        input/output pins, buttons, and status display.

        Args:
            node: Node domain model to render
            on_execute: Callback when execute button clicked
            on_delete: Callback when delete button clicked
            on_edit: Callback when edit button clicked
            on_rename: Callback when rename button clicked
        """
        ...

    def update_node_status(
        self,
        node_id: str,
        status: str,
        color: tuple[int, int, int]
    ) -> None:
        """
        Update node visual status.

        Changes the displayed status text and color
        to reflect execution state.

        Args:
            node_id: Node identifier
            status: Status text (PENDING, RUNNING, COMPLETED, ERROR)
            color: RGB color tuple (e.g., (0, 255, 0) for green)
        """
        ...

    def render_connection(
        self,
        from_node: str,
        to_node: str,
        connection_id: str
    ) -> None:
        """
        Render a connection between nodes.

        Args:
            from_node: Source node ID
            to_node: Target node ID
            connection_id: Unique connection identifier
        """
        ...

    def show_inspector(
        self,
        node: Node,
        on_save: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Show inspector window for node configuration.

        Displays a modal or panel with fields for editing
        the node's state. Calls on_save when user confirms.

        Args:
            node: Node to inspect/configure
            on_save: Callback with updated state dict when saved
        """
        ...

    def hide_inspector(self, node_id: str) -> None:
        """
        Hide inspector window for a node.

        Args:
            node_id: Node identifier
        """
        ...

    def clear_all(self) -> None:
        """
        Clear all rendered nodes and connections.

        Used when loading a new workflow or resetting the editor.
        """
        ...


class IWorkflowRenderer(Protocol):
    """
    Protocol for rendering the overall workflow UI.

    Handles the main window, tabs, and high-level UI components.
    """

    def show_logs_tab(self) -> None:
        """Switch to the execution logs tab."""
        ...

    def show_editor_tab(self) -> None:
        """Switch to the node editor tab."""
        ...

    def update_logs(self, execution_id: str, logs: list[str]) -> None:
        """
        Update the logs display.

        Args:
            execution_id: Execution session ID
            logs: List of log messages to display
        """
        ...

    def show_error_dialog(self, title: str, message: str) -> None:
        """
        Show an error dialog.

        Args:
            title: Dialog title
            message: Error message
        """
        ...

    def show_info_dialog(self, title: str, message: str) -> None:
        """
        Show an info dialog.

        Args:
            title: Dialog title
            message: Info message
        """
        ...
