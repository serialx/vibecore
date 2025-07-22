import time
from typing import ClassVar, override

from textual import events
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.geometry import Size
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Footer, Static, TextArea


class InputBox(Widget):
    """A simple input box widget."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the input box."""
        text_area = MyTextArea(compact=True, id="input-textarea")
        yield Static(">", id="input-label")
        yield text_area


class AppFooter(Widget):
    def compose(self) -> ComposeResult:
        yield LoadingWidget(status="Generating…", id="loading-widget")
        yield InputBox()
        yield Footer()

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

    @override
    async def _on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.post_message(self.UserMessage(self.text))
            self.text = ""
            event.prevent_default()

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

    def watch_virtual_size(self, size: Size) -> None:
        """Scroll to the bottom when resized = when new content is added."""
        # If the scroll is near the end, keep the scroll sticky to the end
        epsilon = 10
        in_the_end = (size.height - (self.scroll_target_y + self.scrollable_size.height)) < epsilon
        if size.height > self.scrollable_size.height and in_the_end:
            self.scroll_end(animate=False)


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
