# Changelog

All notable changes to vibecore will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2025-01-12

### Changed
- **BREAKING**: Refactored Flow Mode into flexible multi-mode framework
  - Replaced `flow()` function with `Vibecore` class and `@vibecore.workflow()` decorator
  - Simplified workflow signature: removed explicit `app`, `ctx`, `user_input` parameters
  - Workflow functions now return typed results instead of void
  - Unified interface: `user_input()`, `print()`, `run_agent()` work across all modes

### Added
- **Multi-Mode Execution Support**: Run the same workflow in different modes
  - `run_textual()`: Full TUI with streaming (original behavior)
  - `run_cli()`: Simple stdin/stdout interaction
  - `run()`: Programmatic execution with predefined inputs (perfect for testing)
- **Runner Architecture**: Extensible pattern for adding new execution modes
  - `VibecoreRunnerBase`: Base class for all runners
  - `VibecoreTextualRunner`: TUI mode implementation
  - `VibecoreCliRunner`: CLI mode implementation
  - `VibecoreStaticRunner`: Static/testing mode implementation
- New example: `basic_cli.py` demonstrating CLI and static modes

### Benefits
- Cleaner, more Pythonic API with less boilerplate
- Type-safe workflow return values with generics
- Easy to test with static mode and predefined inputs
- Separation of concerns between runners and workflow logic
- Extensible: add new modes (HTTP, Discord, etc.) by implementing runner interface

## [0.4.2] - 2025-09-30

### Added
- **FeedbackWidget**: New widget for collecting user feedback

### Changed
- Remove input textarea autofocus on click for improved user experience

### Fixed
- Fix snapshot flakiness for executing message headers in tests
- Handle list_directory permission test when running as root

### Refactoring
- Consolidate todo item model for better code organization

### Documentation
- Add AGENTS.md and update CLAUDE.md

## [0.4.1] - 2025-09-19

### Fixed
- Prevent duplicate message processing during agent execution by ensuring mutually exclusive handling of user input vs queued messages

## [0.4.0] - 2025-01-30

### Added
- **Path Confinement System**: Enhanced security with comprehensive path validation
  - Configurable allowed and blocked paths via settings
  - Prevents access to sensitive system files and directories
  - Validates both file and shell operations
  - Supports pattern-based path restrictions
- **Copy Button for Agent Messages**: Added copy functionality to AgentMessage widget for improved user experience

### Security
- Implemented path confinement for file and shell tools to prevent unauthorized access
- Added comprehensive test coverage for path validation security boundaries

## [0.3.2] - 2025-01-25

### Fixed
- Disabled dotenv settings loading since vibecore is a framework library

## [0.3.1] - 2025-01-22

### Added
- Copy button for query arguments view to improve user experience

## [0.3.0] - 2025-01-22

### Added
- **Flow Mode (Experimental)**: New programmatic conversation control system for building structured agent-based applications
  - `flow()` entry point for creating custom conversation flows
  - Support for multi-agent orchestration with handoffs
  - Examples adapted from OpenAI Agents SDK (basic.py, customer_service.py)
- **Web Tools**: New tools for web interaction
  - `websearch` tool with extensible backend architecture
  - `webfetch` tool for fetching and converting web content
- **Anthropic Pro/Max OAuth authentication support**: Native integration with Claude Pro/Max accounts via OAuth flow
- **Rich tool call rendering**: New `rich_tool_names` setting for enhanced tool call display
- **Configurable Features**:
  - Make reasoning summary configurable via settings
  - Optional welcome message in VibecoreApp
  - Default model settings support

### Changed
- Default model updated to gpt-5
- Improved Flow API with type-safe user input
- Enhanced settings system with default_model_settings

### Fixed
- Tool call functionality with Claude Pro/Max authentication
- Tool call results not displaying properly in the UI
- Tool execution status handling during agent handoffs and response completion
- Early exit handling in flow prototype
- GitHub workflow conditions for stable PyPI releases
- Version detection using github.ref_name

### Documentation
- Flow Mode documented as key differentiator
- Added uvx as primary quick-test method

## [0.2.0] - Previous Release

[Previous release notes...]