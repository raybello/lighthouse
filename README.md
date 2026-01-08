# Lighthouse

A visual node-based workflow editor built with DearPyGui. Create and connect nodes for workflow automation with dynamic expression evaluation.

## Features

- **Visual Node Editor** - Drag-and-drop interface with node connections and minimap
- **Dynamic Expressions** - Reference upstream node outputs using `{{$node["NodeName"].data.property}}` syntax
- **Multiple Node Types**:
  - **Trigger Nodes**: Manual Trigger, Input
  - **Execution Nodes**: HTTP Request, Execute Command, Calculator, Form, Code, Chat Model
- **Expression Engine** - Supports arithmetic, comparisons, and nested property access
- **Execution Logging** - Track workflow runs with detailed session logs
- **Clean Architecture** - Layered design with dependency injection for testability

## Installation

### Requirements

- Python 3.11+
- macOS, Linux, or Windows

### Setup

```bash
# Clone the repository
git clone https://github.com/raybello/local-llm.git
cd local-llm

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

## Usage

### Run the Application

```bash
python main.py
```

### Using the Node Editor

1. **Add Nodes**: Right-click in the canvas to open the context menu
2. **Connect Nodes**: Drag from an output port to an input port
3. **Configure Nodes**: Click the edit button on a node to open its inspector
4. **Execute Workflow**: Click the play button on a trigger node

### Expression Syntax

Use `{{}}` expressions to reference data from upstream nodes:

```
{{$node["NodeName"].data.property}}     # Access node output
{{$node["Input"].data.age * 2}}         # Arithmetic operations
{{$node["Input"].data.age >= 18}}       # Boolean comparisons
{{$node["API"].data.items[0].id}}       # Array access
```

## Development

### Run Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/domain/test_expression_service.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Linting
ruff check lighthouse/

# Format code
ruff format lighthouse/

# Type checking
mypy lighthouse/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Architecture

Lighthouse follows Clean Architecture principles with four layers:

```
┌─────────────────────────────────────────────────┐
│   Presentation Layer (DearPyGui UI)             │
├─────────────────────────────────────────────────┤
│   Application Layer (Use Cases, Orchestration)  │
├─────────────────────────────────────────────────┤
│   Domain Layer (Business Logic, Models)         │
├─────────────────────────────────────────────────┤
│   Infrastructure Layer (Logging, HTTP, etc.)    │
└─────────────────────────────────────────────────┘
```

### Key Components

- **Domain Layer** (`lighthouse/domain/`): Pure business logic with zero external dependencies
  - Models: Node, Workflow, ExecutionResult
  - Services: ExpressionService, TopologyService
  - Protocols: INode, IExecutor, ILogger, INodeRenderer

- **Application Layer** (`lighthouse/application/`): Orchestrates domain operations
  - WorkflowOrchestrator: Coordinates workflow execution
  - NodeFactory: Creates node instances
  - ExecutionManager: Manages execution sessions

- **Presentation Layer** (`lighthouse/presentation/`): UI components
  - LighthouseUI: Main application window
  - ThemeManager: Visual theming
  - DearPyGuiNodeRenderer: Node rendering

- **Infrastructure Layer** (`lighthouse/infrastructure/`): External dependencies
  - FileLogger: File-based logging
  - HTTP clients, command execution

### Dependency Injection

Services are wired through a `ServiceContainer`:

```python
from lighthouse.container import create_container

# Create container with all dependencies
container = create_container()

# Access services
orchestrator = container.workflow_orchestrator
factory = container.node_factory
```

## Project Structure

```
lighthouse/
├── main.py                    # Entry point
├── lighthouse/
│   ├── domain/                # Business logic
│   │   ├── models/            # Domain models
│   │   ├── protocols/         # Interfaces
│   │   └── services/          # Domain services
│   ├── application/           # Use cases
│   │   └── services/          # App services
│   ├── infrastructure/        # External deps
│   │   └── logging/           # Logging impl
│   ├── presentation/          # UI layer
│   │   └── dearpygui/         # DearPyGui UI
│   ├── nodes/                 # Node implementations
│   │   ├── trigger/           # Trigger nodes
│   │   └── execution/         # Execution nodes
│   ├── container.py           # DI container
│   └── config.py              # Configuration
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
└── src/                       # Legacy implementation
```

## Build Executable

```bash
# macOS/Linux
pyinstaller --onefile main.py --name lighthouse --add-data "fonts:fonts"

# Windows
pyinstaller --onefile main.py --name lighthouse --add-data "fonts;fonts"
```

## Release

```bash
git tag -a v[version] -m "Release v[version]"
git push origin v[version]
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [DearPyGui](https://github.com/hoffstadt/DearPyGui)
- Inspired by workflow automation platforms like [N8n](https://n8n.io/)
