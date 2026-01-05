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
    """Welcome message widget displaying the Vibecore logo and greeting."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the welcome message."""
        yield Static(f"[$primary]{VIBECORE_LOGO}[/]", classes="logo")
        yield Static("Welcome to [$text-primary][b]Vibecore[/b][/]!", classes="title")
        yield Static(
            "Type '/help' to see available commands.",
            classes="subtitle",
        )
