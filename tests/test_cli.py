"""Tests for the Vibecore CLI."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from vibecore.cli import app, find_latest_session


class TestFindLatestSession:
    """Test the find_latest_session function."""

    def test_find_latest_session_no_sessions(self, tmp_path):
        """Test when no sessions exist."""
        result = find_latest_session(project_path=tmp_path, base_dir=tmp_path)
        assert result is None

    def test_find_latest_session_with_sessions(self, tmp_path):
        """Test finding the most recent session."""
        # Create session directory structure
        from vibecore.session.path_utils import canonicalize_path

        canonical = canonicalize_path(tmp_path)
        session_dir = tmp_path / "projects" / canonical
        session_dir.mkdir(parents=True)

        # Create multiple session files with different timestamps
        session1 = session_dir / "chat-20250123-100000.jsonl"
        session2 = session_dir / "chat-20250124-150000.jsonl"
        session3 = session_dir / "chat-20250124-140000.jsonl"

        # Create files
        session1.touch()
        session2.touch()
        session3.touch()

        # Manually set modification times (session2 should be newest)
        import time

        session1.touch()
        time.sleep(0.01)
        session3.touch()
        time.sleep(0.01)
        session2.touch()

        result = find_latest_session(project_path=tmp_path, base_dir=tmp_path)
        assert result == "chat-20250124-150000"


class TestCLI:
    """Test the CLI commands."""

    def test_cli_help(self):
        """Test the help command."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Run the Vibecore TUI application" in result.stdout

    @patch("vibecore.cli.VibecoreApp")
    @patch("vibecore.cli.find_latest_session")
    def test_cli_continue_no_sessions(self, mock_find_latest, mock_app_class):
        """Test --continue when no sessions exist."""
        mock_find_latest.return_value = None

        runner = CliRunner()
        result = runner.invoke(app, ["--continue"])

        assert result.exit_code == 1
        assert "No existing sessions found" in result.stdout
        mock_app_class.assert_not_called()

    @patch("vibecore.cli.VibecoreApp")
    @patch("vibecore.cli.find_latest_session")
    def test_cli_continue_with_session(self, mock_find_latest, mock_app_class):
        """Test --continue with existing session."""
        mock_find_latest.return_value = "chat-20250124-150000"
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        runner = CliRunner()
        result = runner.invoke(app, ["--continue"])

        assert result.exit_code == 0
        assert "Continuing session: chat-20250124-150000" in result.stdout
        mock_app_class.assert_called_once()
        # Check that session_id was passed
        _, _, kwargs = mock_app_class.mock_calls[0]
        assert kwargs["session_id"] == "chat-20250124-150000"

    @patch("vibecore.cli.VibecoreApp")
    def test_cli_specific_session(self, mock_app_class):
        """Test --session with specific session ID."""
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        runner = CliRunner()
        result = runner.invoke(app, ["--session", "chat-custom-123"])

        assert result.exit_code == 0
        assert "Loading session: chat-custom-123" in result.stdout
        mock_app_class.assert_called_once()
        # Check that session_id was passed
        _, _, kwargs = mock_app_class.mock_calls[0]
        assert kwargs["session_id"] == "chat-custom-123"

    @patch("vibecore.cli.VibecoreApp")
    def test_cli_no_options(self, mock_app_class):
        """Test running without any options (new session)."""
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        runner = CliRunner()
        result = runner.invoke(app, [])

        assert result.exit_code == 0
        mock_app_class.assert_called_once()
        # Check that session_id was None (creates new session)
        _, _, kwargs = mock_app_class.mock_calls[0]
        assert kwargs["session_id"] is None
