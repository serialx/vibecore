"""Simple test harness for message widget snapshot testing."""

import json
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll

from vibecore.widgets.messages import AgentMessage, MessageStatus, ReasoningMessage, UserMessage
from vibecore.widgets.tool_messages import (
    MCPToolMessage,
    PythonToolMessage,
    ReadToolMessage,
    TaskToolMessage,
    TodoWriteToolMessage,
    ToolMessage,
    WriteToolMessage,
)

# Get the vibecore source directory for CSS paths
VIBECORE_SRC = Path(__file__).parent.parent.parent / "src" / "vibecore"


class MessageTestApp(App):
    """A simple test app for testing individual message widgets.

    This app provides a minimal container for testing message widgets
    in isolation, without the complexity of the full VibecoreApp.
    """

    # Include the necessary CSS files for message rendering
    CSS_PATH: ClassVar = [
        str(VIBECORE_SRC / "widgets" / "core.tcss"),
        str(VIBECORE_SRC / "widgets" / "messages.tcss"),
        str(VIBECORE_SRC / "widgets" / "tool_messages.tcss"),
        str(VIBECORE_SRC / "widgets" / "expandable.tcss"),
        str(VIBECORE_SRC / "widgets" / "info.tcss"),
    ]

    def compose(self) -> ComposeResult:
        """Create the app layout with a scrollable container."""
        with VerticalScroll(id="message-container"):
            yield from self.create_test_messages()

    def create_test_messages(self) -> ComposeResult:
        """Override this method to yield test messages."""
        # Default implementation yields nothing
        # Subclasses should override to add specific messages
        yield from []


class UserMessageTestApp(MessageTestApp):
    """Test app for UserMessage widgets."""

    def create_test_messages(self) -> ComposeResult:
        """Create various UserMessage test cases."""
        # Simple text message
        yield UserMessage("Hello, world!")

        # Message with markdown
        yield UserMessage("# Heading\n\n**Bold** and *italic* text")

        # Long message
        yield UserMessage("This is a very long message that should wrap properly. " * 10)

        # Message with code
        yield UserMessage("Here's some `inline code` and a block:\n\n```python\ndef hello():\n    print('Hello')\n```")


class AgentMessageTestApp(MessageTestApp):
    """Test app for AgentMessage widgets."""

    def create_test_messages(self) -> ComposeResult:
        """Create various AgentMessage test cases."""
        # Simple response
        yield AgentMessage("I can help you with that.", status=MessageStatus.SUCCESS)

        # In-progress message
        yield AgentMessage("Thinking...", status=MessageStatus.EXECUTING)

        # Error message
        yield AgentMessage("An error occurred", status=MessageStatus.ERROR)

        # Long response with markdown
        yield AgentMessage(
            "## Analysis\n\n"
            "Here are the key findings:\n\n"
            "1. **First point**: Important detail\n"
            "2. **Second point**: Another detail\n\n"
            "```python\n# Example code\nresult = process_data()\n```",
            status=MessageStatus.SUCCESS,
        )


class ToolMessageTestApp(MessageTestApp):
    """Test app for various tool message widgets."""

    def create_test_messages(self) -> ComposeResult:
        """Create various tool message test cases."""
        # Generic tool message
        yield ToolMessage(
            tool_name="custom_tool",
            command='custom_tool(param="value")',
            output="Tool executed successfully",
            status=MessageStatus.SUCCESS,
        )

        # Python tool message - executing
        yield PythonToolMessage(code="print('Hello from Python')", output="", status=MessageStatus.EXECUTING)

        # Python tool message - with output
        yield PythonToolMessage(
            code="import math\nprint(math.pi)", output="3.141592653589793", status=MessageStatus.SUCCESS
        )

        # Python tool message - with error
        yield PythonToolMessage(code="1 / 0", output="ZeroDivisionError: division by zero", status=MessageStatus.ERROR)

        # Read tool message
        yield ReadToolMessage(
            file_path="/path/to/file.py",
            output="def main():\n    print('File content')\n\nif __name__ == '__main__':\n    main()",
            status=MessageStatus.SUCCESS,
        )

        # Write tool message
        yield WriteToolMessage(
            file_path="/path/to/output.txt",
            content="This content was written to the file",
            output="File written successfully",
            status=MessageStatus.SUCCESS,
        )

        # Todo tool message
        yield TodoWriteToolMessage(
            todos=[
                {"id": "1", "content": "Complete feature implementation", "status": "completed", "priority": "high"},
                {"id": "2", "content": "Write tests", "status": "in_progress", "priority": "medium"},
                {"id": "3", "content": "Update documentation", "status": "pending", "priority": "low"},
            ],
            output="",
            status=MessageStatus.SUCCESS,
        )

        # Task tool message
        yield TaskToolMessage(
            description="Analyze codebase",
            prompt="Review the code structure and identify improvements",
            output="Analysis complete. Found 3 areas for improvement...",
            status=MessageStatus.SUCCESS,
        )


class MixedMessageTestApp(MessageTestApp):
    """Test app showing a conversation with mixed message types."""

    def create_test_messages(self) -> ComposeResult:
        """Create a realistic conversation flow."""
        yield UserMessage("Can you help me read a file and analyze it?")

        yield AgentMessage("I'll help you read and analyze the file.", status=MessageStatus.SUCCESS)

        yield ReadToolMessage(
            file_path="/project/data.py",
            output="""import pandas as pd

def process_data(filename):
    df = pd.read_csv(filename)
    return df.describe()

# Main execution
if __name__ == '__main__':
    results = process_data('input.csv')
    print(results)""",
            status=MessageStatus.SUCCESS,
        )

        yield AgentMessage("I've read the file. Let me analyze it by running the code:", status=MessageStatus.SUCCESS)

        yield PythonToolMessage(
            code=(
                "# Simulating the analysis\n"
                "import pandas as pd\n"
                "print('Analysis results:')\n"
                "print('- Uses pandas for data processing')\n"
                "print('- Has a main function')"
            ),
            output="Analysis results:\n- Uses pandas for data processing\n- Has a main function",
            status=MessageStatus.SUCCESS,
        )

        yield AgentMessage(
            "## Analysis Complete\n\n"
            "The file contains:\n"
            "- A data processing function using pandas\n"
            "- Proper main guard for script execution\n"
            "- Clean structure for CSV file processing",
            status=MessageStatus.SUCCESS,
        )


class ReasoningMessageTestApp(MessageTestApp):
    """Test app for ReasoningMessage widgets."""

    def create_test_messages(self) -> ComposeResult:
        """Create various ReasoningMessage test cases."""
        # Simple reasoning summary
        yield ReasoningMessage(
            "Let me think about the best approach to implement this feature.", status=MessageStatus.IDLE
        )

        # More detailed reasoning
        yield ReasoningMessage(
            "**Analysis**\n\n"
            "I need to consider several factors:\n\n"
            "1. **Performance**: The algorithm should be efficient\n"
            "2. **Maintainability**: Code should be readable\n"
            "3. **Scalability**: Solution should handle large datasets\n\n"
            "Based on these requirements, I'll use a hash-based approach.",
            status=MessageStatus.IDLE,
        )

        # Short reasoning
        yield ReasoningMessage("Processing the user's request step by step.", status=MessageStatus.IDLE)

        # Reasoning with code mentions
        yield ReasoningMessage(
            "I should create a `ReasoningMessage` widget that extends `BaseMessage` "
            "and displays reasoning summaries with a star icon (*) to distinguish "
            "it from regular agent messages.",
            status=MessageStatus.EXECUTING,
        )


class MCPToolMessageTestApp(MessageTestApp):
    """Test app for MCPToolMessage widgets."""

    def create_test_messages(self) -> ComposeResult:
        """Create various MCPToolMessage test cases."""
        # Simple MCP tool call
        yield MCPToolMessage(
            server_name="filesystem",
            tool_name="read_file",
            arguments='{"path": "/etc/hosts"}',
            output=json.dumps({"type": "text", "text": "127.0.0.1 localhost"}),
            status=MessageStatus.SUCCESS,
        )

        # MCP tool with no arguments
        yield MCPToolMessage(
            server_name="github",
            tool_name="list_repositories",
            arguments="{}",
            output=json.dumps({"type": "text", "text": '["repo1", "repo2", "repo3"]'}),
            status=MessageStatus.SUCCESS,
        )

        # MCP tool executing
        yield MCPToolMessage(
            server_name="docker",
            tool_name="list_containers",
            arguments='{"all": true}',
            status=MessageStatus.EXECUTING,
        )

        # MCP tool with error
        yield MCPToolMessage(
            server_name="database",
            tool_name="execute_query",
            arguments='{"query": "SELECT * FROM users"}',
            output=json.dumps({"type": "text", "text": "Error: Connection refused"}),
            status=MessageStatus.ERROR,
        )

        # MCP tool with long arguments
        yield MCPToolMessage(
            server_name="api_server",
            tool_name="make_request",
            arguments=(
                '{"url": "https://api.example.com/v1/users/data", "method": "POST", '
                '"headers": {"Authorization": "Bearer token123", "Content-Type": "application/json"}, '
                '"body": {"user": "test", "action": "update"}}'
            ),
            output=json.dumps({"type": "text", "text": "Response: 200 OK"}),
            status=MessageStatus.SUCCESS,
        )

        # MCP tool with complex output
        yield MCPToolMessage(
            server_name="git",
            tool_name="get_diff",
            arguments='{"file": "main.py", "base": "main", "head": "feature"}',
            output=json.dumps(
                {
                    "type": "text",
                    "text": """--- a/main.py
+++ b/main.py
@@ -10,7 +10,10 @@
 def process():
-    print("Old implementation")
+    print("New implementation")
+    # Added feature
+    result = calculate()
+    return result

 def main():
     process()""",
                }
            ),
            status=MessageStatus.SUCCESS,
        )

        # MCP tool with JSON output (should be prettified)
        yield MCPToolMessage(
            server_name="api_server",
            tool_name="get_user_profile",
            arguments='{"user_id": "12345"}',
            output=json.dumps(
                {
                    "type": "text",
                    "text": (
                        '{"id": "12345", "name": "John Doe", "email": "john@example.com", '
                        '"roles": ["admin", "developer"], "created_at": "2024-01-15T10:30:00Z", '
                        '"settings": {"theme": "dark", "notifications": true}}'
                    ),
                }
            ),
            status=MessageStatus.SUCCESS,
        )

        # MCP tool with nested JSON output
        yield MCPToolMessage(
            server_name="database",
            tool_name="query_stats",
            arguments='{"table": "users"}',
            output=json.dumps(
                {
                    "type": "text",
                    "text": (
                        '{"table": "users", "stats": {"total_rows": 15234, "indexes": ["id", "email"], '
                        '"size_mb": 42.5}, "recent_operations": [{"type": "INSERT", "count": 123}, '
                        '{"type": "UPDATE", "count": 456}]}'
                    ),
                }
            ),
            status=MessageStatus.SUCCESS,
        )

        # MCP tool with JSON array output
        yield MCPToolMessage(
            server_name="filesystem",
            tool_name="list_directory",
            arguments='{"path": "/home/user/documents"}',
            output=json.dumps(
                {
                    "type": "text",
                    "text": (
                        '[{"name": "report.pdf", "size": 102400, "modified": "2024-01-20"}, '
                        '{"name": "notes.txt", "size": 2048, "modified": "2024-01-21"}, '
                        '{"name": "project", "type": "directory", "modified": "2024-01-19"}]'
                    ),
                }
            ),
            status=MessageStatus.SUCCESS,
        )
