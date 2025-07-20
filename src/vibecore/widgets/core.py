from typing import override

from textual import events, log
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Footer, Static, TextArea


class InputBox(Widget):
    """A simple input box widget."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the input box."""
        log("InputBox compose")
        log(TextArea.__init__.__doc__)
        text_area = MyTextArea(compact=True, id="input-textarea")
        yield Static(">", id="input-label")
        yield text_area


class AppFooter(Widget):
    def compose(self) -> ComposeResult:
        yield InputBox()
        yield Footer()


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
