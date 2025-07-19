from time import monotonic
from typing import ClassVar

from textual import log, on
from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Digits, Footer, Header


class TimeDisplay(Digits):
    """A widget to display elapsed time."""

    start_time = reactive(monotonic)
    time = reactive(0.0)
    total = reactive(0.0)

    def on_mount(self) -> None:
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self) -> None:
        self.time = self.total + (monotonic() - self.start_time)

    def watch_time(self, time: float) -> None:
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)
        self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")

    def start(self) -> None:
        """Start the timer."""
        self.start_time = monotonic()
        self.update_timer.resume()

    def stop(self) -> None:
        """Stop the timer."""
        self.update_timer.pause()
        self.total += monotonic() - self.start_time
        self.time = self.total

    def reset(self) -> None:
        self.total = 0.0
        self.time = 0.0


class Stopwatch(HorizontalGroup):
    """A stopwatch widget."""

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Start", id="start", variant="success")
        yield Button("Stop", id="stop", variant="error")
        yield Button("Reset", id="reset")
        yield TimeDisplay()
        log("start")

    @on(Button.Pressed, "#start")
    def on_start(self, event: Button.Pressed) -> None:
        time_display = self.query_one(TimeDisplay)
        time_display.start()
        self.add_class("started")

    @on(Button.Pressed, "#stop")
    def on_stop(self, event: Button.Pressed) -> None:
        time_display = self.query_one(TimeDisplay)
        time_display.stop()
        self.remove_class("started")

    @on(Button.Pressed, "#reset")
    def on_reset(self, event: Button.Pressed) -> None:
        time_display = self.query_one(TimeDisplay)
        time_display.reset()


class StopwatchApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "stopwatch03.tcss"
    BINDINGS: ClassVar = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_stopwatch", "Add"),
        ("r", "remove_stopwatch", "Remove"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield VerticalScroll(Stopwatch(), Stopwatch(), Stopwatch(), id="timers")

    def action_add_stopwatch(self) -> None:
        """An action to add a timer."""
        new_stopwatch = Stopwatch()
        self.query_one("#timers").mount(new_stopwatch)
        new_stopwatch.scroll_visible()

    def action_remove_stopwatch(self) -> None:
        """Called to remove a timer."""
        timers = self.query("Stopwatch")
        if timers:
            timers.last().remove()

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

    app = StopwatchApp()
    app.run()
