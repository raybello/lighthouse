# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lighthouse is a visual node-based workflow editor built with DearPyGui. It allows users to create and connect nodes for workflow automation, similar to N8n. The application supports dynamic expression evaluation with `{{}}` syntax, allowing nodes to reference outputs from upstream nodes.

## Commands

### Run the Application
```bash
python main.py
```

### Run Tests
```bash
python test_expressions.py
python test_form_validation.py
python test_input_validation.py
```

### Build Executable
```bash
# macOS/Linux
pyinstaller --onefile main.py --name lighthouse --add-data "fonts:fonts"

# Windows
pyinstaller --onefile main.py --name lighthouse --add-data "fonts;fonts"
```

### Create Release
```bash
git tag -a v[version] -F CHANGELOG.md
git push origin v[version]
```

## Architecture

### Core Components

- **`main.py`** - Entry point, creates and runs `LighthouseApp`
- **`src/lighthouse.py`** - Main application class managing DearPyGui context, viewport, node editor, and workflow execution
- **`src/node_base.py`** - Abstract base class `NodeBase` defining node UI, state management, and inspector windows
- **`src/nodes.py`** - Concrete node implementations and node type enums (`ExecutionNodes`, `TriggerNodes`)
- **`src/executor.py`** - Workflow execution engine managing node context and expression resolution
- **`src/expression_engine.py`** - Parses and evaluates `{{}}` expressions with node context
- **`src/logging_service.py`** - Execution tracking, session management, and log file creation

### Node Types

**Trigger Nodes** (no inputs, start workflows):
- `ManualTriggerNode` - Manual workflow trigger
- `InputNode` - Provides static data with property/value pairs

**Execution Nodes** (have inputs, perform actions):
- `HTTPRequestNode` - HTTP requests (GET, POST, etc.) with JSON support
- `ExecuteCommandNode` - Shell command execution with stdout/stderr capture
- `ChatModelNode` - LLM/chat model integration (OpenAI-compatible API)
- `CalculatorNode` - Arithmetic operations with expression support
- `FormNode` - Dynamic forms with typed fields (string, number, boolean, object)
- `CodeNode` - Sandboxed Python code execution with 30s timeout

### Expression System

The `{{}}` expression syntax allows dynamic value references:
- `{{$node["NodeName"].data.property}}` - Access node output
- `{{$node["Input"].data.age * 2}}` - Arithmetic operations
- `{{$node["Input"].data.age >= 18}}` - Boolean comparisons

Expressions are resolved at runtime by `ExpressionEngine` using context built from completed upstream nodes.

### Execution Flow

1. `LighthouseApp._exec_graph()` performs topological sort of nodes
2. Context is built from previously completed nodes via `_build_context_from_completed_nodes()`
3. Each node executes in order via `_execute_step()`
4. Node outputs are stored in context for downstream expression resolution
5. `Executor` tracks all node inputs/outputs and manages logging

### UI Structure

- Primary window contains tabs: Node Editor and Execution Logs
- Node Editor uses DearPyGui's node editor with minimap
- Right-click context menu for adding nodes
- Each node has an inspector window for configuration (modal)
- Nodes support rename, delete, edit, and execute actions

## Dependencies

- `dearpygui==1.8.0` - GUI framework
- `rich==14.2.0` - Console output formatting
- `requests` - HTTP requests (for HTTPRequestNode and ChatModelNode)
- Python 3.11+
