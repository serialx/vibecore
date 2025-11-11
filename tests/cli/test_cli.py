"""Tests for the Vibecore CLI."""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

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

    @patch("vibecore.cli.find_latest_session")
    def test_cli_continue_no_sessions(self, mock_find_latest):
        """Test --continue when no sessions exist."""
        mock_find_latest.return_value = None

        runner = CliRunner()
        result = runner.invoke(app, ["--continue"])

        assert result.exit_code == 1
        assert "No existing sessions found" in result.stdout

    @patch("vibecore.cli.JSONLSession")
    @patch("vibecore.cli.Vibecore")
    @patch("vibecore.cli.MCPManager")
    @patch("vibecore.cli.find_latest_session")
    def test_cli_continue_with_session(
        self, mock_find_latest, mock_mcp_manager_class, mock_vibecore_class, mock_jsonl_class
    ):
        """Test --continue with existing session."""
        mock_find_latest.return_value = "chat-20250124-150000"

        # Mock the vibecore instance with async methods
        mock_vibecore = MagicMock()
        mock_vibecore.run_textual = AsyncMock()
        mock_vibecore.workflow = MagicMock(return_value=lambda f: f)  # Decorator passthrough
        mock_vibecore.user_input = AsyncMock(side_effect=Exception("Should not be called in mocked run_textual"))
        mock_vibecore.run_agent = AsyncMock(side_effect=Exception("Should not be called in mocked run_textual"))
        mock_vibecore_class.return_value = mock_vibecore
        # Handle generic type syntax Vibecore[Type1, Type2](...)
        mock_vibecore_class.__getitem__.return_value = mock_vibecore_class

        # Mock MCPManager context manager
        mock_mcp_manager = MagicMock()
        mock_mcp_manager.servers = []
        mock_mcp_manager_class.return_value.__aenter__ = AsyncMock(return_value=mock_mcp_manager)
        mock_mcp_manager_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock JSONLSession
        mock_session = MagicMock()
        mock_jsonl_class.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(app, ["--continue"])

        assert result.exit_code == 0
        assert "Continuing session: chat-20250124-150000" in result.stdout
        # Verify session was created with correct ID
        mock_jsonl_class.assert_called_once()
        call_kwargs = mock_jsonl_class.call_args.kwargs
        assert call_kwargs["session_id"] == "chat-20250124-150000"
        # Verify run_textual was called with prompt (None), context, and session
        mock_vibecore.run_textual.assert_called_once_with(None, context=ANY, session=mock_session)

    @patch("vibecore.cli.JSONLSession")
    @patch("vibecore.cli.Vibecore")
    @patch("vibecore.cli.MCPManager")
    def test_cli_specific_session(self, mock_mcp_manager_class, mock_vibecore_class, mock_jsonl_class):
        """Test --session with specific session ID."""
        # Mock the vibecore instance with async methods
        mock_vibecore = MagicMock()
        mock_vibecore.run_textual = AsyncMock()
        mock_vibecore.workflow = MagicMock(return_value=lambda f: f)  # Decorator passthrough
        mock_vibecore.user_input = AsyncMock(side_effect=Exception("Should not be called in mocked run_textual"))
        mock_vibecore.run_agent = AsyncMock(side_effect=Exception("Should not be called in mocked run_textual"))
        mock_vibecore_class.return_value = mock_vibecore
        # Handle generic type syntax Vibecore[Type1, Type2](...)
        mock_vibecore_class.__getitem__.return_value = mock_vibecore_class

        # Mock MCPManager context manager
        mock_mcp_manager = MagicMock()
        mock_mcp_manager.servers = []
        mock_mcp_manager_class.return_value.__aenter__ = AsyncMock(return_value=mock_mcp_manager)
        mock_mcp_manager_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock JSONLSession
        mock_session = MagicMock()
        mock_jsonl_class.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(app, ["--session", "chat-custom-123"])

        assert result.exit_code == 0
        assert "Loading session: chat-custom-123" in result.stdout
        # Verify session was created with correct ID
        mock_jsonl_class.assert_called_once()
        call_kwargs = mock_jsonl_class.call_args.kwargs
        assert call_kwargs["session_id"] == "chat-custom-123"
        # Verify run_textual was called with prompt (None), context, and session
        mock_vibecore.run_textual.assert_called_once_with(None, context=ANY, session=mock_session)

    @patch("vibecore.cli.JSONLSession")
    @patch("vibecore.cli.Vibecore")
    @patch("vibecore.cli.MCPManager")
    def test_cli_no_options(self, mock_mcp_manager_class, mock_vibecore_class, mock_jsonl_class):
        """Test running without any options (new session)."""
        # Mock the vibecore instance with async methods
        mock_vibecore = MagicMock()
        mock_vibecore.run_textual = AsyncMock()
        mock_vibecore.workflow = MagicMock(return_value=lambda f: f)  # Decorator passthrough
        mock_vibecore.user_input = AsyncMock(side_effect=Exception("Should not be called in mocked run_textual"))
        mock_vibecore.run_agent = AsyncMock(side_effect=Exception("Should not be called in mocked run_textual"))
        mock_vibecore_class.return_value = mock_vibecore
        # Handle generic type syntax Vibecore[Type1, Type2](...)
        mock_vibecore_class.__getitem__.return_value = mock_vibecore_class

        # Mock MCPManager context manager
        mock_mcp_manager = MagicMock()
        mock_mcp_manager.servers = []
        mock_mcp_manager_class.return_value.__aenter__ = AsyncMock(return_value=mock_mcp_manager)
        mock_mcp_manager_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock JSONLSession
        mock_session = MagicMock()
        mock_jsonl_class.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(app, [])

        assert result.exit_code == 0
        # Check that a new session was created (with auto-generated timestamp-based ID)
        mock_jsonl_class.assert_called_once()
        call_kwargs = mock_jsonl_class.call_args.kwargs
        # Session ID should start with "chat-" for new sessions
        assert call_kwargs["session_id"].startswith("chat-")
        # Verify run_textual was called with prompt (None), context, and session
        mock_vibecore.run_textual.assert_called_once_with(None, context=ANY, session=mock_session)
