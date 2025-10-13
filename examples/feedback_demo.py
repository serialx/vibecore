"""Demo application for the FeedbackWidget.

This demonstrates how to use the FeedbackWidget within VibecoreApp.
The demo shows an agent message followed by a feedback widget.
"""

from pathlib import Path
from typing import ClassVar

from agents import Agent
from textual import log

from vibecore.agents.default import create_default_agent
from vibecore.context import VibecoreContext
from vibecore.main import VibecoreApp
from vibecore.widgets.feedback import FeedbackWidget
from vibecore.widgets.messages import AgentMessage, MessageStatus, SystemMessage


class FeedbackDemoApp(VibecoreApp):
    """Demo app that shows the FeedbackWidget in action."""

    # Override CSS_PATH to use absolute paths from the vibecore module
    CSS_PATH: ClassVar = [
        Path(__file__).parent.parent / "src" / "vibecore" / "widgets" / "core.tcss",
        Path(__file__).parent.parent / "src" / "vibecore" / "widgets" / "messages.tcss",
        Path(__file__).parent.parent / "src" / "vibecore" / "widgets" / "feedback.tcss",
        Path(__file__).parent.parent / "src" / "vibecore" / "widgets" / "tool_messages.tcss",
        Path(__file__).parent.parent / "src" / "vibecore" / "widgets" / "expandable.tcss",
        Path(__file__).parent.parent / "src" / "vibecore" / "widgets" / "info.tcss",
        Path(__file__).parent.parent / "src" / "vibecore" / "main.tcss",
    ]

    async def on_mount(self) -> None:
        """Mount the app and inject demo content."""
        # Call parent's on_mount first
        await super().on_mount()

        # Add demo content
        await self.add_demo_content()

    async def add_demo_content(self) -> None:
        """Add demo agent message and feedback widget."""
        # Add agent message
        agent_msg = AgentMessage(
            "Hello! I'm an AI assistant. I can help you with various tasks like:\n\n"
            "- Answering questions\n"
            "- Writing and editing code\n"
            "- Analyzing data\n"
            "- And much more!\n\n"
            "What would you like to know?",
            status=MessageStatus.SUCCESS,
        )
        await self.add_message(agent_msg)

        # Add feedback widget
        feedback = FeedbackWidget(prompt="How was this response?")
        await self.add_message(feedback)

    async def on_feedback_widget_feedback_submitted(self, event: FeedbackWidget.FeedbackSubmitted) -> None:
        """Handle feedback submission by adding a SystemMessage to the app."""
        # Build feedback summary message
        rating_emoji = "👍" if event.rating == "good" else "👎"
        message_parts = [f"{rating_emoji} Feedback received: {event.rating.upper()}"]

        # Add criteria that were checked
        checked_criteria = [name for name, checked in event.criteria.items() if checked]
        if checked_criteria:
            message_parts.append("\nCriteria marked:")
            for criterion in checked_criteria:
                message_parts.append(f"  ✓ {criterion}")

        # Add comment if provided
        if event.comment:
            message_parts.append(f"\nComment: {event.comment}")

        feedback_message = "\n".join(message_parts)

        # Add as SystemMessage to the app
        system_msg = SystemMessage(feedback_message)
        await self.add_message(system_msg)

        # Also log for debugging
        log(f"Feedback submitted: {event.rating}")


def main():
    """Run the feedback demo app.

    This creates a minimal VibecoreApp instance with demo content.
    """
    # Create context and agent (same pattern as CLI)
    vibecore_ctx = VibecoreContext()
    agent: Agent = create_default_agent(mcp_servers=[])

    # Create the demo app
    app = FeedbackDemoApp(
        context=vibecore_ctx,
        agent=agent,
        session_id=None,
        show_welcome=False,  # Hide welcome message for cleaner demo
    )

    # Run the app
    app.run()


if __name__ == "__main__":
    main()
