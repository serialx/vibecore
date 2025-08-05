# Message Widget Snapshot Tests

This document explains the message-specific snapshot testing framework for vibecore.

## Overview

The message test harness provides a lightweight way to test individual message widgets without the complexity of the full VibecoreApp. This is useful for:

- Testing specific message widget behaviors
- Verifying visual rendering of different message types
- Testing edge cases and special content
- Rapid iteration on widget styling

## Components

### `message_test_harness.py`

Provides a simple `MessageTestApp` base class and several pre-configured test apps:

- `UserMessageTestApp` - Tests user message rendering
- `AgentMessageTestApp` - Tests agent messages in different states
- `ToolMessageTestApp` - Tests various tool message widgets
- `MixedMessageTestApp` - Tests realistic conversation flows

### `test_message_snapshots.py`

Contains the actual snapshot tests organized into two classes:

- `TestMessageSnapshots` - Core message widget tests
- `TestMessageEdgeCases` - Edge cases and special scenarios

## Running the Tests

```bash
# Run all message snapshot tests
uv run pytest tests/test_message_snapshots.py

# Run a specific test
uv run pytest tests/test_message_snapshots.py::TestMessageSnapshots::test_user_messages

# Update snapshots after intentional changes
uv run pytest tests/test_message_snapshots.py --snapshot-update

# Run with verbose output
uv run pytest tests/test_message_snapshots.py -v
```

## Adding New Tests

To add a new message test:

1. Create a new test app class in `message_test_harness.py`:
```python
class MyCustomTestApp(MessageTestApp):
    def create_test_messages(self):
        from vibecore.widgets.messages import UserMessage
        yield UserMessage("Test content")
```

2. Add a test method in `test_message_snapshots.py`:
```python
def test_my_custom_messages(self, snap_compare):
    """Test my custom scenario."""
    app = MyCustomTestApp()
    assert snap_compare(app, press=[])
```

3. Run with `--snapshot-update` to create the initial snapshot
4. Review the generated SVG to ensure correctness

## Test Coverage

The test suite covers:

- All message types (User, Agent, Tool messages)
- Different message states (idle, executing, success, error)
- Markdown rendering
- Expandable content
- Special characters and edge cases
- Long lines and text wrapping
- Empty messages
- Error states

## Benefits

- **Fast**: Tests run quickly without full app initialization
- **Focused**: Test individual widgets in isolation
- **Visual**: Snapshots show exactly how widgets render
- **Maintainable**: Easy to add new test cases