# Lighthouse

A visual node-based workflow automation engine built with DearPyGui. Lighthouse provides a directed acyclic graph (DAG) execution model with dynamic expression evaluation, enabling users to compose complex data pipelines through an intuitive drag-and-drop interface.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-426%20passed-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen.svg)]()

## Overview

Lighthouse implements a modular workflow execution system where nodes represent discrete operations connected via typed ports. The execution engine performs topological sorting to determine evaluation order, resolving inter-node dependencies through a context-aware expression system.

### Core Capabilities

- **DAG-Based Execution** - Topologically sorted node evaluation with dependency resolution
- **Expression Engine** - Runtime interpolation using `{{$node["name"].data.property}}` syntax with support for arithmetic, comparisons, and nested property access
- **Extensible Node System** - Protocol-based node architecture enabling custom node implementations
- **Session Management** - Comprehensive execution tracking with per-node timing and result capture
- **Dependency Injection** - Service container architecture for testability and modularity

### Node Types

| Category | Nodes | Description |
|----------|-------|-------------|
| **Trigger** | `ManualTrigger`, `Input` | Workflow entry points; no upstream dependencies |
| **Execution** | `HTTPRequest`, `ExecuteCommand`, `Calculator`, `Form`, `Code`, `ChatModel` | Data transformation and external integrations |

## Requirements

- Python 3.11+
- macOS, Linux, or Windows
- DearPyGui 1.11.1+

## Installation

```bash
git clone https://github.com/raybello/local-llm.git
cd local-llm

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e .

# Development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
python3 main.py
```
or
```bash
python3 -c "from lighthouse.presentation.dearpygui.app import run_app; run_app()"
```

### Programmatic Usage

```python
from lighthouse.container import create_headless_container
from lighthouse.domain.models.workflow import Workflow

# Initialize service container
container = create_headless_container()
factory = container.node_factory

# Create nodes
input_node = factory.create_node("Input", name="UserData")
input_node.set_state({"properties": [{"key": "value", "value": "42"}]})

calc_node = factory.create_node("Calculator", name="Processor")
calc_node.set_state({"expression": "{{$node['UserData'].data.value}} * 2"})

# Build workflow
workflow = Workflow(id="pipeline", name="Data Pipeline")
workflow.add_node(input_node)
workflow.add_node(calc_node)
workflow.add_connection(input_node.id, calc_node.id)

# Execute
result = container.workflow_orchestrator.execute_workflow(
    workflow,
    triggered_by=input_node.id
)
```

## Architecture

Lighthouse follows Clean Architecture principles with strict layer separation:

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer                                         │
│  └── DearPyGui UI, Node Renderer, Theme Manager             │
├─────────────────────────────────────────────────────────────┤
│  Application Layer                                          │
│  └── WorkflowOrchestrator, NodeFactory, ExecutionManager    │
├─────────────────────────────────────────────────────────────┤
│  Domain Layer (Zero External Dependencies)                  │
│  └── Models, Protocols, ExpressionService, TopologyService  │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                       │
│  └── FileLogger, HTTP Clients, Command Execution            │
└─────────────────────────────────────────────────────────────┘
```

### Component Overview

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **Domain** | `ExpressionService` | Parses and evaluates `{{}}` expressions against execution context |
| **Domain** | `TopologyService` | Computes topological ordering for DAG traversal |
| **Application** | `WorkflowOrchestrator` | Coordinates end-to-end workflow execution |
| **Application** | `NodeFactory` | Instantiates nodes from registry by type identifier |
| **Application** | `ExecutionManager` | Tracks session state and node execution records |
| **Presentation** | `DearPyGuiNodeRenderer` | Renders node UI components and handles user interaction |

### Execution Pipeline

1. **Trigger** - User initiates workflow from a trigger node
2. **Topology Resolution** - `TopologyService.topological_sort()` determines execution order
3. **Context Building** - For each node, upstream results are aggregated into execution context
4. **Expression Resolution** - `ExpressionService.resolve()` interpolates expressions in node state
5. **Node Execution** - `node.execute(context)` performs the node's operation
6. **Result Capture** - `ExecutionManager` records timing, status, and output data

### Expression Syntax

```
{{$node["NodeName"].data.property}}       # Property access
{{$node["Input"].data.count * 2}}         # Arithmetic operations
{{$node["Input"].data.age >= 18}}         # Boolean comparisons
{{$node["API"].data.items[0].id}}         # Array indexing
{{$node["Config"].data.settings.nested}}  # Nested property access
```

## Project Structure

```
lighthouse/
├── container.py                 # DI container configuration
├── config.py                    # Application settings
├── domain/
│   ├── models/
│   │   ├── node.py              # Node, ExecutionResult, NodeMetadata
│   │   ├── workflow.py          # Workflow, Connection
│   │   ├── execution.py         # ExecutionSession, NodeExecutionRecord
│   │   └── field_types.py       # FieldDefinition, FieldType enums
│   ├── protocols/               # INode, IExecutor, ILogger, INodeRenderer
│   ├── services/
│   │   ├── expression_service.py
│   │   ├── topology_service.py
│   │   └── context_builder.py
│   └── exceptions.py
├── application/
│   └── services/
│       ├── node_factory.py
│       ├── execution_manager.py
│       └── workflow_orchestrator.py
├── nodes/
│   ├── base/base_node.py        # Abstract base implementation
│   ├── trigger/                 # ManualTrigger, Input
│   ├── execution/               # Calculator, HTTPRequest, Code, etc.
│   └── registry.py              # Dynamic node type registry
├── presentation/
│   └── dearpygui/
│       ├── app.py
│       ├── theme_manager.py
│       └── node_renderer.py
└── infrastructure/
    └── logging/
tests/
├── unit/                        # Isolated component tests
└── integration/                 # End-to-end workflow tests
```

## Development

### Testing

```bash
# Full test suite with coverage
pytest tests/ -v --cov=lighthouse --cov-report=html

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific module
pytest tests/unit/domain/test_expression_service.py -v
```

### Code Quality

```bash
# Linting
ruff check lighthouse/

# Formatting
ruff format lighthouse/

# Type checking
mypy lighthouse/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Building

```bash
# Package build
python -m build

# Standalone executable
pyinstaller --onefile main.py --name lighthouse --add-data "fonts:fonts"
```

## API Reference

### ServiceContainer

```python
from lighthouse.container import create_headless_container, create_ui_container

# Headless mode (testing, scripting)
container = create_headless_container()

# UI mode (full application)
container = create_ui_container()
```

### Node Protocol

```python
from lighthouse.domain.protocols import INode

class CustomNode(INode):
    def execute(self, context: dict) -> ExecutionResult:
        # Implementation
        pass

    def get_state(self) -> dict:
        pass

    def set_state(self, state: dict) -> None:
        pass
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [DearPyGui](https://github.com/hoffstadt/DearPyGui) - Immediate mode GUI framework
- [n8n](https://n8n.io/) - Workflow automation inspiration
