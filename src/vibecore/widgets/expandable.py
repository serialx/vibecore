"""Expandable content widgets for Textual applications."""

from textual.app import ComposeResult
from textual.events import Click
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Markdown, Static


class ExpandableContent(Widget):
    """A widget that shows truncated content with an expandable button."""

    expanded: reactive[bool] = reactive(False, recompose=True)

    def __init__(self, content: str, truncated_lines: int = 3, **kwargs) -> None:
        """
        Initialize the ExpandableContent widget.

        Args:
            content: The full content to display
            truncated_lines: Number of lines to show when collapsed
            **kwargs: Additional keyword arguments for Widget
        """
        super().__init__(**kwargs)
        self.content = content
        self.truncated_lines = truncated_lines
        self.lines = content.splitlines()
        self.total_lines = len(self.lines)

    def compose(self) -> ComposeResult:
        """Create child widgets based on expanded state."""
        if self.expanded:
            # Show all content
            yield Static(self.content, classes="expandable-content-full")
            yield Static("▲ collapse", classes="expandable-toggle expanded")
        else:
            # Show truncated content
            if self.total_lines > self.truncated_lines:
                truncated_content = "\n".join(self.lines[: self.truncated_lines])
                yield Static(truncated_content, classes="expandable-content-truncated")
                remaining_lines = self.total_lines - self.truncated_lines
                yield Static(f"… +{remaining_lines} more lines (view)", classes="expandable-toggle collapsed")
            else:
                # If content fits, just show it all
                yield Static(self.content, classes="expandable-content-full")

    def on_click(self, event: Click) -> None:
        """Handle click events to toggle expansion."""
        # Only toggle if we clicked on the toggle element
        if event.widget and event.widget.has_class("expandable-toggle"):
            self.expanded = not self.expanded
            event.stop()


class ExpandableMarkdown(Widget):
    """A widget that shows truncated Markdown content with an expandable button."""

    expanded: reactive[bool] = reactive(False, recompose=True)

    def __init__(self, code: str, language: str = "python", truncated_lines: int = 8, **kwargs) -> None:
        """
        Initialize the ExpandableMarkdown widget.

        Args:
            code: The full code to display
            language: Programming language for syntax highlighting
            truncated_lines: Number of lines to show when collapsed
            **kwargs: Additional keyword arguments for Widget
        """
        super().__init__(**kwargs)
        self.code = code
        self.language = language
        self.truncated_lines = truncated_lines
        self.lines = code.splitlines()
        self.total_lines = len(self.lines)

    def compose(self) -> ComposeResult:
        """Create child widgets based on expanded state."""
        if self.expanded:
            # Show all code
            yield Markdown(f"```{self.language}\n{self.code}\n```", classes="expandable-markdown-full")
            yield Static("▲ collapse", classes="expandable-toggle expanded")
        else:
            # Show truncated code
            if self.total_lines > self.truncated_lines:
                truncated_code = "\n".join(self.lines[: self.truncated_lines])
                yield Markdown(f"```{self.language}\n{truncated_code}\n```", classes="expandable-markdown-truncated")
                remaining_lines = self.total_lines - self.truncated_lines
                yield Static(f"… +{remaining_lines} more lines (view)", classes="expandable-toggle collapsed")
            else:
                # If code fits, just show it all
                yield Markdown(f"```{self.language}\n{self.code}\n```", classes="expandable-markdown-full")

    def on_click(self, event: Click) -> None:
        """Handle click events to toggle expansion."""
        # Only toggle if we clicked on the toggle element
        if event.widget and event.widget.has_class("expandable-toggle"):
            self.expanded = not self.expanded
            event.stop()
