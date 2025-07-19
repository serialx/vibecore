# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vibecore** is a Textual-based terminal user interface (TUI) application written in Python. It implements a chat-like interface with custom widgets for message display and input.

## IMPORTANT: Never Run This Application

⚠️ **WARNING**: This is a TUI application. DO NOT run `vibecore` or attempt to execute the application directly as it will interfere with Claude Code's terminal interface. Only work with the source code.

## Development Commands

### Environment Setup
This project uses `uv` as the package manager. Install dependencies with:
```bash
uv sync
```

### Code Quality Commands
```bash
# Linting and formatting with ruff
uv run ruff check .              # Check for linting issues
uv run ruff check . --fix        # Auto-fix linting issues
uv run ruff format .             # Format code

# Type checking with pyright
uv run pyright

# Run all quality checks
uv run ruff check . && uv run ruff format --check . && uv run pyright
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_filename.py

# Run tests with coverage
uv run pytest --cov=vibecore
```

## Architecture Overview

### Main Components

1. **VibecoreApp** (`src/vibecore/main.py`): The main application class that extends Textual's App
   - Manages the overall UI layout with Header, Footer, and scrollable message area
   - Handles theme toggling (dark/light mode)
   - Coordinates message flow between widgets

2. **Custom Widgets**:
   - **UserMessage**: Displays user messages with a ">" prefix
   - **MyTextArea**: Custom TextArea that captures Enter key to post messages
   - **InputBox**: Container for the text input area
   - **MyFooter**: Custom footer containing the input box

3. **Styling**: Uses TCSS (Textual CSS) defined in `stopwatch03.tcss` for visual styling

### Key Patterns

- **Message Flow**: User types in MyTextArea → Enter key triggers custom Message → VibecoreApp handles message → Creates UserMessage widget → Adds to VerticalScroll container
- **Widget Communication**: Uses Textual's message system for inter-widget communication
- **Async Operations**: Leverages Python's async/await for responsive UI

### Development Notes

- The project requires Python 3.13+ and uses modern Python features
- All widgets follow Textual's composition pattern with `compose()` methods
- The application uses reactive properties for state management
- Custom CSS classes are used for styling individual components