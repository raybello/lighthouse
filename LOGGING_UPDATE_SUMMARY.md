# Logging System Update Summary

## Overview
Updated the Lighthouse v2.0 architecture to include the same comprehensive file-based logging system as the legacy code in `src/`. The logging system now creates a directory per execution in `.logs/` with separate log files for each node execution.

## Changes Made

### 1. Created File-Based Logger (`lighthouse/infrastructure/logging/file_logger.py`)
- Implements the `ILogger` protocol
- Creates one directory per execution: `.logs/<session_id>/`
- Generates separate log files for each node execution
- Tracks execution metadata in `execution_metadata.json`
- Creates `execution_summary.log` for high-level events
- Creates `errors.log` for all errors during execution

### 2. Updated ILogger Protocol (`lighthouse/domain/protocols/logger_protocol.py`)
- Added `start_session()` method to mark execution start
- Enhanced `log_node_start()` to include `node_type` parameter
- Enhanced `log_node_end()` to include `output_data` parameter
- Added `log_to_node()` method for node-specific logging

### 3. Updated ExecutionManager (`lighthouse/application/services/execution_manager.py`)
- Added optional `logger: ILogger` parameter to constructor
- Integrated logging calls throughout execution lifecycle:
  - `create_session()` - Creates logging session with metadata
  - `start_session()` - Marks session as started
  - `end_session()` - Finalizes logs with duration
  - `log_node_start()` - Logs node execution start with node type
  - `log_node_end()` - Logs node completion with output data
- Added `log_to_node()` helper method for direct node logging

### 4. Updated WorkflowOrchestrator (`lighthouse/application/services/workflow_orchestrator.py`)
- Modified `_execute_node()` to pass node type to `log_node_start()`

### 5. Updated ServiceContainer (`lighthouse/container.py`)
- Added `logger: Optional[ILogger]` to ServiceContainer dataclass
- Updated `create_container()` with new parameters:
  - `enable_logging: bool = True` - Toggle logging on/off
  - `logs_dir: str = ".logs"` - Configure log directory
- Logger is instantiated and injected into ExecutionManager

### 6. Created Integration Test (`test_logging_integration.py`)
- Verifies end-to-end logging functionality
- Tests directory creation, log file generation, and metadata tracking
- Confirms all 426 existing tests still pass

## Directory Structure

Each execution creates the following structure:

```
.logs/
├── .gitignore                    # Prevents logs from being committed
├── execution_registry.json       # Registry of all executions
└── <session_id>/                 # One directory per execution
    ├── execution_metadata.json   # Execution details and node records
    ├── execution_summary.log     # High-level execution events
    ├── errors.log               # All errors (if any)
    ├── <node_id>_<node_name>.log # Individual node log files
    └── ...
```

## Log File Formats

### Node Log File (`<node_id>_<node_name>.log`)
```
[2026-01-07 21:04:38.370] [INFO] [node_id] Started execution of NodeName (NodeType)
[2026-01-07 21:04:38.371] [INFO] [node_id] Output data: {...}
[2026-01-07 21:04:38.371] [INFO] [node_id] Node execution COMPLETED (Duration: 0.00s)
```

### Execution Summary Log (`execution_summary.log`)
```
[2026-01-07 21:04:38.370] [INFO] [SYSTEM] Execution session <id> initialized
[2026-01-07 21:04:38.371] [INFO] [node_id] Node NodeName execution started
[2026-01-07 21:04:38.371] [INFO] [node_id] Node execution COMPLETED (Duration: 0.00s)
[2026-01-07 21:04:38.734] [INFO] [SYSTEM] Execution <id> COMPLETED (Duration: 0.36s)
```

### Execution Metadata (`execution_metadata.json`)
```json
{
  "id": "6e200ee2",
  "status": "COMPLETED",
  "created_at": "2026-01-07T21:04:38.370322",
  "started_at": "2026-01-07T21:04:38.370759",
  "ended_at": "2026-01-07T21:04:38.733162",
  "duration_seconds": 0.362398,
  "workflow_id": "test_workflow",
  "workflow_name": "Test Workflow",
  "triggered_by": "fe2ec76a",
  "node_count": 3,
  "nodes_executed": 3,
  "nodes_failed": 0,
  "log_directory": ".logs/6e200ee2",
  "execution_order": ["fe2ec76a", "aa72fd94", "96b04d30"],
  "node_logs": [
    {
      "node_id": "fe2ec76a",
      "node_name": "TestInput",
      "node_type": "InputNode",
      "execution_id": "6e200ee2",
      "status": "COMPLETED",
      "started_at": "2026-01-07T21:04:38.370899",
      "ended_at": "2026-01-07T21:04:38.371151",
      "duration_seconds": 0.000254,
      "log_file": "fe2ec76a_TestInput.log",
      "error_message": null
    }
  ]
}
```

## Usage

### Default (Logging Enabled)
```python
from lighthouse.container import create_headless_container

# Create container with logging enabled (default)
container = create_headless_container()

# Execute workflow - logs will be created automatically
result = container.workflow_orchestrator.execute_workflow(workflow, triggered_by)

# Access logger if needed
logger = container.logger
```

### Disable Logging
```python
from lighthouse.container import create_container

# Create container without logging
container = create_container(enable_logging=False)
```

### Custom Log Directory
```python
from lighthouse.container import create_container

# Use custom log directory
container = create_container(logs_dir="./custom_logs")
```

## Testing

Run the integration test:
```bash
python3 test_logging_integration.py
```

All existing tests pass:
```bash
pytest tests/ -v
# 426 passed in 57.85s
```

## Benefits

1. **Debugging**: Each node execution is logged separately, making it easy to trace issues
2. **Auditing**: Complete execution history with timestamps and durations
3. **Analysis**: Structured JSON metadata enables programmatic analysis
4. **Performance Tracking**: Duration metrics for each node and overall execution
5. **Error Tracking**: Dedicated error log with full error messages
6. **Clean Architecture**: Logger is injected via DI, maintaining separation of concerns

## Backward Compatibility

- Logging is enabled by default but can be disabled
- No breaking changes to existing API
- All existing tests pass without modification
- Legacy code in `src/` remains unchanged
