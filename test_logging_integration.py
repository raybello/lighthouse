"""
Test script to verify the new logging system works correctly.

Creates a simple workflow and verifies that:
1. Log directories are created in .logs/
2. Each node gets its own log file
3. execution_metadata.json is created
4. execution_summary.log is created
"""

from lighthouse.container import create_headless_container
from lighthouse.domain.models.workflow import Workflow
from lighthouse.domain.models.node import Node
from pathlib import Path
import json


def test_logging_system():
    """Test the logging system with a simple workflow."""

    print("🧪 Testing Lighthouse Logging System\n")

    # Create container with logging enabled
    print("1. Creating service container with logging enabled...")
    container = create_headless_container()

    # Verify logger was created
    assert container.logger is not None, "Logger should be created"
    print("   ✓ Logger created successfully\n")

    # Create a simple workflow
    print("2. Creating workflow with 3 nodes...")
    workflow = Workflow(id="test_workflow", name="Test Workflow")

    # Create nodes using the factory
    input_node = container.node_factory.create_node("Input", name="TestInput")
    input_node.update_state({"age": 25, "name": "Alice"})

    calc_node = container.node_factory.create_node("Calculator", name="AgeCalc")
    calc_node.update_state({"expression": '{{$node["TestInput"].data.age}} * 2'})

    http_node = container.node_factory.create_node("HTTPRequest", name="HTTPTest")
    http_node.update_state({"method": "GET", "url": "https://api.github.com/zen"})

    # Add nodes to workflow
    workflow.add_node(input_node)
    workflow.add_node(calc_node)
    workflow.add_node(http_node)

    # Connect nodes
    workflow.add_connection(input_node.id, calc_node.id)
    workflow.add_connection(calc_node.id, http_node.id)

    print("   ✓ Workflow created with 3 nodes\n")

    # Execute workflow
    print("3. Executing workflow...")
    result = container.workflow_orchestrator.execute_workflow(
        workflow=workflow, triggered_by=input_node.id
    )

    print(f"   ✓ Workflow execution {result['status']}\n")

    # Get session ID
    session_id = result["session_id"]
    print(f"4. Verifying log files for session: {session_id}")

    # Check log directory structure
    logs_dir = Path(".logs")
    session_dir = logs_dir / session_id

    assert session_dir.exists(), f"Session directory should exist: {session_dir}"
    print(f"   ✓ Session directory exists: {session_dir}")

    # Check execution_metadata.json
    metadata_file = session_dir / "execution_metadata.json"
    assert metadata_file.exists(), "execution_metadata.json should exist"

    with open(metadata_file) as f:
        metadata = json.load(f)

    print(f"   ✓ execution_metadata.json exists")
    print(f"     - Status: {metadata['status']}")
    print(f"     - Nodes executed: {metadata['nodes_executed']}")
    print(f"     - Duration: {metadata['duration_seconds']:.2f}s")

    # Check execution_summary.log
    summary_log = session_dir / "execution_summary.log"
    assert summary_log.exists(), "execution_summary.log should exist"
    print(f"   ✓ execution_summary.log exists")

    # Check node-specific log files
    print(f"\n5. Checking individual node log files...")
    node_logs = list(session_dir.glob("*.log"))

    # Filter out summary log
    node_logs = [
        log for log in node_logs if log.name != "execution_summary.log" and log.name != "errors.log"
    ]

    assert len(node_logs) >= 3, f"Should have at least 3 node log files, found {len(node_logs)}"

    for log_file in node_logs:
        print(f"   ✓ {log_file.name}")

        # Read and display first few lines
        with open(log_file) as f:
            lines = f.readlines()[:3]
            for line in lines:
                print(f"      {line.strip()}")

    # Check node execution records in metadata
    print(f"\n6. Checking node execution records...")
    for node_log in metadata["node_logs"]:
        print(f"   ✓ {node_log['node_name']} ({node_log['node_type']})")
        print(f"     - Status: {node_log['status']}")
        print(f"     - Duration: {node_log['duration_seconds']:.2f}s")
        print(f"     - Log file: {node_log['log_file']}")

        # Check if outputs are captured
        if node_log.get("outputs"):
            print(f"     - Outputs captured: Yes")
            # Show a preview of the outputs
            outputs_str = str(node_log["outputs"])
            if len(outputs_str) > 100:
                outputs_str = outputs_str[:100] + "..."
            print(f"     - Output preview: {outputs_str}")
        else:
            print(f"     - Outputs captured: No")

    print(f"\n✅ All logging tests passed!")
    print(f"📁 View logs at: {session_dir}")

    return session_dir


if __name__ == "__main__":
    try:
        log_dir = test_logging_system()
        print(f"\n🎉 Success! Logging system is working correctly.")
        print(f"   Check the logs in: {log_dir}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
