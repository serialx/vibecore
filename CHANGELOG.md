# Changelog

All notable changes to vibecore will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0b1] - 2025-01-18

### Added
- **Flow Mode (Experimental)**: New programmatic conversation control system for building structured agent-based applications
  - `flow()` entry point for creating custom conversation flows
  - Support for multi-agent orchestration with handoffs
  - Examples adapted from OpenAI Agents SDK (basic.py, customer_service.py)
- **Web Tools**: New tools for web interaction
  - `websearch` tool with extensible backend architecture
  - `webfetch` tool for fetching and converting web content
- **Configurable Features**:
  - Make reasoning summary configurable via settings
  - Optional welcome message in VibecoreApp
  - Default model settings support

### Changed
- Default model updated to gpt-5
- Improved Flow API with type-safe user input
- Enhanced settings system with default_model_settings

### Fixed
- Early exit handling in flow prototype
- GitHub workflow conditions for stable PyPI releases
- Version detection using github.ref_name

### Documentation
- Flow Mode documented as key differentiator
- Added uvx as primary quick-test method

## [0.2.0] - Previous Release

[Previous release notes...]