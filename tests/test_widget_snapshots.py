"""Snapshot tests for vibecore widget rendering."""


from tests.test_harness import create_test_app


class TestWidgetSnapshots:
    """Test widget rendering using snapshot testing."""

    def test_empty_app(self, snap_compare):
        """Test empty app shows Welcome widget."""
        app = create_test_app()
        assert snap_compare(app, press=[])

    def test_basic_conversation(self, snap_compare):
        """Test basic user-assistant conversation rendering."""
        app = create_test_app("basic_conversation.jsonl")
        assert snap_compare(app, press=[])

    def test_tool_usage_bash(self, snap_compare):
        """Test Bash tool message rendering."""
        app = create_test_app("tool_usage_bash.jsonl")
        assert snap_compare(app, press=[])

    def test_tool_usage_read(self, snap_compare):
        """Test Read tool with expandable content."""
        app = create_test_app("tool_usage_read.jsonl")
        # Test both collapsed and expanded states
        assert snap_compare(app, press=[])
        # TODO: Add test for expanded state once we figure out how to trigger it

    def test_tool_usage_python(self, snap_compare):
        """Test Python tool message rendering."""
        app = create_test_app("tool_usage_python.jsonl")
        assert snap_compare(app, press=[])

    def test_tool_usage_todo(self, snap_compare):
        """Test TodoWrite tool message rendering."""
        app = create_test_app("tool_usage_todo.jsonl")
        assert snap_compare(app, press=[])


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_session(self, snap_compare):
        """Test loading an empty session file."""
        app = create_test_app("empty.jsonl")
        assert snap_compare(app, press=[])
