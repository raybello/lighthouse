#!/usr/bin/env python3
"""Test if expression preservation works correctly."""

from lighthouse.container import create_headless_container
from lighthouse.domain.models.workflow import Workflow

# Create container and factory
container = create_headless_container()
factory = container.node_factory

# Create an Input node with test data
input_node = factory.create_node("Input", name="TestInput")
input_node.update_state({"properties": '[{"name": "url", "value": "example.com"}]'})

# Create HTTPRequest node with expression
http_node = factory.create_node("HTTPRequest", name="TestHTTP")
http_node.update_state(
    {"url": '{{$node["TestInput"].data.url}}', "method": "GET", "body": "{}", "timeout": "30"}
)

print("Before execution:")
print("HTTP Node state:", http_node.state)

# Create workflow
workflow = Workflow(id="test", name="Test")
workflow.add_node(input_node)
workflow.add_node(http_node)
workflow.add_connection(input_node.id, http_node.id)

# Execute using orchestrator (which doesn't use the UI app's execution code)
result = container.workflow_orchestrator.execute_workflow(workflow, triggered_by=input_node.id)

print("\nAfter execution (orchestrator):")
print("HTTP Node state:", http_node.state)
print("Expression preserved?", "{{" in str(http_node.state.get("url", "")))
