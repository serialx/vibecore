"""Snapshot tests for individual message widgets."""

from tests._harness.message_test_harness import (
    AgentMessageTestApp,
    FeedbackWidgetTestApp,
    MCPToolMessageTestApp,
    MessageTestApp,
    MixedMessageTestApp,
    ReasoningMessageTestApp,
    ToolMessageTestApp,
    UserMessageTestApp,
)


class TestMessageSnapshots:
    """Test suite for message widget snapshots."""

    def test_user_messages(self, snap_compare):
        """Test rendering of various UserMessage widgets."""
        app = UserMessageTestApp()
        assert snap_compare(app, press=[])

    def test_agent_messages(self, snap_compare):
        """Test rendering of AgentMessage widgets in different states."""
        app = AgentMessageTestApp()
        assert snap_compare(app, press=[])

    def test_tool_messages(self, snap_compare):
        """Test rendering of various tool message widgets."""
        app = ToolMessageTestApp()
        assert snap_compare(app, press=[])

    def test_mcp_tool_messages(self, snap_compare):
        """Test rendering of MCP tool message widgets."""
        app = MCPToolMessageTestApp()
        assert snap_compare(app, press=[])

    def test_reasoning_messages(self, snap_compare):
        """Test rendering of ReasoningMessage widgets."""
        app = ReasoningMessageTestApp()
        assert snap_compare(app, press=[])

    def test_feedback_widgets(self, snap_compare):
        """Test rendering of FeedbackWidget widgets."""
        app = FeedbackWidgetTestApp()
        assert snap_compare(app, press=[])

    def test_mixed_conversation(self, snap_compare):
        """Test rendering of a realistic conversation with mixed message types."""
        app = MixedMessageTestApp()
        assert snap_compare(app, press=[])

    def test_message_status_transitions(self, snap_compare):
        """Test message status changes and their visual effects."""

        # Create a custom test app for status transitions
        class StatusTransitionTestApp(MessageTestApp):
            def create_test_messages(self):
                from vibecore.widgets.messages import MessageStatus
                from vibecore.widgets.tool_messages import PythonToolMessage

                # Show both executing and completed states
                yield PythonToolMessage(code="import time\ntime.sleep(1)", output="", status=MessageStatus.EXECUTING)
                yield PythonToolMessage(
                    code="import time\ntime.sleep(1)", output="Execution completed", status=MessageStatus.SUCCESS
                )

        app = StatusTransitionTestApp()
        assert snap_compare(app, press=[])

    def test_expandable_content(self, snap_compare):
        """Test expandable content widgets in messages."""

        # Create test app with long content
        class ExpandableTestApp(MessageTestApp):
            def create_test_messages(self):
                from vibecore.widgets.messages import MessageStatus
                from vibecore.widgets.tool_messages import ReadToolMessage

                # Create long content
                long_content = "\n".join([f"Line {i}: This is a test line" for i in range(50)])

                yield ReadToolMessage(file_path="/test/long_file.py", output=long_content, status=MessageStatus.SUCCESS)

        app = ExpandableTestApp()
        assert snap_compare(app, press=[])

    def test_markdown_rendering(self, snap_compare):
        """Test markdown rendering in messages."""

        # Create test app with markdown content
        class MarkdownTestApp(MessageTestApp):
            def create_test_messages(self):
                from vibecore.widgets.messages import AgentMessage, MessageStatus, UserMessage

                # User message with complex markdown
                yield UserMessage(
                    "# Test Request\n\n"
                    "Please analyze this **code**:\n\n"
                    "```python\ndef factorial(n):\n"
                    "    if n <= 1:\n"
                    "        return 1\n"
                    "    return n * factorial(n-1)\n```\n\n"
                    "- Item 1\n"
                    "- Item 2\n"
                    "  - Nested item\n\n"
                    "> This is a quote"
                )

                # Agent response with markdown
                yield AgentMessage(
                    "## Analysis Results\n\n"
                    "The code implements a **recursive factorial** function.\n\n"
                    "### Key Points:\n"
                    "1. Base case: `n <= 1` returns `1`\n"
                    "2. Recursive case: `n * factorial(n-1)`\n\n"
                    "| Complexity | Value |\n"
                    "|------------|-------|\n"
                    "| Time       | O(n)  |\n"
                    "| Space      | O(n)  |\n\n"
                    "Here's an iterative version:\n"
                    "```python\ndef factorial_iter(n):\n"
                    "    result = 1\n"
                    "    for i in range(2, n+1):\n"
                    "        result *= i\n"
                    "    return result\n```",
                    status=MessageStatus.SUCCESS,
                )

        app = MarkdownTestApp()
        assert snap_compare(app, press=[])

    def test_error_states(self, snap_compare):
        """Test error message rendering."""

        # Create test app with error messages
        class ErrorTestApp(MessageTestApp):
            def create_test_messages(self):
                from vibecore.widgets.messages import AgentMessage, MessageStatus
                from vibecore.widgets.tool_messages import (
                    BashToolMessage,
                    PythonToolMessage,
                    ReadToolMessage,
                    ToolMessage,
                )

                # Python execution error
                yield PythonToolMessage(
                    code="import nonexistent_module\nraise ValueError('Test error')",
                    output="Traceback (most recent call last):\n"
                    '  File "<stdin>", line 1, in <module>\n'
                    "ModuleNotFoundError: No module named 'nonexistent_module'",
                    status=MessageStatus.ERROR,
                )

                # Bash execution error
                yield BashToolMessage(
                    command="ls /nonexistent/directory",
                    output="ls: cannot access '/nonexistent/directory': No such file or directory\nExit code: 2",
                    status=MessageStatus.ERROR,
                )

                # Generic tool error
                yield ToolMessage(
                    tool_name="custom_tool",
                    command="custom_command",
                    output="Error: Command failed",
                    status=MessageStatus.ERROR,
                )

                # Read error
                yield ReadToolMessage(
                    file_path="/path/to/missing/file.txt", output="Error: File not found", status=MessageStatus.ERROR
                )

                # Agent error message
                yield AgentMessage(
                    "I encountered an error while processing your request. The operation could not be completed.",
                    status=MessageStatus.ERROR,
                )

        app = ErrorTestApp()
        assert snap_compare(app, press=[])


class TestMessageEdgeCases:
    """Test edge cases for message rendering."""

    def test_empty_messages(self, snap_compare):
        """Test messages with empty content."""

        class EmptyMessagesApp(MessageTestApp):
            def create_test_messages(self):
                from vibecore.widgets.messages import AgentMessage, MessageStatus, UserMessage
                from vibecore.widgets.tool_messages import ToolMessage

                # Empty user message
                yield UserMessage("")

                # Empty agent message
                yield AgentMessage("", status=MessageStatus.SUCCESS)

                # Tool with empty output
                yield ToolMessage(tool_name="test", command="test_command", output="", status=MessageStatus.SUCCESS)

        app = EmptyMessagesApp()
        assert snap_compare(app, press=[])

    def test_special_characters(self, snap_compare):
        """Test messages with special characters and markup."""

        class SpecialCharsApp(MessageTestApp):
            def create_test_messages(self):
                from vibecore.widgets.messages import AgentMessage, MessageStatus, UserMessage

                # Message with square brackets (potential markup)
                yield UserMessage("Array access: data[0], dict['key'], list[1:3]")

                # Message with various special characters
                yield AgentMessage(
                    "Special chars: <>&\"'\nEmoji: 🎉 🚀 ✨\nUnicode: αβγ δεζ\nMath: x² + y³ = z⁴",
                    status=MessageStatus.SUCCESS,
                )

        app = SpecialCharsApp()
        assert snap_compare(app, press=[])

    def test_long_lines(self, snap_compare):
        """Test messages with very long lines."""

        class LongLinesApp(MessageTestApp):
            def create_test_messages(self):
                from vibecore.widgets.messages import MessageStatus, UserMessage
                from vibecore.widgets.tool_messages import PythonToolMessage

                # Very long single line
                long_line = "This is a very long line that should wrap properly " * 20
                yield UserMessage(long_line)

                # Code with long lines
                yield PythonToolMessage(
                    code=(
                        "very_long_variable_name = "
                        '"This is a string with a very long value that might need '
                        'to wrap in the code display" * 3'
                    ),
                    output="Output from long line code",
                    status=MessageStatus.SUCCESS,
                )

        app = LongLinesApp()
        assert snap_compare(app, press=[])
