"""Session loading functionality for vibecore."""

from typing import Any

from agents import Session
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseInputItemParam,
    ResponseOutputItem,
    ResponseOutputMessage,
    ResponseReasoningItem,
)
from pydantic import TypeAdapter
from textual import log

from vibecore.utils.text import TextExtractor
from vibecore.widgets.messages import (
    AgentMessage,
    BaseMessage,
    MessageStatus,
    ReasoningMessage,
    UserMessage,
)
from vibecore.widgets.tool_message_factory import create_tool_message
from vibecore.widgets.tool_messages import BaseToolMessage


class SessionLoader:
    """Loads and parses session history into message widgets."""

    def __init__(self, session: Session):
        """Initialize SessionLoader with a session.

        Args:
            session: The JSONL session to load from
        """
        self.session = session
        self.adapter = TypeAdapter(ResponseOutputItem)
        self.tool_calls_pending: dict[str, tuple[str, str]] = {}

    async def load_history(self) -> list[BaseMessage]:
        """Load all session items and convert to message widgets.

        Returns:
            List of message widgets from the session history

        Raises:
            RuntimeError: If there are pending tool calls without outputs
        """
        session_items = await self.session.get_items()
        messages = []

        for item in session_items:
            if message := self.parse_session_item(item):
                messages.append(message)

        self._validate_no_pending_calls()
        return messages

    def parse_session_item(self, item: ResponseInputItemParam) -> BaseMessage | None:
        """Parse a single session item into a message widget.

        Args:
            item: Raw session item from the session

        Returns:
            A message widget or None if item cannot be parsed
        """
        # Try to parse as output item first
        if output_item := self._parse_output_item(item):
            return output_item

        # Otherwise try to parse as input item
        return self._parse_input_item(item)

    def _parse_output_item(self, item: Any) -> BaseMessage | None:
        """Try to parse item as ResponseOutputItem.

        Args:
            item: Raw item dict

        Returns:
            A message widget or None if not a valid output item
        """
        try:
            output_item = self.adapter.validate_python(item)

            match output_item:
                case ResponseOutputMessage(role="user", content=content):
                    # User message
                    text_content = TextExtractor.extract_from_content(content)
                    return UserMessage(text_content)

                case ResponseReasoningItem(summary=summary):
                    # assert len(summary) == 1, "Summary must contain exactly one item"
                    summary_merged = "\n\n".join(item.text for item in summary) if summary else "Thinking..."
                    return ReasoningMessage(summary_merged, status=MessageStatus.IDLE)

                case ResponseOutputMessage(role="assistant", content=content):
                    # Handle assistant messages
                    text_content = TextExtractor.extract_from_content(content)
                    if text_content:
                        # If agent decides to immediately tool call, we often have no text content
                        return AgentMessage(text_content, status=MessageStatus.IDLE)
                    return None

                case ResponseFunctionToolCall(call_id=call_id, name=name, arguments=arguments) if call_id:
                    log(f"Tool call: {name} with arguments: {arguments}")
                    # Tool call - store for matching with output
                    self._handle_tool_call(call_id, name, str(arguments))
                    return None

                case _:
                    # Log unknown output item types for debugging
                    log(f"Unknown output item type: {type(output_item).__name__}")
                    return None

        except Exception:
            # Not a valid output item
            return None

    def _parse_input_item(self, item: Any) -> BaseMessage | None:
        """Parse items that are input-only (not valid output items).

        Args:
            item: Raw item

        Returns:
            A message widget or None if item cannot be parsed
        """
        if not isinstance(item, dict):
            return None

        match item:
            case {"role": "user", "content": content}:
                # User message input (EasyInputMessageParam is not convertible to ResponseOutputMessage)
                text_content = str(content) if isinstance(content, list) else content
                return UserMessage(text_content)

            case {"type": "function_call_output", "call_id": call_id, "output": output}:
                # Tool output - check if we have a pending call
                return self._create_tool_message(call_id, output)

            case _:
                # Log unhandled input items
                log(f"Unhandled session item: {item}")
                return None

    def _handle_tool_call(self, call_id: str, name: str, arguments: str) -> None:
        """Track pending tool calls for matching with outputs.

        Args:
            call_id: The tool call ID
            name: The tool name
            arguments: The tool arguments as a string
        """
        self.tool_calls_pending[call_id] = (name, arguments)

    def _create_tool_message(self, call_id: str, output: str) -> BaseToolMessage | None:
        """Create tool message by matching call_id with pending calls.

        Args:
            call_id: The tool call ID
            output: The tool output

        Returns:
            A BaseToolMessage widget, or None if no matching call found
        """
        if not call_id or call_id not in self.tool_calls_pending:
            return None

        tool_name, command = self.tool_calls_pending.pop(call_id)

        # Determine status based on output
        output_str = str(output) if output else ""
        status = MessageStatus.SUCCESS

        # Use factory to create the appropriate tool message with output
        return create_tool_message(
            tool_name=tool_name,
            arguments=command,
            output=output_str,
            status=status,
        )

    def _validate_no_pending_calls(self) -> None:
        """Validate that there are no pending tool calls without outputs.

        Raises:
            RuntimeError: If there are pending tool calls
        """
        if self.tool_calls_pending:
            raise RuntimeError(f"Pending tool calls without outputs found: {self.tool_calls_pending}")
