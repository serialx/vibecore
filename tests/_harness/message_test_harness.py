"""Simple test harness for message widget snapshot testing."""

from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll

from vibecore.widgets.messages import AgentMessage, MessageStatus, UserMessage
from vibecore.widgets.tool_messages import (
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
