"""Stream handler for processing agent streaming responses."""

import json
from typing import TYPE_CHECKING

from agents import (
    Agent,
    AgentUpdatedStreamEvent,
    MessageOutputItem,
    RawResponsesStreamEvent,
    RunItemStreamEvent,
    RunResultStreaming,
    ToolCallItem,
    ToolCallOutputItem,
)
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputItemDoneEvent,
    ResponseTextDeltaEvent,
)
from textual import log

from vibecore.widgets.messages import (
    AgentMessage,
    BaseMessage,
    MessageStatus,
    PythonToolMessage,
    ReadToolMessage,
    TodoWriteToolMessage,
    ToolMessage,
)

if TYPE_CHECKING:
    from vibecore.main import VibecoreApp


class StreamHandler:
    """Handles streaming responses from agents."""

    def __init__(self, app: "VibecoreApp") -> None:
        """Initialize the stream handler.

        Args:
            app: The VibecoreApp instance
        """
        self.app = app
        self.message_content = ""
        self.agent_message: AgentMessage | None = None
        self.tool_messages: dict[str, ToolMessage | PythonToolMessage | TodoWriteToolMessage | ReadToolMessage] = {}

    async def handle_text_delta(self, delta: str) -> None:
        """Handle incremental text updates from the agent.

        Args:
            delta: The text delta to append
        """
        self.message_content += delta
        if not self.agent_message:
            self.agent_message = AgentMessage(self.message_content, status=MessageStatus.EXECUTING)
            await self.app.add_message(self.agent_message)
        else:
            self.agent_message.update(self.message_content)

    async def handle_tool_call(self, tool_name: str, arguments: str, call_id: str) -> None:
        """Create and display tool message when tool is invoked.

        Args:
            tool_name: Name of the tool being called
            arguments: JSON string of tool arguments
            call_id: Unique identifier for this tool call
        """
        if tool_name == "execute_python":
            # Parse the arguments to extract the Python code
            try:
                args_dict = json.loads(arguments)
                code = args_dict.get("code", "")
                tool_message = PythonToolMessage(code=code)
            except (json.JSONDecodeError, KeyError):
                # Fallback to regular ToolMessage if parsing fails
                tool_message = ToolMessage(tool_name, command=arguments)
        elif tool_name == "todo_write":
            # Parse the arguments to extract the todos
            try:
                args_dict = json.loads(arguments)
                todos = args_dict.get("todos", [])
                tool_message = TodoWriteToolMessage(todos=todos)
            except (json.JSONDecodeError, KeyError):
                # Fallback to regular ToolMessage if parsing fails
                tool_message = ToolMessage(tool_name, command=arguments)
        elif tool_name == "read":
            # Parse the arguments to extract the file path
            try:
                args_dict = json.loads(arguments)
                file_path = args_dict.get("file_path", "")
                tool_message = ReadToolMessage(file_path=file_path)
            except (json.JSONDecodeError, KeyError):
                # Fallback to regular ToolMessage if parsing fails
                tool_message = ToolMessage(tool_name, command=arguments)
        else:
            tool_message = ToolMessage(tool_name, command=arguments)

        self.tool_messages[call_id] = tool_message
        await self.app.add_message(tool_message)

    async def handle_tool_output(self, output: str, call_id: str) -> None:
        """Update tool message with execution results.

        Args:
            output: The tool execution output
            call_id: The tool call identifier to match with pending calls
        """
        if call_id in self.tool_messages:
            tool_message = self.tool_messages[call_id]
            if isinstance(tool_message, ReadToolMessage):
                # For ReadToolMessage, pass the content as the second argument
                tool_message.update(MessageStatus.SUCCESS, str(output))
            else:
                tool_message.update(MessageStatus.SUCCESS, str(output))

    async def handle_message_complete(self) -> None:
        """Finalize agent message when complete."""
        if self.agent_message:
            self.agent_message.update(self.message_content, status=MessageStatus.IDLE)
            self.agent_message = None
            self.message_content = ""

    async def handle_agent_update(self, new_agent: Agent) -> None:
        """Handle agent handoff events.

        Args:
            new_agent: The new agent after handoff
        """
        log(f"Agent updated: {new_agent.name}")
        self.app.agent = new_agent

    async def _handle_event(
        self, event: RawResponsesStreamEvent | RunItemStreamEvent | AgentUpdatedStreamEvent
    ) -> None:
        """Handle a single streaming event.

        Args:
            event: The streaming event to process
        """
        match event:
            case RawResponsesStreamEvent(data=data):
                match data:
                    case ResponseTextDeltaEvent(delta=delta) if delta:
                        await self.handle_text_delta(delta)

                    case ResponseOutputItemDoneEvent(
                        item=ResponseFunctionToolCall(name=tool_name, arguments=arguments, call_id=call_id)
                    ):
                        await self.handle_tool_call(tool_name, arguments, call_id)

            case RunItemStreamEvent(item=item):
                match item:
                    case ToolCallItem():
                        pass
                    case ToolCallOutputItem(output=output, raw_item=raw_item):
                        # Find the corresponding tool message by call_id
                        if (
                            isinstance(raw_item, dict)
                            and "call_id" in raw_item
                            and raw_item["call_id"] in self.tool_messages
                        ):
                            await self.handle_tool_output(output, raw_item["call_id"])
                    case MessageOutputItem():
                        await self.handle_message_complete()

            case AgentUpdatedStreamEvent(new_agent=new_agent):
                await self.handle_agent_update(new_agent)

    async def _handle_error(self, error: Exception) -> None:
        """Handle errors during streaming.

        Args:
            error: The exception that occurred
        """
        # Log the error
        log(f"Error during agent response: {type(error).__name__}: {error!s}")

        # Create an error message for the user
        error_msg = f"❌ Error: {type(error).__name__}"
        if str(error):
            error_msg += f"\n\n{error!s}"

        # Display the error to the user
        error_agent_msg = AgentMessage(error_msg, status=MessageStatus.ERROR)
        await self.app.add_message(error_agent_msg)

    async def _cleanup(self) -> None:
        """Clean up after streaming completes or errors."""
        # Remove the last agent message if it is still executing (which means the agent run was cancelled)
        messages = self.app.query_one("#messages")
        try:
            last_message = messages.query_one("BaseMessage:last-child", BaseMessage)
            if last_message.status == MessageStatus.EXECUTING:
                last_message.remove()
        except Exception:
            # No messages to clean up
            pass

    async def process_stream(self, result: RunResultStreaming) -> None:
        """Process all streaming events from the agent.

        Args:
            result: The streaming result to process
        """
        try:
            async for event in result.stream_events():
                await self._handle_event(event)
        except Exception as e:
            await self._handle_error(e)
        finally:
            await self._cleanup()
