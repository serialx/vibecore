"""Test loading message history from session."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibecore.context import VibecoreContext
from vibecore.main import VibecoreApp
from vibecore.widgets.messages import MessageStatus, ToolMessage, UserMessage


@pytest.mark.asyncio
async def test_load_session_history_empty():
    """Test loading history from an empty session."""
    # Mock session with no items
    mock_session = AsyncMock()
    mock_session.get_items.return_value = []

    # Create app instance
    ctx = VibecoreContext()
    mock_agent = MagicMock()

    with patch("vibecore.main.JSONLSession") as mock_jsonl_class:
        mock_jsonl_class.return_value = mock_session
        app = VibecoreApp(ctx, mock_agent, session_id="test-session")
        app._session_id_provided = True

        # Mock the query methods
        app.query_one = MagicMock()
        mock_messages = MagicMock()
        mock_messages.query.return_value = []  # No Welcome widget
        app.query_one.return_value = mock_messages

        # Mock add_message
        app.add_message = AsyncMock()

        # Load history
        await app.load_session_history()

        # Verify session was queried
        mock_session.get_items.assert_called_once()
        # No messages should be added
        app.add_message.assert_not_called()


@pytest.mark.asyncio
async def test_load_session_history_with_messages():
    """Test loading history with various message types."""
    # Mock session with items
    session_items = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"type": "function_call", "call_id": "call_123", "name": "Bash", "arguments": '{"command": "ls"}'},
        {"type": "function_call_output", "call_id": "call_123", "output": "file1.txt\nfile2.txt"},
        {"role": "user", "content": "Thanks"},
    ]

    mock_session = AsyncMock()
    mock_session.get_items.return_value = session_items

    # Create app instance
    ctx = VibecoreContext()
    mock_agent = MagicMock()

    with patch("vibecore.main.JSONLSession") as mock_jsonl_class:
        mock_jsonl_class.return_value = mock_session
        app = VibecoreApp(ctx, mock_agent, session_id="test-session")
        app._session_id_provided = True

        # Mock the query methods
        app.query_one = MagicMock()
        mock_messages = MagicMock()
        mock_welcome_query = MagicMock()
        mock_welcome_query.first.return_value = MagicMock()  # Mock Welcome widget
        mock_messages.query.return_value = mock_welcome_query
        app.query_one.return_value = mock_messages

        # Track added messages
        added_messages = []
        app.add_message = AsyncMock(side_effect=lambda msg: added_messages.append(msg))

        # Load history
        await app.load_session_history()

        # Verify messages were added (assistant message is skipped as it's not a valid output item)
        assert len(added_messages) == 3  # 2 user, 1 tool (assistant skipped)

        # Check message types and content
        assert isinstance(added_messages[0], UserMessage)
        assert added_messages[0].text == "Hello"

        assert isinstance(added_messages[1], ToolMessage)
        assert added_messages[1].tool_name == "Bash"
        assert added_messages[1].command == '{"command": "ls"}'
        assert added_messages[1].output == "file1.txt\nfile2.txt"
        assert added_messages[1].status == MessageStatus.SUCCESS

        assert isinstance(added_messages[2], UserMessage)
        assert added_messages[2].text == "Thanks"


@pytest.mark.asyncio
async def test_load_session_history_with_complex_content():
    """Test loading history with complex content types."""
    # Mock session with complex content
    session_items = [
        {"role": "user", "content": ["text", {"type": "image", "url": "image.png"}]},  # Complex content
        {"role": "assistant", "content": {"text": "Response"}},  # Dict content
    ]

    mock_session = AsyncMock()
    mock_session.get_items.return_value = session_items

    # Create app instance
    ctx = VibecoreContext()
    mock_agent = MagicMock()

    with patch("vibecore.main.JSONLSession") as mock_jsonl_class:
        mock_jsonl_class.return_value = mock_session
        app = VibecoreApp(ctx, mock_agent, session_id="test-session")
        app._session_id_provided = True

        # Mock the query methods
        app.query_one = MagicMock()
        mock_messages = MagicMock()
        mock_messages.query.return_value = []  # No Welcome widget
        app.query_one.return_value = mock_messages

        # Track added messages
        added_messages = []
        app.add_message = AsyncMock(side_effect=lambda msg: added_messages.append(msg))

        # Load history
        await app.load_session_history()

        # Verify complex content was converted to strings
        # Note: assistant message with dict content is skipped since content is not a string
        assert len(added_messages) == 1
        assert isinstance(added_messages[0], UserMessage)
        assert isinstance(added_messages[0].text, str)
        # The user message content was a list, so it should be converted to string
        assert "text" in added_messages[0].text  # The list was stringified


@pytest.mark.asyncio
async def test_load_session_history_with_orphaned_tool_calls():
    """Test loading history with tool calls that have no output."""
    # Mock session with orphaned tool call
    session_items = [
        {"type": "function_call", "call_id": "call_456", "name": "Read", "arguments": '{"file_path": "/test.txt"}'},
        # No corresponding function_call_output
    ]

    mock_session = AsyncMock()
    mock_session.get_items.return_value = session_items

    # Create app instance
    ctx = VibecoreContext()
    mock_agent = MagicMock()

    with patch("vibecore.main.JSONLSession") as mock_jsonl_class:
        mock_jsonl_class.return_value = mock_session
        app = VibecoreApp(ctx, mock_agent, session_id="test-session")
        app._session_id_provided = True

        # Mock the query methods
        app.query_one = MagicMock()
        mock_messages = MagicMock()
        mock_messages.query.return_value = []  # No Welcome widget
        app.query_one.return_value = mock_messages

        # Track added messages
        added_messages = []
        app.add_message = AsyncMock(side_effect=lambda msg: added_messages.append(msg))

        # Load history should raise RuntimeError for orphaned tool calls
        with pytest.raises(RuntimeError, match="Pending tool calls without outputs found"):
            await app.load_session_history()
