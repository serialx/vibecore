from typing import ClassVar, override

from textual import events, log
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Footer, Header, Static, TextArea


class UserMessage(Widget):
    """A widget to display user messages."""

    def __init__(self, text: str, **kwargs) -> None:
        """
        Construct a UserMessage.

        Args:
            text: The text to display.
            **kwargs: Additional keyword arguments for Static.
        """
        super().__init__(**kwargs)
        self.text = text
        self.add_class("user-message")

    def compose(self) -> ComposeResult:
        """Create child widgets for the user message."""
        yield Horizontal(Static("> ", classes="prefix"), Static(self.text))


class MyFooter(Widget):
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


class InputBox(Widget):
    """A simple input box widget."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the input box."""
        log("InputBox compose")
        log(TextArea.__init__.__doc__)
        text_area = MyTextArea(compact=True)
        yield Horizontal(Static(">", id="input-label"), text_area)


class VibecoreApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "main.tcss"
    BINDINGS: ClassVar = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield MyFooter()
        # yield Footer()
        yield VerticalScroll(id="timers")

    def on_my_text_area_user_message(self, event: MyTextArea.UserMessage) -> None:
        """Handle user messages from the text area."""
        log(f"User message: {event.text}")
        user_message = UserMessage(event.text)
        self.query_one("#timers").mount(user_message)
        user_message.scroll_visible()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"


def main() -> None:
    """Run the StopwatchApp."""
    import logging

    from textual.logging import TextualHandler

    logging.basicConfig(
        level="NOTSET",
        handlers=[TextualHandler()],
    )

    app = VibecoreApp()
    app.run()
