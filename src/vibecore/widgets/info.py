from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

VIBECORE_LOGO = """
██╗   ██╗██╗██████╗ ███████╗ ██████╗ ██████╗ ██████╗ ███████╗
██║   ██║██║██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
██║   ██║██║██████╔╝█████╗  ██║     ██║   ██║██████╔╝█████╗
╚██╗ ██╔╝██║██╔══██╗██╔══╝  ██║     ██║   ██║██╔══██╗██╔══╝
 ╚████╔╝ ██║██████╔╝███████╗╚██████╗╚██████╔╝██║  ██║███████╗
  ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝
""".strip()


class Welcome(Widget):
    """A simple input box widget."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the input box."""
        yield Static(f"[$primary]{VIBECORE_LOGO}[/]", classes="logo")
        yield Static("Welcome to [$text-primary][b]Vibecore[/b][/]!", classes="title")
        yield Static(
            "Type '/help' to see available commands.",
            classes="subtitle",
        )
