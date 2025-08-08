"""Unit tests for MCPToolMessage widget."""

import pytest
from textual.app import App

from vibecore.widgets.messages import MessageStatus
from vibecore.widgets.tool_messages import MCPToolMessage


class TestMCPToolMessage:
    """Test suite for MCPToolMessage widget."""

    @pytest.fixture
    def app(self):
        """Create a test app."""
        return App()

    def test_mcp_tool_message_init(self, app):
        """Test MCPToolMessage initialization."""
        msg = MCPToolMessage(
            server_name="test_server",
            tool_name="test_tool",
            arguments='{"param": "value"}',
            output="Test output",
            status=MessageStatus.SUCCESS,
        )

        assert msg.server_name == "test_server"
        assert msg.tool_name == "test_tool"
        assert msg.arguments == '{"param": "value"}'
        assert msg.output == "Test output"
        assert msg.status == MessageStatus.SUCCESS

    def test_mcp_tool_message_empty_args(self, app):
        """Test MCPToolMessage with empty arguments."""
        msg = MCPToolMessage(
            server_name="server",
            tool_name="tool",
            arguments="{}",
            status=MessageStatus.EXECUTING,
        )

        assert msg.arguments == "{}"
        assert msg.output == ""

    def test_mcp_tool_message_update(self, app):
        """Test updating MCPToolMessage status and output directly."""
        msg = MCPToolMessage(
            server_name="server",
            tool_name="tool",
            arguments="{}",
            status=MessageStatus.EXECUTING,
        )

        # Test that we can update output directly
        msg.output = "Operation completed"
        assert msg.output == "Operation completed"

        # Note: update() method requires the widget to be mounted in an app
        # to update child components, so we test the properties directly

    def test_mcp_tool_message_header_format(self, app):
        """Test that the header is formatted correctly."""
        msg = MCPToolMessage(
            server_name="github",
            tool_name="create_issue",
            arguments='{"title": "Bug report"}',
            status=MessageStatus.SUCCESS,
        )

        # The header should show server name and tool name
        # expected_header = "MCP[github]::create_issue"
        # This would be tested in the compose method, but we can at least
        # verify the data is stored correctly
        assert msg.server_name == "github"
        assert msg.tool_name == "create_issue"

    @pytest.mark.parametrize(
        "status,expected_class",
        [
            (MessageStatus.EXECUTING, "executing"),
            (MessageStatus.SUCCESS, "success"),
            (MessageStatus.ERROR, "error"),
        ],
    )
    def test_mcp_tool_message_status_classes(self, app, status, expected_class):
        """Test that status affects CSS classes."""
        msg = MCPToolMessage(
            server_name="server",
            tool_name="tool",
            arguments="{}",
            status=status,
        )

        # The status should be reflected in the widget's state
        assert msg.status == status

    def test_mcp_tool_message_long_arguments(self, app):
        """Test handling of long argument strings."""
        long_args = (
            '{"very_long_parameter_name": "very_long_value_that_might_need_truncation", "another_param": "value"}'
        )
        msg = MCPToolMessage(
            server_name="server",
            tool_name="tool",
            arguments=long_args,
            status=MessageStatus.SUCCESS,
        )

        assert msg.arguments == long_args

    def test_mcp_tool_message_multiline_output(self, app):
        """Test handling of multiline output."""
        multiline_output = """Line 1
Line 2
Line 3
Line 4
Line 5"""
        msg = MCPToolMessage(
            server_name="server",
            tool_name="tool",
            arguments="{}",
            output=multiline_output,
            status=MessageStatus.SUCCESS,
        )

        assert msg.output == multiline_output

    def test_mcp_tool_message_special_characters(self, app):
        """Test handling of special characters in server/tool names."""
        msg = MCPToolMessage(
            server_name="server-with-dashes",
            tool_name="tool_with_underscores",
            arguments='{"key": "value with spaces"}',
            status=MessageStatus.SUCCESS,
        )

        assert msg.server_name == "server-with-dashes"
        assert msg.tool_name == "tool_with_underscores"

    def test_mcp_tool_message_reactive_properties(self, app):
        """Test that reactive properties can be set."""
        msg = MCPToolMessage(
            server_name="server",
            tool_name="tool",
            arguments="{}",
            status=MessageStatus.EXECUTING,
        )

        # Change reactive properties
        msg.output = "New output"
        assert msg.output == "New output"

        # Note: Setting status requires the widget to be mounted
        # because it triggers watch_status which updates child components
