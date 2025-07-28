"""Stream handler for processing agent streaming responses."""

from typing import Protocol

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

from vibecore.widgets.messages import (
    AgentMessage,
    BaseMessage,
    MessageStatus,
)
from vibecore.widgets.tool_message_factory import create_tool_message
from vibecore.widgets.tool_messages import BaseToolMessage, ReadToolMessage


class MessageHandler(Protocol):
    """Protocol defining the interface for message handling."""

    async def handle_agent_message(self, message: BaseMessage) -> None:
        """Add a message to the widget's message list."""
        ...

    async def handle_agent_update(self, new_agent: Agent) -> None:
        """Handle agent updates."""
        ...

    async def handle_agent_error(self, error: Exception) -> None:
        """Handle errors during streaming."""
        ...

    async def handle_agent_finished(self) -> None:
        """Handle when the agent has finished processing."""
        ...


class AgentStreamHandler:
    """Handles streaming responses from agents."""

    def __init__(self, message_handler: MessageHandler) -> None:
        """Initialize the stream handler.

        Args:
            app: The VibecoreApp instance
        """
        self.message_handler = message_handler
        self.message_content = ""
        self.agent_message: AgentMessage | None = None
        self.tool_messages: dict[str, BaseToolMessage] = {}

    async def handle_text_delta(self, delta: str) -> None:
        """Handle incremental text updates from the agent.

        Args:
            delta: The text delta to append
        """
        self.message_content += delta
        if not self.agent_message:
            self.agent_message = AgentMessage(self.message_content, status=MessageStatus.EXECUTING)
            await self.message_handler.handle_agent_message(self.agent_message)
        else:
            self.agent_message.update(self.message_content)

    async def handle_tool_call(self, tool_name: str, arguments: str, call_id: str) -> None:
        """Create and display tool message when tool is invoked.

        Args:
            tool_name: Name of the tool being called
            arguments: JSON string of tool arguments
            call_id: Unique identifier for this tool call
        """
        # Use factory to create the appropriate tool message
        tool_message = create_tool_message(tool_name, arguments)

        self.tool_messages[call_id] = tool_message
        await self.message_handler.handle_agent_message(tool_message)

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

    async def handle_event(self, event: RawResponsesStreamEvent | RunItemStreamEvent | AgentUpdatedStreamEvent) -> None:
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
                await self.message_handler.handle_agent_update(new_agent)

    async def process_stream(self, result: RunResultStreaming) -> None:
        """Process all streaming events from the agent.

        Args:
            result: The streaming result to process
        """
        try:
            async for event in result.stream_events():
                await self.handle_event(event)
        except Exception as e:
            await self.message_handler.handle_agent_error(e)
        finally:
            await self.message_handler.handle_agent_finished()
            # await self._cleanup()
