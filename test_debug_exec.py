#!/usr/bin/env python3
import json

from lighthouse.container import create_headless_container
from lighthouse.domain.models.workflow import Workflow

container = create_headless_container()
factory = container.node_factory
orchestrator = container.workflow_orchestrator

workflow = Workflow(id="test", name="Test")

# Create nodes
input_node = factory.create_node("Input", name="Source")
calc1_node = factory.create_node("Calculator", name="Calc1")
calc2_node = factory.create_node("Calculator", name="Calc2")

# Configure nodes
input_node.update_state({"properties": json.dumps([{"name": "x", "value": "5", "type": "number"}])})

calc1_expression = '{{$node["Source"].data.x}}'
calc1_node.update_state({"field_a": calc1_expression, "field_b": "3", "operation": "*"})

calc2_expression = '{{$node["Calc1"].data.result}}'
calc2_node.update_state({"field_a": calc2_expression, "field_b": "2", "operation": "+"})

# Build workflow - use to_domain_node()
workflow.add_node(input_node.to_domain_node())
workflow.add_node(calc1_node.to_domain_node())
workflow.add_node(calc2_node.to_domain_node())

workflow.add_connection(input_node.id, calc1_node.id)
workflow.add_connection(calc1_node.id, calc2_node.id)

# Execute
result = orchestrator.execute_workflow(workflow, triggered_by=input_node.id)

print("Status:", result["status"])
if "error" in result:
    print("Error:", result["error"])

    if "traceback" in result:
        print("Traceback:", result["traceback"])
