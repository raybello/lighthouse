"""Domain-level exceptions for Lighthouse application."""


class LighthouseError(Exception):
    """Base exception for all Lighthouse domain errors."""

    pass


class WorkflowExecutionError(LighthouseError):
    """Raised when workflow execution fails."""

    pass


class CycleDetectedError(LighthouseError):
    """Raised when a cycle is detected in the workflow graph."""

    pass


class NodeValidationError(LighthouseError):
    """Raised when node validation fails."""

    pass


class ExpressionError(LighthouseError):
    """Raised when expression evaluation fails."""

    pass


class NodeNotFoundError(LighthouseError):
    """Raised when a referenced node is not found."""

    pass


class InvalidConnectionError(LighthouseError):
    """Raised when attempting to create an invalid connection."""

    pass
