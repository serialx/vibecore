"""Test harness for snapshot testing vibecore widgets."""

from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import MagicMock

from agents import Agent
from openai.types.responses import ResponseInputItemParam

from vibecore.context import VibecoreContext
from vibecore.main import VibecoreApp
from vibecore.session import JSONLSession

# Get the vibecore source directory for CSS paths
VIBECORE_SRC = Path(__file__).parent.parent / "src" / "vibecore"


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

    def __init__(
        self,
        session_fixture_path: Path | None = None,
        context: VibecoreContext | None = None,
    ) -> None:
        """Initialize test app with optional session fixture.

        Args:
            session_fixture_path: Path to JSONL session fixture file
            context: Optional VibecoreContext (creates new one if not provided)
        """
        # Create a mock agent that won't actually run
        mock_agent = MagicMock(spec=Agent)
        mock_agent.name = "TestAgent"

        # Use provided context or create a new one
        if context is None:
            context = VibecoreContext()

        # Initialize with a test session ID
        super().__init__(
            context=context,
            agent=mock_agent,
            session_id="test-snapshot",
            print_mode=False,
        )

        # Store the fixture path for loading
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
        self.session = TestJSONLSession(
            fixture_path=self.session_fixture_path,
            session_id="test-snapshot",
            project_path=None,
            base_dir=None,
        )

        # Mark that we should load history
        self._session_id_provided = True

    async def on_mount(self) -> None:
        """Override on_mount to disable cursor blinking in MyTextArea for deterministic snapshots."""
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
            fixture_path = Path(__file__).parent / "fixtures" / "sessions" / session_fixture
        else:
            fixture_path = Path(session_fixture)

    return VibecoreTestApp(session_fixture_path=fixture_path)
