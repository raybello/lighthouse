"""
Dependency Injection Container for Lighthouse.

Provides centralized service instantiation and dependency management.
"""

from dataclasses import dataclass
from typing import Optional

from lighthouse.application.services.execution_manager import ExecutionManager
from lighthouse.application.services.node_factory import NodeFactory
from lighthouse.application.services.workflow_file_service import WorkflowFileService
from lighthouse.application.services.workflow_orchestrator import WorkflowOrchestrator
from lighthouse.domain.protocols.logger_protocol import ILogger
from lighthouse.domain.services.context_builder import ContextBuilder
from lighthouse.domain.services.expression_service import ExpressionService
from lighthouse.domain.services.topology_service import TopologyService
from lighthouse.domain.services.workflow_serializer import WorkflowSerializer
from lighthouse.infrastructure.logging.file_logger import FileLogger
from lighthouse.nodes.registry import NodeRegistry, get_registry


@dataclass
class ServiceContainer:
    """
    Service container holding all application services.

    All services are explicitly wired with their dependencies.
    Supports both UI and headless modes.
    """

    # Domain services (pure business logic)
    expression_service: ExpressionService
    topology_service: TopologyService
    context_builder: ContextBuilder
    workflow_serializer: WorkflowSerializer

    # Application services
    node_registry: NodeRegistry
    node_factory: NodeFactory
    execution_manager: ExecutionManager
    workflow_orchestrator: WorkflowOrchestrator
    workflow_file_service: WorkflowFileService

    # Infrastructure services
    logger: Optional[ILogger] = None


def create_container(
    ui_mode: bool = False,
    registry: Optional[NodeRegistry] = None,
    enable_logging: bool = True,
    logs_dir: str = ".logs",
) -> ServiceContainer:
    """
    Create and wire the service container.

    Args:
        ui_mode: Whether to initialize UI components
        registry: Optional custom node registry (uses global if None)
        enable_logging: Whether to enable file logging (default: True)
        logs_dir: Directory for log files (default: .logs)

    Returns:
        Fully wired ServiceContainer
    """
    # Domain services (stateless, no dependencies)
    expression_service = ExpressionService()
    topology_service = TopologyService()
    context_builder = ContextBuilder()
    workflow_serializer = WorkflowSerializer()

    # Infrastructure services
    logger: Optional[ILogger] = None
    if enable_logging:
        logger = FileLogger(logs_dir=logs_dir)

    # Node registry and factory
    node_registry = registry or get_registry()
    node_factory = NodeFactory(registry=node_registry)

    # Execution services
    execution_manager = ExecutionManager(logger=logger)
    workflow_orchestrator = WorkflowOrchestrator(
        topology_service=topology_service,
        expression_service=expression_service,
        execution_manager=execution_manager,
    )

    # Workflow file service
    workflow_file_service = WorkflowFileService(
        serializer=workflow_serializer,
        node_factory=node_factory,
    )

    # Create container
    return ServiceContainer(
        expression_service=expression_service,
        topology_service=topology_service,
        context_builder=context_builder,
        workflow_serializer=workflow_serializer,
        node_registry=node_registry,
        node_factory=node_factory,
        execution_manager=execution_manager,
        workflow_orchestrator=workflow_orchestrator,
        workflow_file_service=workflow_file_service,
        logger=logger,
    )


def create_headless_container() -> ServiceContainer:
    """
    Create a container for headless (non-UI) execution.

    Returns:
        ServiceContainer configured for headless mode
    """
    return create_container(ui_mode=False)


def create_ui_container() -> ServiceContainer:
    """
    Create a container for UI mode.

    Returns:
        ServiceContainer configured for UI mode
    """
    return create_container(ui_mode=True)
