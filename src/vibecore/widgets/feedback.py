"""Feedback widget for collecting user feedback."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Checkbox, Static, TextArea

from vibecore.widgets.messages import BaseMessage, MessageHeader, MessageStatus


class FeedbackWidget(BaseMessage):
    """A widget to collect user feedback with Good/Bad rating and optional text comment."""

    class FeedbackSubmitted(Message):
        """Event emitted when feedback is submitted."""

        def __init__(self, rating: str, comment: str, criteria: dict[str, bool]) -> None:
            """
            Construct a FeedbackSubmitted message.

            Args:
                rating: The rating ("good" or "bad").
                comment: Optional text comment from the user.
                criteria: Dict of criterion name to boolean value.
            """
            super().__init__()
            self.rating = rating
            self.comment = comment
            self.criteria = criteria

    rating: reactive[str | None] = reactive(None)
    comment: reactive[str] = reactive("")
    submitted: reactive[bool] = reactive(False)
    show_comment_input: reactive[bool] = reactive(False)
    show_criteria: reactive[bool] = reactive(False)

    def __init__(self, prompt: str = "How was this response?", **kwargs) -> None:
        """
        Construct a FeedbackWidget.

        Args:
            prompt: The prompt text to display.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=MessageStatus.IDLE, **kwargs)
        self.prompt = prompt
        self.add_class("feedback-widget")

    def get_header_params(self) -> tuple[str, str, bool]:
        """Get parameters for MessageHeader."""
        return ("⏺", self.prompt, False)

    def compose(self) -> ComposeResult:
        """Create child widgets for the feedback widget."""
        yield MessageHeader("⏺", self.prompt, status=self.status)

        with Horizontal(classes="feedback-controls"):
            yield Button("👍 Good", id="feedback-good", classes="feedback-button good-button", variant="success")
            yield Button("👎 Bad", id="feedback-bad", classes="feedback-button bad-button", variant="error")

        # Feedback form containing criteria, comment area, and submit button (shown after rating selection)
        with Vertical(id="feedback-form", classes="feedback-form"):
            # Structured feedback criteria checkboxes
            with Vertical(classes="feedback-criteria"):
                yield Static("Please check any criteria that apply:", classes="criteria-label")
                yield Checkbox("Factual accuracy - Was the information correct?", id="criteria-accuracy")
                yield Checkbox("Task completion - Did it fully address the request?", id="criteria-completion")
                yield Checkbox(
                    "Instruction following - Did it follow specific constraints or requirements?",
                    id="criteria-instructions",
                )
                yield Checkbox(
                    "Good format/structure - Are the format and structure appropriate?", id="criteria-format"
                )

            # Comment text area
            with Vertical(classes="feedback-comment-area"):
                yield Static("Optional comment:", classes="comment-label")
                yield TextArea(id="feedback-textarea", classes="feedback-textarea", show_line_numbers=False)

            # Submit button
            yield Button("Submit", id="feedback-submit", classes="feedback-submit-button", variant="primary")

        with Vertical(id="feedback-result", classes="feedback-result"):
            yield Static("", id="feedback-result-text")

    def on_mount(self) -> None:
        """Initialize widget state on mount."""
        # Hide feedback form and result initially
        self.query_one("#feedback-form").display = False
        self.query_one("#feedback-result").display = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if self.submitted:
            return  # Ignore clicks after submission

        if button_id == "feedback-good":
            self.rating = "good"
            self._show_feedback_form()
            event.button.add_class("selected")
            self.query_one("#feedback-bad").remove_class("selected")

        elif button_id == "feedback-bad":
            self.rating = "bad"
            self._show_feedback_form()
            event.button.add_class("selected")
            self.query_one("#feedback-good").remove_class("selected")

        elif button_id == "feedback-submit":
            self._submit_feedback()

    def _show_feedback_form(self) -> None:
        """Show the feedback form (criteria, comment area, and submit button)."""
        self.show_criteria = True
        self.show_comment_input = True
        feedback_form = self.query_one("#feedback-form")
        feedback_form.display = True
        feedback_form.refresh()

    def _get_criteria_values(self) -> dict[str, bool]:
        """Get the current state of all criteria checkboxes."""
        return {
            "accuracy": self.query_one("#criteria-accuracy", Checkbox).value,
            "completion": self.query_one("#criteria-completion", Checkbox).value,
            "instructions": self.query_one("#criteria-instructions", Checkbox).value,
            "format": self.query_one("#criteria-format", Checkbox).value,
        }

    def _submit_feedback(self) -> None:
        """Submit the feedback."""
        if not self.rating:
            # Require a rating before submission
            return

        self.submitted = True
        self.comment = self.query_one("#feedback-textarea", TextArea).text
        criteria = self._get_criteria_values()

        # Hide controls and form, show result
        self.query_one(".feedback-controls").display = False
        self.query_one("#feedback-form").display = False

        # Show result
        result_container = self.query_one("#feedback-result")
        result_text = self.query_one("#feedback-result-text", Static)

        rating_emoji = "👍" if self.rating == "good" else "👎"
        result_msg = f"{rating_emoji} Thank you for your feedback!"
        if self.comment:
            result_msg += f"\nComment: {self.comment}"

        result_text.update(Content(result_msg))
        result_container.display = True

        # Update status to success
        self.status = MessageStatus.SUCCESS

        # Emit feedback event
        self.post_message(self.FeedbackSubmitted(self.rating, self.comment, criteria))
