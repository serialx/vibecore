"""Test harness for snapshot testing vibecore widgets."""

from pathlib import Path
from typing import Any, ClassVar, cast

from agents.result import RunResultBase
from openai.types.responses import ResponseInputItemParam
from textual.app import ComposeResult

from vibecore.context import AppAwareContext
from vibecore.flow import Vibecore, VibecoreTextualRunner
from vibecore.main import VibecoreApp
from vibecore.session import JSONLSession
from vibecore.widgets.core import AppFooter

# Get the vibecore source directory for CSS paths
VIBECORE_SRC = Path(__file__).parent.parent.parent / "src" / "vibecore"


# Fixed working directory path for consistent snapshots
FIXED_CWD = "~/test/workspace"


class VibecoreTestApp(VibecoreApp):
    """A test-oriented version of VibecoreApp for snapshot testing.

    This subclass modifies the app to:
    - Load sessions from fixture files synchronously
    - Disable agent interactions
    - Provide deterministic rendering for snapshots
    """

    # Override CSS_PATH to use absolute paths
    CSS_PATH: ClassVar = [
        str(VIBECORE_SRC / "widgets" / "core.tcss"),
        str(VIBECORE_SRC / "widgets" / "messages.tcss"),
        str(VIBECORE_SRC / "widgets" / "tool_messages.tcss"),
        str(VIBECORE_SRC / "widgets" / "expandable.tcss"),
        str(VIBECORE_SRC / "widgets" / "info.tcss"),
        str(VIBECORE_SRC / "main.tcss"),
    ]

    def __init__(self, session_fixture_path: Path | None = None) -> None:
        """Initialize test app with optional session fixture.

        Args:
            session_fixture_path: Path to JSONL session fixture file
            context: Optional VibecoreContext (creates new one if not provided)
        """
        # Use provided context or create a new one
        vibecore = Vibecore()

        # Create a runner for the test app
        # Cast needed: test apps don't use real contexts, but runner expects AppAwareContext
        runner = VibecoreTextualRunner(
            cast("Vibecore[AppAwareContext, RunResultBase]", vibecore),
            context=None,
            session=None,
        )

        # Initialize with a test session ID
        super().__init__(runner)

        # Store the fixture path for loading
        self.fixture_session: JSONLSession | None = None
        self.session_fixture_path = session_fixture_path

        # Override to prevent actual session file creation
        if session_fixture_path:
            self._override_session_with_fixture()

    def _override_session_with_fixture(self) -> None:
        """Override the session to load from fixture file."""
        if not self.session_fixture_path or not self.session_fixture_path.exists():
            return

        # Create a mock session that reads from our fixture
        class TestJSONLSession(JSONLSession):
            def __init__(self, fixture_path: Path, *args: Any, **kwargs: Any):
                super().__init__(*args, **kwargs)
                self.fixture_path = fixture_path

            async def get_items(self, limit: int | None = None) -> list[ResponseInputItemParam]:
                """Load items from fixture file."""
                import json

                items = []
                with open(self.fixture_path) as f:
                    for line in f:
                        if line.strip():
                            items.append(json.loads(line))

                # Apply limit if specified
                if limit is not None and limit > 0:
                    items = items[-limit:]  # Get last N items

                return items

            async def save(self) -> None:
                """No-op for testing."""
                pass

            async def append_item(self, item: dict) -> None:
                """No-op for testing."""
                pass

        # Replace the session with our test version
        self.fixture_session = TestJSONLSession(
            fixture_path=self.session_fixture_path,
            session_id="test-snapshot",
            project_path=None,
            base_dir=None,
        )

    def compose(self) -> ComposeResult:
        """Create child widgets for the app with patched AppFooter."""
        from textual.widgets import Header

        from vibecore.widgets.core import MainScroll
        from vibecore.widgets.info import Welcome

        # Create a patched AppFooter instance
        footer = AppFooter()
        # Override the method on this instance
        footer.get_current_working_directory = lambda: FIXED_CWD

        yield Header()
        yield footer  # Use our patched footer instance
        with MainScroll(id="messages"):
            if self.show_welcome:
                yield Welcome()

    async def on_mount(self) -> None:
        """Override on_mount to disable cursor blinking in MyTextArea for deterministic snapshots."""
        if self.fixture_session:
            await self.load_session_history(self.fixture_session)  # Load history synchronously

        # Find MyTextArea and disable cursor blinking
        from vibecore.widgets.core import MyTextArea

        text_area = self.query_one(MyTextArea)
        text_area.cursor_blink = False


def create_test_app(session_fixture: str | Path | None = None) -> VibecoreTestApp:
    """Create a test app instance with optional session fixture.

    Args:
        session_fixture: Path to JSONL session fixture file (relative to tests/fixtures/sessions)

    Returns:
        TestVibecoreApp instance ready for snapshot testing
    """
    fixture_path = None
    if session_fixture:
        if isinstance(session_fixture, str):
            # Assume relative to fixtures/sessions directory
            fixture_path = Path(__file__).parent.parent / "fixtures" / "sessions" / session_fixture
        else:
            fixture_path = Path(session_fixture)

    return VibecoreTestApp(session_fixture_path=fixture_path)
