# Changelog

## [1.0.11] - 2025-12-09

### Added
- Updated Changelog formatting to comply with [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

### Changed

### Fixed

### Removed


## [1.0.10] - 2025-12-05

### Added
- Node inspector now supports **multi-line string inputs** for long text fields.
- Minimap added for easier navigation of large workflows.
- Node context menu supports **rename** and **delete** actions.
- Support for **HTTP PATCH and DELETE methods** in HTTPRequestNode.

### Changed
- Updated UI theme with rounded buttons and modern dark mode styling.
- Node linking now shows active connection highlights.
- Execution logic improved to track node states (`idle`, `running`, `completed`, `error`).

### Fixed
- Bug where nodes could overlap when added near existing nodes.
- Issue where node inspector did not refresh after property changes.
- Fixed improper topological execution order in some workflow scenarios.

### Removed
- Deprecated `OldTriggerNode` removed from TriggerNodes enum.
