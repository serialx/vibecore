"""Expandable content widgets for Textual applications."""

from textual.app import ComposeResult
from textual.content import Content
from textual.events import Click
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Markdown, Static


class ExpandableContent(Widget):
    """A widget that shows truncated content with an expandable button."""

    expanded: reactive[bool] = reactive(False, recompose=True)

    def __init__(
        self, content: str | Content, truncated_lines: int = 3, collapsed_text: str | Content | None = None, **kwargs
    ) -> None:
        """
        Initialize the ExpandableContent widget.

        Args:
            content: The full content to display (str or Content for safe rendering)
            truncated_lines: Number of lines to show when collapsed (ignored if collapsed_text is provided)
            collapsed_text: Custom text to show when collapsed (overrides truncated content)
            **kwargs: Additional keyword arguments for Widget
        """
        super().__init__(**kwargs)
        self.content = content
        self.truncated_lines = truncated_lines
        self.collapsed_text = collapsed_text
        # Extract plain text for line counting
        self.content_str = str(content) if isinstance(content, Content) else content
        self.lines = self.content_str.splitlines()
        self.total_lines = len(self.lines)

    def compose(self) -> ComposeResult:
        """Create child widgets based on expanded state."""
        if self.expanded:
            # Show all content
            yield Static(self.content, classes="expandable-content-full")
            yield Static("▲ collapse", classes="expandable-toggle expanded")
        else:
            # Show custom collapsed text if provided
            if self.collapsed_text is not None:
                yield Static(self.collapsed_text, classes="expandable-toggle collapsed")
            # Show truncated content
            elif self.total_lines > self.truncated_lines:
                truncated_text = "\n".join(self.lines[: self.truncated_lines])
                # Preserve Content safety if original was Content
                truncated_content = Content(truncated_text) if isinstance(self.content, Content) else truncated_text
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
            language: Programming language for syntax highlighting (empty string for plain markdown)
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
        # Determine content format based on language
        if self.language:
            # Render as code block with syntax highlighting
            full_content = f"```{self.language}\n{self.code}\n```"
            truncated_lines = "\n".join(self.lines[: self.truncated_lines])
            truncated_content = f"```{self.language}\n{truncated_lines}\n```"
        else:
            # Render as plain markdown (no code block)
            full_content = self.code
            truncated_content = "\n".join(self.lines[: self.truncated_lines])

        if self.expanded:
            # Show all content
            yield Markdown(full_content, classes="expandable-markdown-full")
            yield Static("▲ collapse", classes="expandable-toggle expanded")
        else:
            # Show truncated content
            if self.total_lines > self.truncated_lines:
                yield Markdown(truncated_content, classes="expandable-markdown-truncated")
                remaining_lines = self.total_lines - self.truncated_lines
                yield Static(f"… +{remaining_lines} more lines (view)", classes="expandable-toggle collapsed")
            else:
                # If content fits, just show it all
                yield Markdown(full_content, classes="expandable-markdown-full")

    def on_click(self, event: Click) -> None:
        """Handle click events to toggle expansion."""
        # Only toggle if we clicked on the toggle element
        if event.widget and event.widget.has_class("expandable-toggle"):
            self.expanded = not self.expanded
            event.stop()
