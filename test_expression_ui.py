#!/usr/bin/env python3
"""
Test expression preservation in workflow execution and serialization.

This test verifies that expressions like {{$node["Input"].data.value}} are:
1. Preserved after node execution
2. Preserved in saved workflow files
3. Preserved when workflows are loaded back
"""

import json
import os
import tempfile

from lighthouse.container import create_headless_container
from lighthouse.domain.models.workflow import Workflow


def test_expression_preservation():
    """Test that expressions are preserved through execution and save/load cycles."""

    # Create container and factory
    container = create_headless_container()
    factory = container.node_factory

    # Create an Input node with test data
    input_node = factory.create_node("Input", name="TestInput")
    input_node.update_state({"properties": '[{"name": "url", "value": "example.com"}]'})

    # Create HTTPRequest node with expression
    http_node = factory.create_node("HTTPRequest", name="TestHTTP")
    expression_url = '{{$node["TestInput"].data.url}}'
    http_node.update_state({"url": expression_url, "method": "GET", "body": "{}", "timeout": "30"})

    # Create Calculator node with expression
    calc_node = factory.create_node("Calculator", name="TestCalc")
    expression_calc = '{{$node["TestInput"].data.url}}'
    calc_node.update_state({"expression": expression_calc})

    print("✓ Created nodes with expressions")
    print(f"  HTTP URL: {http_node.state['url']}")
    print(f"  Calc expr: {calc_node.state['expression']}")

    # Create workflow
    workflow = Workflow(id="test", name="ExpressionTest")
    workflow.add_node(input_node)
    workflow.add_node(http_node)
    workflow.add_node(calc_node)
    workflow.add_connection(input_node.id, http_node.id)
    workflow.add_connection(input_node.id, calc_node.id)

    # Execute workflow
    print("\n🚀 Executing workflow...")
    result = container.workflow_orchestrator.execute_workflow(workflow, triggered_by=input_node.id)
    print(result)

    # Check that expressions are preserved after execution
    print("\n✓ Checking state after execution...")
    http_url_after = http_node.state.get("url", "")
    calc_expr_after = calc_node.state.get("expression", "")

    assert expression_url in http_url_after, f"Expression lost! Got: {http_url_after}"
    assert expression_calc in calc_expr_after, f"Expression lost! Got: {calc_expr_after}"

    print(f"  ✓ HTTP URL preserved: {http_url_after}")
    print(f"  ✓ Calc expr preserved: {calc_expr_after}")

    # Save workflow to file
    print("\n💾 Saving workflow to file...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lh", delete=False) as f:
        temp_file = f.name
        positions = {input_node.id: (100, 100), http_node.id: (300, 100), calc_node.id: (300, 300)}
        container.workflow_file_service.save_to_file(workflow, positions, temp_file)

    # Read the saved file and check expressions are in the JSON
    with open(temp_file, "r") as f:
        saved_data = json.load(f)

    print("\n✓ Checking saved file...")
    found_http_expr = False
    found_calc_expr = False

    for node_data in saved_data.get("nodes", []):
        state = node_data.get("state", {})
        if "url" in state and expression_url in state["url"]:
            found_http_expr = True
            print(f"  ✓ HTTP expression in file: {state['url']}")
        if "expression" in state and expression_calc in state["expression"]:
            found_calc_expr = True
            print(f"  ✓ Calc expression in file: {state['expression']}")

    assert found_http_expr, "HTTP expression not found in saved file!"
    assert found_calc_expr, "Calc expression not found in saved file!"

    # Load workflow from file
    print("\n📂 Loading workflow from file...")
    loaded_workflow, loaded_positions = container.workflow_file_service.load_from_file(temp_file)

    # Check expressions are preserved after loading
    print("\n✓ Checking state after loading...")
    loaded_http = loaded_workflow.get_node(http_node.id)
    loaded_calc = loaded_workflow.get_node(calc_node.id)

    assert loaded_http is not None, "HTTP node not loaded!"
    assert loaded_calc is not None, "Calc node not loaded!"

    loaded_http_url = loaded_http.state.get("url", "")
    loaded_calc_expr = loaded_calc.state.get("expression", "")

    assert expression_url in loaded_http_url, f"Expression lost after load! Got: {loaded_http_url}"
    assert (
        expression_calc in loaded_calc_expr
    ), f"Expression lost after load! Got: {loaded_calc_expr}"

    print(f"  ✓ HTTP URL after load: {loaded_http_url}")
    print(f"  ✓ Calc expr after load: {loaded_calc_expr}")

    # Clean up
    os.unlink(temp_file)

    print("\n✅ All tests passed! Expressions are preserved throughout the workflow lifecycle.")


if __name__ == "__main__":
    test_expression_preservation()
