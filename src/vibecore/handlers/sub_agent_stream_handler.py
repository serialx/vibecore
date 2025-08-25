"""Stream handler for processing sub-agent streaming responses."""

from typing import Protocol

from agents import RunResultStreaming

from vibecore.handlers.stream_handler import AgentStreamHandler, MessageHandler
from vibecore.widgets.messages import MessageStatus


class SubAgentMessageHandler(Protocol):
    """Protocol defining the interface for sub-agent message handling."""

    async def handle_sub_agent_message(self, message) -> None:
        """Add a sub-agent message to the widget's message list."""
        ...

    async def handle_sub_agent_complete(self, output: str) -> None:
        """Handle when the sub-agent has completed processing."""
        ...

    async def handle_sub_agent_error(self, error: Exception) -> None:
        """Handle errors during sub-agent streaming."""
        ...


class SubAgentStreamHandler(AgentStreamHandler):
    """Specialized handler for sub-agent streaming responses."""

    def __init__(
        self,
        message_handler: MessageHandler,
        sub_agent_message_handler: SubAgentMessageHandler,
        agent_name: str,
        parent_context: dict | None = None,
    ) -> None:
        """Initialize the sub-agent stream handler.

        Args:
            message_handler: The MessageHandler protocol instance
            sub_agent_message_handler: Handler for sub-agent specific messages
            agent_name: Name of the sub-agent
            parent_context: Optional metadata from parent agent
        """
        super().__init__(message_handler)
        self.sub_agent_message_handler = sub_agent_message_handler
        self.agent_name = agent_name
        self.parent_context = parent_context or {}
        self.sub_agent_message = None  # Will be created when first delta arrives

    async def handle_text_delta(self, delta: str) -> None:
        """Override to use SubAgentMessage instead of AgentMessage.

        Args:
            delta: The text delta to append
        """
        self.message_content += delta
        if not self.sub_agent_message:
            # Import here to avoid circular dependency
            from vibecore.widgets.messages import SubAgentMessage

            self.sub_agent_message = SubAgentMessage(
                agent_name=self.agent_name,
                content=self.message_content,
                status=MessageStatus.EXECUTING,
                metadata=self.parent_context,
            )
            await self.sub_agent_message_handler.handle_sub_agent_message(self.sub_agent_message)
        else:
            self.sub_agent_message.update_content(self.message_content)

    async def handle_message_complete(self) -> None:
        """Finalize sub-agent message when complete."""
        if self.sub_agent_message:
            self.sub_agent_message.update_status(MessageStatus.SUCCESS)
            self.sub_agent_message = None
            self.message_content = ""

    async def process_stream(self, result: RunResultStreaming) -> None:
        """Process all streaming events from the sub-agent.

        Args:
            result: The streaming result to process

        Returns:
            The final output from the sub-agent
        """
        try:
            async for event in result.stream_events():
                await self.handle_event(event)

            # Wait for the final output
            output = await result.final_output
            await self.sub_agent_message_handler.handle_sub_agent_complete(output)
            return output

        except Exception as e:
            await self.sub_agent_message_handler.handle_sub_agent_error(e)
            if self.sub_agent_message:
                self.sub_agent_message.update_status(MessageStatus.ERROR)
            raise

        finally:
            await self.message_handler.handle_agent_finished()
