"""Domain-level exceptions for Lighthouse application."""


class LighthouseException(Exception):
    """Base exception for all Lighthouse domain errors."""

    pass


class WorkflowExecutionError(LighthouseException):
    """Raised when workflow execution fails."""

    pass


class CycleDetectedError(LighthouseException):
    """Raised when a cycle is detected in the workflow graph."""

    pass


class NodeValidationError(LighthouseException):
    """Raised when node validation fails."""

    pass


class ExpressionError(LighthouseException):
    """Raised when expression evaluation fails."""

    pass


class NodeNotFoundError(LighthouseException):
    """Raised when a referenced node is not found."""

    pass


class InvalidConnectionError(LighthouseException):
    """Raised when attempting to create an invalid connection."""

    pass
