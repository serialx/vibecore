"""Test the /clear command functionality."""

import tempfile
from pathlib import Path

import pytest
from agents import Agent

from vibecore.context import VibecoreContext
from vibecore.main import VibecoreApp
from vibecore.session import JSONLSession
from vibecore.widgets.messages import SystemMessage


@pytest.mark.asyncio
async def test_clear_command_detection():
    """Test that /clear command is properly detected."""
    with tempfile.TemporaryDirectory() as temp_dir:
        context = VibecoreContext()
        agent = Agent(
            name="Test Agent",
            instructions="You are a test agent.",
            model="gpt-4o-mini",
        )

        app = VibecoreApp(
            context=context,
            agent=agent,
            session_id="test-session",
        )

        # Override the session to use temp directory
        app.session = JSONLSession(session_id="test-session", project_path=Path.cwd(), base_dir=Path(temp_dir))

        # Mock handle_clear_command to avoid UI operations
        clear_command_called = False

        async def mock_handle_clear():
            nonlocal clear_command_called
            clear_command_called = True

        app.handle_clear_command = mock_handle_clear

        # Create a UserMessage event with /clear command
        from vibecore.widgets.core import MyTextArea

        clear_event = MyTextArea.UserMessage("/clear")

        # Process the event
        await app.on_my_text_area_user_message(clear_event)

        # Verify that the clear command handler was called
        assert clear_command_called


@pytest.mark.asyncio
async def test_clear_command_with_whitespace():
    """Test that /clear command works with whitespace."""
    with tempfile.TemporaryDirectory() as temp_dir:
        context = VibecoreContext()
        agent = Agent(
            name="Test Agent",
            instructions="You are a test agent.",
            model="gpt-4o-mini",
        )

        app = VibecoreApp(
            context=context,
            agent=agent,
            session_id="test-session",
        )

        # Override the session to use temp directory
        app.session = JSONLSession(session_id="test-session", project_path=Path.cwd(), base_dir=Path(temp_dir))

        # Mock handle_clear_command to avoid UI operations
        clear_command_called = False

        async def mock_handle_clear():
            nonlocal clear_command_called
            clear_command_called = True

        app.handle_clear_command = mock_handle_clear

        # Test with leading/trailing whitespace
        from vibecore.widgets.core import MyTextArea

        clear_event = MyTextArea.UserMessage("  /clear  ")

        await app.on_my_text_area_user_message(clear_event)

        # Verify that the clear command handler was called
        assert clear_command_called


@pytest.mark.asyncio
async def test_normal_message_not_affected():
    """Test that normal messages are not affected by clear command detection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        context = VibecoreContext()
        agent = Agent(
            name="Test Agent",
            instructions="You are a test agent.",
            model="gpt-4o-mini",
        )

        app = VibecoreApp(
            context=context,
            agent=agent,
            session_id="test-session",
        )

        # Override the session to use temp directory
        app.session = JSONLSession(session_id="test-session", project_path=Path.cwd(), base_dir=Path(temp_dir))

        original_session_id = app.session.session_id

        # Mock add_message to track if it gets called
        add_message_called = False

        async def mock_add_message(message):
            nonlocal add_message_called
            add_message_called = True

        app.add_message = mock_add_message

        # Mock watch_agent_status to avoid UI dependencies
        app.watch_agent_status = lambda _old_status, new_status: None

        # Send a normal message
        from vibecore.widgets.core import MyTextArea

        normal_event = MyTextArea.UserMessage("This is a normal message")

        await app.on_my_text_area_user_message(normal_event)

        # Verify session ID didn't change
        assert app.session.session_id == original_session_id

        # Verify add_message was called (normal message processing)
        assert add_message_called


@pytest.mark.asyncio
async def test_session_reset_logic():
    """Test the core session reset logic without UI dependencies."""
    with tempfile.TemporaryDirectory() as temp_dir:
        context = VibecoreContext()

        # Set up initial state
        context.todo_manager.write([{"id": "test-1", "content": "Test todo", "status": "pending", "priority": "high"}])

        session = JSONLSession(session_id="test-session", project_path=Path.cwd(), base_dir=Path(temp_dir))

        original_session_id = session.session_id

        # Test the context reset logic
        context.reset_state()

        # Verify context state was reset
        assert len(context.todo_manager.todos) == 0
        assert context.python_manager is not None  # Should be a new instance

        # Test session recreation
        new_session = JSONLSession(session_id="new-test-session", project_path=Path.cwd(), base_dir=Path(temp_dir))

        assert new_session.session_id != original_session_id


@pytest.mark.asyncio
async def test_system_message_creation():
    """Test that SystemMessage can be created and has correct properties."""
    message = SystemMessage("Test system message")

    assert message.text == "Test system message"
    assert message.get_header_params() == ("!", "Test system message", False)
    assert "system-message" in message.classes
