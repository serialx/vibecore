"""Test keyboard interactions and key bindings in vibecore."""

from pathlib import Path

from tests.test_harness import create_test_app


class TestKeyboardInteractions:
    """Test keyboard shortcuts and interactions."""

    def test_toggle_dark_mode(self, snap_compare):
        """Test that Ctrl+Shift+D toggles dark mode."""
        app = create_test_app()
        # Press Ctrl+Shift+D to toggle
        assert snap_compare(app, press=["ctrl+shift+d"])

    def test_ctrl_d_exit_confirmation(self, snap_compare):
        """Test that Ctrl+D shows exit confirmation."""
        app = create_test_app()
        # Press Ctrl+D for exit confirmation
        assert snap_compare(app, press=["ctrl+d"])

    def test_typing_in_input(self, snap_compare):
        """Test typing text in the input area."""
        app = create_test_app()
        # Type "Hello World"
        keys = list("Hello World")
        assert snap_compare(app, press=keys)

    def test_multiline_input_with_shift_enter(self, snap_compare):
        """Test that Shift+Enter creates multiline input."""
        app = create_test_app()
        # Type first line, press Shift+Enter, type second line
        keys = [*list("Line 1"), "shift+enter", *list("Line 2")]
        assert snap_compare(app, press=keys)

    def test_navigation_keys(self, snap_compare):
        """Test navigation keys in the input field."""
        app = create_test_app()
        # Type text, then use arrow keys to navigate
        keys = [*list("Hello"), "left", "left", "left", *list("123")]
        assert snap_compare(app, press=keys)

    def test_select_all_and_delete(self, snap_compare):
        """Test selecting all text and deleting."""
        app = create_test_app()
        # Type text, select all with F7, then delete
        keys = [*list("Test text"), "f7", "delete"]
        assert snap_compare(app, press=keys)

    def test_scroll_with_keyboard(self, snap_compare):
        """Test scrolling messages with keyboard."""
        # Use a conversation fixture with many messages if available
        fixture_path = Path(__file__).parent / "fixtures" / "sessions" / "tool_usage_todo.jsonl"
        app = create_test_app("tool_usage_todo.jsonl") if fixture_path.exists() else create_test_app()

        # Test scroll keys
        keys = ["tab", "pagedown"]
        assert snap_compare(app, press=keys)

    def test_tab_navigation(self, snap_compare):
        """Test Tab key navigation between focusable elements."""
        app = create_test_app()
        # Press Tab and Shift+Tab to navigate
        keys = ["tab"]
        assert snap_compare(app, press=keys)


class TestComplexKeySequences:
    """Test complex keyboard interaction sequences."""

    def test_edit_and_send_message(self, snap_compare):
        """Test editing a message before sending."""
        app = create_test_app()
        # Type, navigate back, insert text, then send
        keys = [*list("H!"), "left", "i", "end", "enter"]
        assert snap_compare(app, press=keys)

    def test_copy_paste_workflow(self, snap_compare):
        """Test copy and paste workflow."""
        app = create_test_app()
        # Type text, select all, copy, space, paste
        keys = [*list("Copy")] + ["shift+left"] * 4 + ["ctrl+c", "right", "space", "ctrl+v"]
        assert snap_compare(app, press=keys)

    def test_undo_redo(self, snap_compare):
        """Test undo and redo operations."""
        app = create_test_app()
        # Type text, undo, redo
        keys = [*list("Test undo"), "ctrl+z", "ctrl+z", "ctrl+shift+z"]
        assert snap_compare(app, press=keys)

    def test_special_characters(self, snap_compare):
        """Test typing special characters."""
        app = create_test_app()
        # Type various special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        keys = list(special_chars)
        assert snap_compare(app, press=keys)


class TestKeyBindingEdgeCases:
    """Test edge cases and error conditions for key bindings."""

    def test_escape_without_active_agent(self, snap_compare):
        """Test Escape key when no agent is running."""
        app = create_test_app()
        # Press Escape when idle (should have no effect)
        keys = ["escape"]
        assert snap_compare(app, press=keys)

    def test_empty_input_enter(self, snap_compare):
        """Test pressing Enter with empty input."""
        app = create_test_app()
        # Press Enter without typing anything
        keys = ["enter"]
        assert snap_compare(app, press=keys)
