# Lighthouse Workflow Editor

A professional visual node-based workflow editor built with [DearPyGui](https://github.com/hoffstadt/DearPyGui) for creating, configuring, and connecting execution and trigger nodes. Supports HTTP requests, shell command execution, and chat/language model integrations with a drag-and-drop interface.

## 🚀 Overview

Lighthouse is a production-ready workflow automation platform similar to N8n, designed for creating complex node-based workflows with comprehensive execution tracking, logging, and monitoring capabilities. The application provides a visual interface for connecting various node types while maintaining enterprise-grade observability and audit trails.

## 📋 Current Features

### Core Workflow Editor
- **Drag-and-drop node editor** with visual connections and minimap navigation
- **Trigger nodes** for starting workflows manually (ManualTrigger, scheduled triggers)
- **Execution nodes** for:
  - HTTP requests (GET, POST, PATCH, PUT, DELETE)
  - Shell command execution with configurable logging
  - Chat/AI model queries (Gemma, GPT, custom endpoints)
- **Dynamic inspector UI** for configuring node parameters
- **Context menus** for quick node creation and management
- **Modern dark interface** with rounded UI elements and professional theming
- **Real-time status indicators** with execution feedback

### Architecture
- **Modular node system** with abstract base classes for extensibility
- **Topological execution engine** for proper dependency resolution
- **Event-driven architecture** with callback-based node communication
- **Type-safe configuration** with enum-based node type management

---

## 🎯 Product Requirements: Execution Tracking & Logging System

### 1. Executive Summary

This document defines the requirements for implementing a comprehensive execution tracking and logging system that will transform Lighthouse into an enterprise-grade workflow automation platform. The system will provide complete execution audit trails, real-time monitoring, and professional-grade observability.

### 2. Problem Statement

The current system lacks production-ready execution tracking:
- No persistent execution logs or audit trails
- No real-time execution monitoring capabilities
- No per-node output capture to structured log files
- No historical execution review or analysis tools
- Limited observability for debugging and optimization

### 3. Solution Vision

Implement a robust execution tracking and logging system that provides:
- Complete execution audit trail with hierarchical organization
- Real-time execution monitoring with live status updates
- Per-node output capture to structured log files
- Historical execution review and analysis capabilities
- Professional-grade workflow observability

## 🏗️ Technical Architecture

### System Components

```
LighthouseApp (main.py)
├── LighthouseApp (src/lighthouse.py)
│   ├── Node Editor UI
│   ├── Execution Management
│   └── Log Viewer Interface
├── Executor (src/executor.py)
│   ├── Execution Engine
│   ├── Session Management
│   └── Logging Integration
├── Node System (src/nodes.py, src/node_base.py)
│   ├── NodeBase (Abstract)
│   ├── Trigger Nodes
│   └── Execution Nodes
└── Logging Service (NEW)
    ├── ExecutionSession Manager
    ├── Log File Management
    └── Real-time Monitoring
```

### File System Structure

```
lighthouse/
├── main.py
├── src/
│   ├── lighthouse.py
│   ├── executor.py
│   ├── nodes.py
│   ├── node_base.py
│   └── logging_service.py (NEW)
├── .logs/ (NEW)
│   ├── {execution_id}/
│   │   ├── execution_metadata.json
│   │   ├── {node_id}_{node_name}.log
│   │   ├── execution_summary.log
│   │   └── errors.log
│   └── execution_registry.json
└── README.md
```

## 📊 Functional Requirements

### 6.1 Execution Management System

#### 6.1.1 Execution Session Tracking
- **REQ-6.1.1.1**: Generate unique execution ID (format: `exec_{timestamp}_{8char}`)
- **REQ-6.1.1.2**: Capture execution metadata (timestamp, triggered by, node count, topology)
- **REQ-6.1.1.3**: Track execution state (INITIALIZING, RUNNING, COMPLETED, FAILED, CANCELLED)
- **REQ-6.1.1.4**: Maintain execution duration metrics with millisecond precision
- **REQ-6.1.1.5**: Store execution topology and node dependency graph

#### 6.1.2 Node-Level Execution Tracking
- **REQ-6.1.2.1**: Track individual node execution states with timestamps
- **REQ-6.1.2.2**: Capture node input/output data flow and transformations
- **REQ-6.1.2.3**: Record node execution performance metrics (CPU, memory, duration)
- **REQ-6.1.2.4**: Capture node execution errors with full stack traces
- **REQ-6.1.2.5**: Track inter-node data transfers and connection integrity

### 6.2 Logging Infrastructure

#### 6.2.1 Log File Management
- **REQ-6.2.1.1**: Create `.logs` directory structure with proper permissions
- **REQ-6.2.1.2**: Generate execution-specific subdirectories
- **REQ-6.2.1.3**: Create per-node log files with standardized naming
- **REQ-6.2.1.4**: Implement log rotation (100MB max per file, 10 files retention)
- **REQ-6.2.1.5**: Maintain log cleanup and archival procedures

#### 6.2.2 Log Content Standards
- **REQ-6.2.2.1**: Standardized log format: `[TIMESTAMP] [LEVEL] [NODE_ID] MESSAGE`
- **REQ-6.2.2.2**: Capture stdout/stderr for command execution nodes
- **REQ-6.2.2.3**: Log HTTP request/response details (headers, status, body)
- **REQ-6.2.2.4**: Record AI model interactions (prompts, responses, tokens)
- **REQ-6.2.2.5**: Include execution context and environment metadata

### 6.3 Real-Time Monitoring Interface

#### 6.3.1 Execution Dashboard
- **REQ-6.3.1.1**: Create dedicated "Execution Logs" tab in main interface
- **REQ-6.3.1.2**: Display currently running executions with live progress bars
- **REQ-6.3.1.3**: Show real-time node execution status with color indicators
- **REQ-6.3.1.4**: Provide execution summary statistics (success rate, avg duration)
- **REQ-6.3.1.5**: Implement auto-refresh (1-second intervals) for live monitoring

#### 6.3.2 Hierarchical Log Display
- **REQ-6.3.2.1**: Collapsible headers for execution sessions (click to expand/collapse)
- **REQ-6.3.2.2**: Display execution metadata in headers (timestamp, status, duration)
- **REQ-6.3.2.3**: Show nested node logs with syntax highlighting
- **REQ-6.3.2.4**: Implement log level filtering (DEBUG, INFO, WARN, ERROR)
- **REQ-6.3.2.5**: Support regex search across all log content

### 6.4 Historical Execution Review

#### 6.4.1 Execution History
- **REQ-6.4.1.1**: Maintain execution registry with JSON-based metadata storage
- **REQ-6.4.1.2**: Provide date-range filtering with calendar picker
- **REQ-6.4.1.3**: Support execution status filtering (success, failure, cancelled)
- **REQ-6.4.1.4**: Enable full-text search across execution logs and metadata
- **REQ-6.4.1.5**: Export execution reports (CSV, JSON, PDF formats)

#### 6.4.2 Log Analysis Tools
- **REQ-6.4.2.1**: Display execution performance trends and analytics
- **REQ-6.4.2.2**: Show node execution frequency and success rates
- **REQ-6.4.2.3**: Provide error pattern analysis with root cause identification
- **REQ-6.4.2.4**: Support log comparison between different executions
- **REQ-6.4.2.5**: Generate automated execution summary reports

## 🎨 User Interface Design

### Execution Logs Tab Layout

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Execution Logs                                            │
├─────────────────────────────────────────────────────────────┤
│ [🔄 Running] [✅ Completed] [❌ Failed] [🔍 Search...]        │
├─────────────────────────────────────────────────────────────┤
│ ▼ exec_20250107_abc12345 | 🟡 RUNNING | ⏱️ 0:45 | 📁 View   │
│   ▶ cmd_def678 | 🟡 RUNNING | ⏱️ 0:10 | 📄 stdout.log      │
│   ▶ http_ghi901 | ✅ COMPLETED | ⏱️ 0:30 | 📄 response.log  │
│   ▶ chat_jkl234 | ⏸️ PENDING | ⏱️ - | 📄 query.log         │
├─────────────────────────────────────────────────────────────┤
│ ▼ exec_20250107_mno67890 | ✅ COMPLETED | ⏱️ 2:15 | 📁 View  │
│   ▶ trigger_pqr345 | ✅ COMPLETED | ⏱️ 0:05 | 📄 trigger.log   │
│   ▶ cmd_stu012 | ✅ COMPLETED | ⏱️ 1:30 | 📄 stdout.log      │
│   ▶ http_vwx567 | ❌ ERROR | ⏱️ 0:40 | 📄 error.log        │
└─────────────────────────────────────────────────────────────┘
```

### UI Components Specification

#### Status Indicators
- **🟡 RUNNING**: Yellow circle for active executions
- **✅ COMPLETED**: Green checkmark for successful executions
- **❌ ERROR**: Red X for failed executions
- **⏸️ PENDING**: Pause symbol for queued executions
- **⏹️ CANCELLED**: Stop symbol for cancelled executions

#### Interactive Elements
- **Collapsible Headers**: Click to expand/collapse execution details
- **Log File Links**: Click to open log content in modal viewer
- **Directory Links**: Click to open execution directory in file explorer
- **Search Bar**: Real-time filtering with regex support
- **Export Buttons**: Context-sensitive export options

## 📈 Data Models

### ExecutionSession Structure
```json
{
  "id": "exec_20250107_abc12345",
  "status": "RUNNING|COMPLETED|FAILED|CANCELLED",
  "created_at": "2025-01-07T10:30:00.000Z",
  "started_at": "2025-01-07T10:30:05.000Z",
  "ended_at": "2025-01-07T10:32:20.000Z",
  "duration_seconds": 135,
  "triggered_by": "manual_trigger_def678",
  "node_count": 3,
  "nodes_executed": 2,
  "nodes_failed": 1,
  "log_directory": ".logs/exec_20250107_abc12345/",
  "topology": {
    "nodes": ["cmd_def678", "http_ghi901", "chat_jkl234"],
    "edges": [["cmd_def678", "http_ghi901"], ["http_ghi901", "chat_jkl234"]]
  },
  "performance_metrics": {
    "total_cpu_time": 45.2,
    "peak_memory_mb": 128.5,
    "io_operations": 1024
  }
}
```

### NodeExecutionLog Structure
```json
{
  "node_id": "cmd_def678",
  "node_name": "Execute Command",
  "node_type": "ExecuteCommandNode",
  "execution_id": "exec_20250107_abc12345",
  "status": "COMPLETED",
  "started_at": "2025-01-07T10:30:05.000Z",
  "ended_at": "2025-01-07T10:30:35.000Z",
  "duration_seconds": 30,
  "input_data": {
    "command": "echo 'Hello World'",
    "log_file": "cmd_def678_Execute_Command.log"
  },
  "output_data": {
    "stdout": "Hello World\n",
    "stderr": "",
    "exit_code": 0
  },
  "log_file": "cmd_def678_Execute_Command.log",
  "error_message": null,
  "performance_metrics": {
    "cpu_time_seconds": 0.05,
    "memory_peak_mb": 8.2,
    "io_read_bytes": 1024,
    "io_write_bytes": 512
  }
}
```

## 🛠️ Implementation Plan

### Phase 1: Core Logging Infrastructure (Sprint 1 - 2 weeks)

#### Tasks
1. **Create LoggingService Class**
   - Implement `src/logging_service.py`
   - Add execution session management
   - Create log file management utilities

2. **Extend Executor Integration**
   - Modify `src/executor.py` to integrate logging
   - Update `create_execution()` to initialize logging
   - Enhance `begin_execution()` and `end_execution()` for log capture

3. **File System Setup**
   - Create `.logs` directory structure
   - Implement log file creation and rotation
   - Add error handling for file operations

#### Acceptance Criteria
- All executions create unique log directories
- Per-node log files are created and populated
- Execution metadata is captured and stored
- Log rotation policies are enforced

### Phase 2: UI Integration (Sprint 2 - 2 weeks)

#### Tasks
1. **Create Execution Logs Tab**
   - Add new tab to main window in `src/lighthouse.py`
   - Implement hierarchical log display with DearPyGui widgets
   - Add collapsible headers and status indicators

2. **Real-time Updates**
   - Implement live execution status updates
   - Add auto-refresh functionality
   - Create log streaming interface

3. **Log Viewer Components**
   - Build log content viewer with syntax highlighting
   - Add search and filtering capabilities
   - Implement export functionality

#### Acceptance Criteria
- Execution logs tab displays running and completed executions
- Real-time status updates work correctly
- Log content is viewable and searchable
- Export functions work for all formats

### Phase 3: Advanced Features (Sprint 3 - 2 weeks)

#### Tasks
1. **Historical Execution Review**
   - Implement execution registry with search
   - Add date-range and status filtering
   - Create execution comparison tools

2. **Analytics and Reporting**
   - Build performance analytics dashboard
   - Add error pattern analysis
   - Create automated report generation

3. **Performance Optimization**
   - Implement asynchronous log writing
   - Add caching for log retrieval
   - Optimize UI rendering for large log sets

#### Acceptance Criteria
- Historical executions are searchable and filterable
- Performance analytics display meaningful insights
- System handles high-volume logging without performance degradation

## 🧪 Testing Strategy

### Unit Testing
- **LoggingService**: Test log creation, file management, and session tracking
- **Executor Integration**: Test execution lifecycle with logging
- **UI Components**: Test log viewer functionality and interactions

### Integration Testing
- **End-to-End Execution**: Test complete workflow with logging
- **File System Operations**: Test log file creation and rotation
- **UI Integration**: Test real-time log updates and display

### Performance Testing
- **Load Testing**: Test with multiple concurrent executions
- **Volume Testing**: Test with large log files and execution history
- **UI Responsiveness**: Test interface performance under load

## 📊 Success Metrics

### Technical Metrics
- **Execution Visibility**: 100% of executions tracked and logged
- **Log Completeness**: All node outputs captured in structured logs
- **UI Performance**: Sub-2-second log retrieval for recent executions
- **System Reliability**: <1% logging system failures
- **Performance Impact**: <5% overhead on execution performance

### User Experience Metrics
- **User Adoption**: 90% of users utilize execution logs for debugging
- **Task Completion**: 85% reduction in debugging time
- **User Satisfaction**: 4.5/5 rating for logging features
- **Feature Usage**: Daily active users for log review functionality

## 🔧 Development Guidelines

### Code Standards
- Follow Python PEP 8 style guidelines
- Use type hints for all function signatures
- Implement comprehensive error handling
- Add docstrings for all public methods

### Architecture Principles
- Maintain separation of concerns between logging and execution
- Use dependency injection for testability
- Implement async patterns for file I/O operations
- Design for extensibility and maintainability

### Security Considerations
- Validate file paths to prevent directory traversal
- Sanitize log content to prevent injection attacks
- Implement proper file permissions for log directories
- Consider log encryption for sensitive data

## 🚀 Deployment & Release

### Version Management
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Maintain CHANGELOG.md with detailed release notes
- Use git tags for version releases

### Release Process
```bash
# Create release
pyinstaller --onefile main.py --name lighthouse --add-data "fonts:fonts"
git tag -a v2.0.0 -F CHANGELOG.md
git push origin v2.0.0

# Build distribution
pyinstaller --onefile main.py --name lighthouse --add-data "fonts:fonts"
```

### Migration Strategy
- Backward compatibility for existing workflows
- Data migration for execution history
- Gradual rollout with feature flags

## 🤝 Contributing Guidelines

### Development Workflow
1. Fork repository and create feature branch
2. Implement changes with comprehensive tests
3. Update documentation and CHANGELOG.md
4. Submit pull request with detailed description

### Code Review Process
- All changes require peer review
- Automated tests must pass
- Documentation must be updated
- Performance impact must be assessed

## 📞 Support & Maintenance

### Bug Reporting
- Use GitHub Issues for bug reports
- Include execution logs and system information
- Provide steps to reproduce issues

### Feature Requests
- Submit feature requests via GitHub Discussions
- Include use case and implementation suggestions
- Community feedback encouraged

---

## 🔄 Releasing New Versions

```bash
# Create versioned release
pyinstaller --onefile main.py --name lighthouse --add-data "fonts:fonts"
git tag -a v[version] -F CHANGELOG.md
git push origin v[version]
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [DearPyGui](https://github.com/hoffstadt/DearPyGui)
- Inspired by workflow automation platforms like [N8n](https://n8n.io/)
- Thanks to the open-source community for contributions and feedback