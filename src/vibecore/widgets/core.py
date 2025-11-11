import os
import time
from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Footer, ProgressBar, Static, TextArea


class InputBox(Widget):
    """A simple input box widget."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the input box."""
        text_area = MyTextArea(compact=True, id="input-textarea")
        yield Static(">", id="input-label")
        yield text_area


class AppFooter(Widget):
    def get_current_working_directory(self) -> str:
        """Get the current working directory for display.

        Returns:
            The current working directory path, with home directory replaced by ~
        """
        cwd = os.getcwd()
        if cwd.startswith(os.path.expanduser("~")):
            cwd = cwd.replace(os.path.expanduser("~"), "~", 1)
        return cwd

    def compose(self) -> ComposeResult:
        yield LoadingWidget(status="Generating…", id="loading-widget")
        yield InputBox()
        # Wrap ProgressBar in vertical container to dock it right
        with Vertical(id="context-info"):
            cwd = self.get_current_working_directory()
            yield Static(f"{cwd}", id="context-cwd")
            with Horizontal(id="context-progress-container"):
                yield Static("Context: ", id="context-progress-label")
                yield ProgressBar(total=100, id="context-progress", show_eta=False)
        yield Footer()

    def set_context_progress(self, percent: float) -> None:
        bar = self.query_one("#context-progress", ProgressBar)
        value = max(0, min(100, int(percent * 100)))
        bar.update(total=100, progress=value)

    def on_mount(self) -> None:
        """Hide loading widget on mount."""
        self.query_one("#loading-widget").display = False

    def show_loading(self, status: str = "Generating…", metadata: str = "") -> None:
        """Show the loading widget with given status and metadata."""
        loading = self.query_one("#loading-widget", LoadingWidget)
        loading._start_time = time.monotonic()  # Reset the timer
        loading.update_status(status)
        if metadata:
            loading.update_metadata(metadata)
        loading.display = True

    def hide_loading(self) -> None:
        """Hide the loading widget."""
        self.query_one("#loading-widget").display = False


class MyTextArea(TextArea):
    class UserMessage(Message):
        """A user message input."""

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

        def __repr__(self) -> str:
            return f"UserMessage(text={self.text!r})"

    def __init__(self, **kwargs) -> None:
        """Initialize MyTextArea with history tracking."""
        super().__init__(**kwargs)
        self.history_index = -1  # -1 means we're typing a new message
        self.draft_text = ""  # Store the draft when navigating history

    async def get_user_history(self) -> list[str]:
        """Get the list of user messages from the session and current input_items."""
        from vibecore.main import VibecoreApp

        app = self.app
        if isinstance(app, VibecoreApp):
            history = []

            # First, load history from the session
            if app.runner.session:
                try:
                    # Get all items from the session
                    session_items = await app.runner.session.get_items()
                    for item in session_items:
                        # Filter for user messages
                        if isinstance(item, dict):
                            # Check both "role" and "type" fields for compatibility
                            role = item.get("role") or item.get("type")
                            if role == "user":
                                content = item.get("content")
                                if isinstance(content, str):
                                    history.append(content)
                except Exception as e:
                    # Log error but don't crash
                    from textual import log

                    log(f"Error loading session history: {e}")

            return history
        return []

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Check if an action may run."""
        # If text is empty, allow app to handle ctrl+d, not as delete_right
        return not (action == "delete_right" and not self.text)

    async def _on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.post_message(self.UserMessage(self.text))
            self.text = ""
            self.history_index = -1  # Reset history navigation
            self.draft_text = ""
            event.prevent_default()
            return

        # Handle up arrow for history navigation
        if event.key == "up":
            if not self.cursor_at_start_of_text:
                # Move cursor to start of text first
                await super()._on_key(event)
                return
            else:
                # Navigate to previous history item
                history = await self.get_user_history()
                if history:
                    # Save current draft if starting history navigation
                    if self.history_index == -1:
                        self.draft_text = self.text

                    # Move to previous item
                    if self.history_index < len(history) - 1:
                        self.history_index += 1
                        self.text = history[-(self.history_index + 1)]
                        self.move_cursor((0, 0))  # Move cursor to start
                        event.prevent_default()
                        return

        # Handle down arrow for history navigation
        elif event.key == "down":
            if not self.cursor_at_end_of_text:
                # Move cursor to end of text first
                await super()._on_key(event)
                return
            else:
                # Navigate to next history item
                if self.history_index >= 0:
                    self.history_index -= 1
                    if self.history_index == -1:
                        # Return to draft
                        self.text = self.draft_text
                    else:
                        history = await self.get_user_history()
                        self.text = history[-(self.history_index + 1)]
                    # Move cursor to end of text
                    last_line = self.document.line_count - 1
                    last_column = len(self.document[last_line]) if last_line >= 0 else 0
                    self.move_cursor((last_line, last_column))
                    event.prevent_default()
                    return

        self._restart_blink()

        if self.read_only:
            return

        key = event.key
        insert_values = {
            "shift+enter": "\n",
            # Ghostty with config: keybind = shift+enter=text:\n
            "ctrl+j": "\n",
        }
        if self.tab_behavior == "indent":
            if key == "escape":
                event.stop()
                event.prevent_default()
                self.screen.focus_next()
                return
            if self.indent_type == "tabs":
                insert_values["tab"] = "\t"
            else:
                insert_values["tab"] = " " * self._find_columns_to_next_tab_stop()

        if event.is_printable or key in insert_values:
            event.stop()
            event.prevent_default()
            insert = insert_values.get(key, event.character)
            # `insert` is not None because event.character cannot be
            # None because we've checked that it's printable.
            assert insert is not None
            start, end = self.selection
            self._replace_via_keyboard(insert, start, end)


class MainScroll(ScrollableContainer):
    """A container with vertical layout and an automatic scrollbar on the Y axis."""

    ...


class LoadingWidget(Widget):
    """A loading indicator with spinner, status text, and metadata."""

    DEFAULT_CSS = """
    LoadingWidget {
        width: 1fr;
        height: 1;
        padding: 0 1;
    }

    LoadingWidget .loading-spinner {
        color: $primary;
    }

    LoadingWidget .loading-status {
        color: $text;
        margin: 0 1;
    }

    LoadingWidget .loading-metadata {
        color: $text-muted;
    }
    """

    SPINNERS: ClassVar[list[str]] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(
        self,
        status: str = "Loading…",
        show_time: bool = True,
        show_metadata: bool = True,
        metadata: str = "",
        escape_message: str = "esc to interrupt",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.status = status
        self.show_time = show_time
        self.show_metadata = show_metadata
        self.metadata = metadata
        self.escape_message = escape_message
        self._spinner_index = 0
        self._start_time = time.monotonic()
        self._spinner_timer = None

    def compose(self) -> ComposeResult:
        yield Static("", id="loading-content")

    def on_mount(self) -> None:
        """Start the spinner animation when mounted."""
        self._spinner_timer = self.set_interval(0.1, self._update_spinner)
        self._update_display()

    def on_unmount(self) -> None:
        """Stop the spinner animation when unmounted."""
        if self._spinner_timer:
            self._spinner_timer.stop()

    def _update_spinner(self) -> None:
        """Update the spinner character and elapsed time."""
        self._spinner_index = (self._spinner_index + 1) % len(self.SPINNERS)
        self._update_display()

    def _update_display(self) -> None:
        """Update the entire loading display."""
        parts = []

        # Spinner
        spinner = self.SPINNERS[self._spinner_index]
        parts.append(f"[bold]{spinner}[/bold]")

        # Status text
        parts.append(self.status)

        # Metadata section
        metadata_parts = []

        if self.show_time:
            elapsed = int(time.monotonic() - self._start_time)
            metadata_parts.append(f"{elapsed}s")

        if self.show_metadata and self.metadata:
            metadata_parts.append(self.metadata)

        if self.escape_message:
            metadata_parts.append(self.escape_message)

        if metadata_parts:
            metadata_str = " · ".join(metadata_parts)
            parts.append(f"[dim]({metadata_str})[/dim]")

        content = " ".join(parts)
        self.query_one("#loading-content", Static).update(content)

    def update_status(self, status: str) -> None:
        """Update the status text."""
        self.status = status
        self._update_display()

    def update_metadata(self, metadata: str) -> None:
        """Update the metadata text."""
        self.metadata = metadata
        self._update_display()
