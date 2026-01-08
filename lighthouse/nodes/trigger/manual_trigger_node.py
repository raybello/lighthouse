"""
Manual Trigger node for initiating workflows.

Pure business logic with NO UI dependencies.
"""

from typing import Dict, Any

from lighthouse.nodes.base.base_node import TriggerNode
from lighthouse.domain.models.node import NodeMetadata, NodeType, ExecutionResult
from lighthouse.domain.models.field_types import FieldDefinition, FieldType


class ManualTriggerNode(TriggerNode):
    """
    Manual trigger node for initiating workflows.

    This node has no inputs and serves as a starting point for workflows.
    It can be executed manually to trigger downstream nodes.

    State Fields:
        None - this is a simple trigger with no configuration
    """

    @property
    def metadata(self) -> NodeMetadata:
        """Get manual trigger node metadata."""
        return NodeMetadata(
            node_type=NodeType.TRIGGER,
            name="ManualTrigger",
            description="Manually triggered workflow starting point",
            version="1.0.0",
            fields=[],  # No configuration fields
            has_inputs=False,  # Triggers have no inputs
            has_config=False,  # No configuration needed
            category="Triggers",
        )

    def execute(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the manual trigger.

        Since this is a trigger node, it simply returns success
        with empty data. Its purpose is to initiate workflow execution.

        Args:
            context: Execution context (not used)

        Returns:
            ExecutionResult with empty data
        """
        import time
        start_time = time.time()

        # Manual trigger just returns success with empty data
        # Its role is to start the workflow
        duration = time.time() - start_time

        return ExecutionResult.success_result(
            data={},
            duration=duration,
        )

    def validate(self) -> list[str]:
        """
        Validate manual trigger configuration.

        Manual trigger has no configuration, so always valid.

        Returns:
            Empty list (always valid)
        """
        return []
