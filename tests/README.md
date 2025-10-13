# Test Organization

This document describes the organization of the test suite for vibecore. The tests are organized into logical groups by functionality to make them easier to find, maintain, and run selectively.

## Directory Structure

```
tests/
├── ui/                           # UI and Widget tests
├── tools/                        # Tool-specific tests
├── session/                      # Session and storage tests
├── cli/                          # CLI and command tests
├── models/                       # Model integration tests
├── fixtures/                     # Test fixtures
├── __snapshots__/               # Snapshot files
└── _harness/                    # Test utilities/infrastructure
```

## Test Categories

### UI Tests (`tests/ui/`)
Tests for the terminal user interface components:
- **test_widget_snapshots.py** - Full application widget rendering tests
- **test_message_snapshots.py** - Individual message widget tests
- **test_keyboard_interactions.py** - Keyboard interaction and key bindings
- **test_tool_message_factory.py** - Tool message widget factory

### Tool Tests (`tests/tools/`)
Tests for the various tools available to the AI agent:
- **test_file_tools.py** - File manipulation tools (read, write, edit, multi_edit)
- **test_shell_tools.py** - Shell command tools (bash, grep, glob, ls)
- **test_python_execution.py** - Python code execution tool
- **test_python_tool_integration.py** - Python tool integration with agents
- **test_todo_tools.py** - Todo/task management tools

### Session Tests (`tests/session/`)
Tests for session management and persistence:
- **test_jsonl_session.py** - JSONL session storage functionality
- **test_jsonl_format.py** - JSONL format parsing
- **test_session_history_loading.py** - Loading message history from sessions

### CLI Tests (`tests/cli/`)
Tests for command-line interface:
- **test_cli.py** - CLI commands and arguments

### Model Tests (`tests/models/`)
Tests for AI model integrations:
- **test_anthropic_model.py** - Anthropic model integration

### Test Utilities (`tests/_harness/`)
Shared test infrastructure:
- **test_harness.py** - Test harness for full app testing
- **message_test_harness.py** - Lightweight harness for message widget testing

## Running Tests

### Run all tests
```bash
uv run pytest
```

### Run tests by category
```bash
# UI tests only
uv run pytest tests/ui/

# Tool tests only
uv run pytest tests/tools/

# Session tests only
uv run pytest tests/session/
```

### Run specific test types
```bash
# Run all snapshot tests
uv run pytest -k snapshot

# Run tests verbosely
uv run pytest -v
```

### Update snapshots
```bash
uv run pytest tests/ui/test_widget_snapshots.py --snapshot-update
uv run pytest tests/ui/test_message_snapshots.py --snapshot-update
```

## Test Development Guidelines

1. **Adding UI Tests**: Place in `tests/ui/` and consider if snapshot testing is appropriate
2. **Adding Tool Tests**: Place in `tests/tools/` and ensure proper mocking of external dependencies
3. **Adding Session Tests**: Place in `tests/session/` and use temporary directories for file operations
4. **Test Fixtures**: Shared fixtures should be in `conftest.py` or test-specific fixture files
5. **Snapshot Tests**: Always review snapshot diffs before committing

## Coverage

Run tests with coverage:
```bash
uv run pytest --cov=vibecore --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

## Message Widget Testing

See `tests/README_message_tests.md` for detailed information about testing message widgets.