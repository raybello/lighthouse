# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lighthouse is a visual node-based workflow editor built with DearPyGui. It allows users to create and connect nodes for workflow automation, similar to N8n. The application supports dynamic expression evaluation with `{{}}` syntax, allowing nodes to reference outputs from upstream nodes.

**Version 2.0** introduces a clean architecture with proper separation of concerns, dependency injection, and comprehensive test coverage.

## Commands

### Run the Application
```bash
# Run with legacy code (original implementation)
python main.py

# Run with new architecture (v2.0 - recommended)
python3 -c "from lighthouse.presentation.dearpygui.app import run_app; run_app()"
```

### Testing Workflow (For Development)
When making changes to the application, follow this workflow:
1. Run tests: `pytest tests/ --tb=short -q`
2. Run the GUI app for user testing
3. User provides feedback after each execution
4. Iterate based on feedback

### Run Tests
```bash
# Run all tests with coverage
pytest tests/ -v --cov=lighthouse

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v
```

### Development
```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check lighthouse/

# Run type checking
mypy lighthouse/

# Setup pre-commit hooks
pre-commit install
```

### Build & Release
```bash
# Build package
python -m build

# Create release
git tag -a v[version] -m "Release v[version]"
git push origin v[version]
```

## Architecture (v2.0)

### Layered Architecture (Clean Architecture)

```
┌─────────────────────────────────────────────────┐
│   Presentation Layer (UI) - depends on ↓        │
│   lighthouse/presentation/                      │
├─────────────────────────────────────────────────┤
│   Application Layer (Use Cases) - depends on ↓  │
│   lighthouse/application/                       │
├─────────────────────────────────────────────────┤
│   Domain Layer (Business Logic) - zero deps    │
│   lighthouse/domain/                            │
├─────────────────────────────────────────────────┤
│   Infrastructure Layer (External) - implements ↑│
│   lighthouse/infrastructure/                    │
└─────────────────────────────────────────────────┘
```

### Directory Structure

```
lighthouse/
├── __init__.py
├── container.py              # DI container - wires all services
├── config.py                 # Application configuration
│
├── domain/                   # Pure business logic (no external deps)
│   ├── models/              # Domain entities
│   │   ├── node.py          # Node, ExecutionResult, NodeMetadata
│   │   ├── workflow.py      # Workflow, Connection
│   │   ├── execution.py     # ExecutionSession, NodeExecutionRecord
│   │   └── field_types.py   # FieldDefinition, FieldType
│   ├── protocols/           # Interfaces (INode, IExecutor, etc.)
│   ├── services/            # Domain services
│   │   ├── expression_service.py  # Expression evaluation
│   │   ├── topology_service.py    # Graph algorithms
│   │   └── context_builder.py     # Context building
│   └── exceptions.py        # Domain exceptions
│
├── application/             # Application services
│   └── services/
│       ├── node_factory.py          # Creates node instances
│       ├── execution_manager.py     # Manages execution sessions
│       └── workflow_orchestrator.py # Coordinates execution
│
├── nodes/                   # Node implementations
│   ├── base/
│   │   └── base_node.py     # Abstract base (pure domain)
│   ├── trigger/             # Trigger nodes
│   │   ├── manual_trigger_node.py
│   │   └── input_node.py
│   ├── execution/           # Execution nodes
│   │   ├── calculator_node.py
│   │   ├── http_node.py
│   │   ├── command_node.py
│   │   ├── code_node.py
│   │   ├── form_node.py
│   │   └── chat_model_node.py
│   └── registry.py          # Dynamic node registry
│
├── presentation/            # UI layer
│   └── dearpygui/
│       ├── app.py           # Main application
│       ├── theme_manager.py # Theme handling
│       └── node_renderer.py # Node rendering
│
└── infrastructure/          # External dependencies
    ├── logging/
    └── external/
```

### Key Components

#### Dependency Injection Container (`container.py`)
```python
from lighthouse.container import create_headless_container, create_ui_container

# For testing (no UI)
container = create_headless_container()

# For UI mode
container = create_ui_container()

# Access services
factory = container.node_factory
orchestrator = container.workflow_orchestrator
```

#### Node Creation
```python
from lighthouse.container import create_headless_container

container = create_headless_container()
factory = container.node_factory

# Create nodes
input_node = factory.create_node("Input", name="MyInput")
calc_node = factory.create_node("Calculator", name="Calc")
```

#### Workflow Execution
```python
from lighthouse.domain.models.workflow import Workflow

workflow = Workflow(id="test", name="Test Workflow")
workflow.add_node(input_node)
workflow.add_node(calc_node)
workflow.add_connection(input_node.id, calc_node.id)

result = container.workflow_orchestrator.execute_workflow(
    workflow,
    triggered_by=input_node.id
)
```

### Node Types

**Trigger Nodes** (no inputs, start workflows):
- `ManualTrigger` - Manual workflow trigger
- `Input` - Provides static data with property/value pairs

**Execution Nodes** (have inputs, perform actions):
- `Calculator` - Arithmetic operations with expression support
- `HTTPRequest` - HTTP requests (GET, POST, etc.)
- `ExecuteCommand` - Shell command execution
- `ChatModel` - LLM/chat model integration
- `Form` - Dynamic forms with typed fields
- `Code` - Sandboxed Python code execution

### Expression System

The `{{}}` expression syntax allows dynamic value references:
```
{{$node["NodeName"].data.property}}     # Access node output
{{$node["Input"].data.age * 2}}         # Arithmetic operations
{{$node["Input"].data.age >= 18}}       # Boolean comparisons
```

Expressions are resolved by `ExpressionService` using context from completed upstream nodes.

### Execution Flow (New Architecture)

1. `WorkflowOrchestrator.execute_workflow()` receives workflow and trigger node
2. `TopologyService.topological_sort()` determines execution order
3. For each node:
   - `ExpressionService.resolve()` evaluates expressions in node state
   - `node.execute(context)` runs the node logic
   - `ExecutionManager` tracks session and node records
4. Results returned with status and per-node outcomes

### Legacy Code (`src/`)

The original implementation remains in `src/` for backward compatibility:
- `src/lighthouse.py` - Main application class
- `src/node_base.py` - Legacy node base class
- `src/nodes.py` - Legacy node implementations
- `src/executor.py` - Legacy execution engine
- `src/expression_engine.py` - Legacy expression parser

## Testing

**426 tests with 87% code coverage**

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=lighthouse --cov-report=html
```

### Test Structure
```
tests/
├── unit/                    # Fast, isolated tests
│   ├── domain/             # Domain model tests
│   ├── nodes/              # Node implementation tests
│   └── application/        # Service tests
└── integration/            # End-to-end workflow tests
```

## Dependencies

- `dearpygui==1.11.1` - GUI framework
- `rich==14.2.0` - Console output formatting
- `requests>=2.31.0` - HTTP requests
- Python 3.11+

### Dev Dependencies
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `ruff` - Linting and formatting
- `mypy` - Type checking
- `pre-commit` - Git hooks
