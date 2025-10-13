"""Stream handler for processing agent streaming responses."""

import json
from typing import Protocol

from agents import (
    MessageOutputItem,
    RawResponsesStreamEvent,
    RunItemStreamEvent,
    RunResultStreaming,
    StreamEvent,
    ToolCallItem,
    ToolCallOutputItem,
)
from openai.types.responses import (
    ResponseCompletedEvent,
    ResponseFunctionToolCall,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseReasoningItem,
    ResponseReasoningSummaryPartAddedEvent,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseReasoningSummaryTextDoneEvent,
    ResponseTextDeltaEvent,
)

from vibecore.widgets.messages import (
    AgentMessage,
    BaseMessage,
    MessageStatus,
    ReasoningMessage,
)
from vibecore.widgets.tool_message_factory import create_tool_message
from vibecore.widgets.tool_messages import BaseToolMessage, TaskToolMessage


class MessageHandler(Protocol):
    """Protocol defining the interface for message handling."""

    async def handle_agent_message(self, message: BaseMessage) -> None:
        """Add a message to the widget's message list."""
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
            message_handler: The MessageHandler protocol instance
        """
        self.message_handler = message_handler
        self.message_content = ""
        self.agent_message: AgentMessage | None = None
        self.tool_messages: dict[str, BaseToolMessage] = {}
        self.reasoning_messages: dict[str, ReasoningMessage] = {}

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
            tool_message.update(MessageStatus.SUCCESS, str(output))

    async def handle_message_complete(self) -> None:
        """Finalize agent message when complete."""
        if self.agent_message:
            self.agent_message.update(self.message_content, status=MessageStatus.IDLE)
            self.agent_message = None
            self.message_content = ""

    async def handle_event(self, event: StreamEvent) -> None:
        """Handle a single streaming event.

        Args:
            event: The streaming event to process
        """
        match event:
            case RawResponsesStreamEvent(data=data):
                # log(f"RawResponsesStreamEvent data: {data.type}")
                match data:
                    case ResponseOutputItemAddedEvent(item=ResponseReasoningItem() as item):
                        reasoning_id = item.id
                        reasoning_message = ReasoningMessage("Thinking...", status=MessageStatus.EXECUTING)
                        self.reasoning_messages[reasoning_id] = reasoning_message
                        await self.message_handler.handle_agent_message(reasoning_message)

                    case ResponseReasoningSummaryPartAddedEvent() as e:
                        reasoning_id = e.item_id
                        reasoning_message = self.reasoning_messages[reasoning_id]
                        assert reasoning_message, f"Reasoning message with ID {reasoning_id} not found"
                        updated = reasoning_message.text + "\n\n" if reasoning_message.text != "Thinking..." else ""
                        reasoning_message.update(updated, status=MessageStatus.EXECUTING)

                    case ResponseReasoningSummaryTextDeltaEvent(item_id=reasoning_id, delta=delta):
                        reasoning_message = self.reasoning_messages[reasoning_id]
                        assert reasoning_message, f"Reasoning message with ID {reasoning_id} not found"
                        updated = reasoning_message.text + delta
                        reasoning_message.update(updated, status=MessageStatus.EXECUTING)

                    case ResponseReasoningSummaryTextDoneEvent(item_id=reasoning_id) as e:
                        pass

                    case ResponseOutputItemDoneEvent(item=ResponseReasoningItem() as item):
                        reasoning_id = item.id
                        reasoning_message = self.reasoning_messages[reasoning_id]
                        assert reasoning_message, f"Reasoning message with ID {reasoning_id} not found"
                        reasoning_message.update(reasoning_message.text, status=MessageStatus.IDLE)

                    case ResponseOutputItemAddedEvent(item=ResponseFunctionToolCall(name=tool_name, call_id=call_id)):
                        # TODO(serialx): We should move all tool call lifecycle start to here
                        #                ResponseOutputItemDoneEvent can have race conditions in case of task tool calls
                        #                Because we stream sub-agent events to our method: handle_task_tool_event()
                        # XXX(serialx): Just handle task tool call lifecycle here for now
                        #               I'm deferring this because `arguments` is not available here... need to refactor
                        if tool_name == "task":
                            await self.handle_tool_call(tool_name, "{}", call_id)

                    case ResponseTextDeltaEvent(delta=delta) if delta:
                        await self.handle_text_delta(delta)

                    case ResponseOutputItemDoneEvent(
                        item=ResponseFunctionToolCall(name=tool_name, arguments=arguments, call_id=call_id)
                    ):
                        # XXX(serialx): See above comments
                        if tool_name == "task":
                            assert call_id in self.tool_messages, f"Tool call ID {call_id} not found in tool messages"
                            task_tool_message = self.tool_messages[call_id]
                            assert isinstance(task_tool_message, TaskToolMessage), (
                                "Tool message must be a TaskToolMessage instance"
                            )
                            args = json.loads(arguments)
                            task_tool_message.description = args.get("description", "")
                            task_tool_message.prompt = args.get("prompt", "")
                        else:
                            await self.handle_tool_call(tool_name, arguments, call_id)

                    case ResponseCompletedEvent():
                        # When in agent handoff or stop at tool situations, the tools should be in executing status.
                        # We find all the executing status tool messages and mark them as success.
                        for tool_message in self.tool_messages.values():
                            if tool_message.status == MessageStatus.EXECUTING:
                                tool_message.status = MessageStatus.SUCCESS

            case RunItemStreamEvent(item=item):
                # log(f"RunItemStreamEvent item: {item.type}")
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

    async def handle_task_tool_event(self, tool_name: str, tool_call_id: str, event: StreamEvent) -> None:
        """Handle streaming events from task tool sub-agents.

        Args:
            tool_name: Name of the tool (e.g., "task")
            tool_call_id: Unique identifier for this tool call
            event: The streaming event from the sub-agent

        Note: This is called by the main app to handle task tool events.
        The main app receives this event from the agent's task tool handler.
        """

        assert tool_call_id in self.tool_messages, f"Tool call ID {tool_call_id} not found in tool messages"
        tool_message = self.tool_messages[tool_call_id]
        assert isinstance(tool_message, TaskToolMessage), "Tool message must be a TaskToolMessage instance"
        await tool_message.handle_task_tool_event(event)

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
