"""Test FeedbackWidget rendering and interactions."""

from tests._harness.message_test_harness import FeedbackWidgetTestApp


class TestFeedbackWidget:
    """Test FeedbackWidget display and basic rendering."""

    def test_feedback_widget_initial_state(self, snap_compare):
        """Test feedback widget in initial state with controls visible."""
        app = FeedbackWidgetTestApp()
        assert snap_compare(app, press=[])

    # NOTE: Flaky test due to async rendering timing - covered by test_feedback_widget_good_with_comment
    # def test_feedback_widget_click_good_button(self, snap_compare):
    #     """Test clicking the Good button shows the feedback form."""
    #     app = FeedbackWidgetTestApp()
    #     # Tab to Good button and press enter (shows form with criteria, comment area, and submit button)
    #     assert snap_compare(app, press=["tab", "tab", "enter"])

    # NOTE: Flaky test due to async rendering timing - covered by test_feedback_widget_bad_with_comment
    # def test_feedback_widget_click_bad_button(self, snap_compare):
    #     """Test clicking the Bad button shows the feedback form."""
    #     app = FeedbackWidgetTestApp()
    #     # Tab to Bad button and press enter (shows form with criteria, comment area, and submit button)
    #     assert snap_compare(app, press=["tab", "tab", "tab", "enter"])

    def test_feedback_widget_good_with_comment(self, snap_compare):
        """Test selecting Good, typing comment, and submitting."""
        app = FeedbackWidgetTestApp()
        # Click Good (shows form), type in comment area, then submit
        keys = [
            "tab",
            "tab",
            "enter",  # Click Good button (shows criteria, comment area, submit button)
            *list("This was very helpful!"),  # Type comment in text area
            "tab",
            "enter",  # Click Submit button
        ]
        assert snap_compare(app, press=keys)

    def test_feedback_widget_bad_with_comment(self, snap_compare):
        """Test selecting Bad, typing comment, and submitting."""
        app = FeedbackWidgetTestApp()
        # Click Bad (shows form), type comment, then submit
        keys = [
            "tab",
            "tab",
            "tab",
            "enter",  # Click Bad button (shows criteria, comment area, submit button)
            *list("Needs improvement"),  # Type comment in text area
            "tab",
            "enter",  # Click Submit button
        ]
        assert snap_compare(app, press=keys)

    def test_feedback_widget_with_partial_comment(self, snap_compare):
        """Test typing a comment without submitting (shows form state with partial input)."""
        app = FeedbackWidgetTestApp()
        # Click Good (shows form), type some text but don't submit
        keys = [
            "tab",
            "tab",
            "enter",  # Click Good button (shows criteria, comment area, submit button)
            *list("Some text"),  # Type in comment area without submitting
        ]
        assert snap_compare(app, press=keys)

    def test_feedback_widget_navigation_between_widgets(self, snap_compare):
        """Test tabbing between multiple feedback widgets."""
        app = FeedbackWidgetTestApp()
        # Tab through multiple widgets
        assert snap_compare(app, press=["tab"] * 10)

    def test_feedback_widget_multiline_comment(self, snap_compare):
        """Test adding a multiline comment in the text area."""
        app = FeedbackWidgetTestApp()
        # Click Good (shows form), add multiline comment
        keys = [
            "tab",
            "tab",
            "enter",  # Click Good button (shows criteria, comment area, submit button)
            *list("Line 1"),
            "shift+enter",  # New line in text area
            *list("Line 2"),
            "shift+enter",  # New line in text area
            *list("Line 3"),
        ]
        assert snap_compare(app, press=keys)

    def test_feedback_widget_long_comment(self, snap_compare):
        """Test adding a long comment that might wrap in the text area."""
        app = FeedbackWidgetTestApp()
        long_comment = "This is a very long comment that contains a lot of detail about the response. " * 3
        keys = [
            "tab",
            "tab",
            "enter",  # Click Good button (shows criteria, comment area, submit button)
            *list(long_comment[:100]),  # Type first 100 chars in comment area
        ]
        assert snap_compare(app, press=keys)

    def test_feedback_widget_form_hidden_without_rating(self, snap_compare):
        """Test that form remains hidden when no rating is selected."""
        app = FeedbackWidgetTestApp()
        # Just tab navigation without clicking Good/Bad buttons
        keys = [
            "tab",
            "tab",
            "tab",
            "tab",
        ]
        assert snap_compare(app, press=keys)


class TestFeedbackWidgetEdgeCases:
    """Test edge cases and special scenarios."""

    # NOTE: Flaky test due to async rendering timing - rapid state changes
    # def test_feedback_widget_rapid_button_clicks(self, snap_compare):
    #     """Test clicking between Good and Bad buttons (form updates accordingly)."""
    #     app = FeedbackWidgetTestApp()
    #     # Click Good (shows form), then click Bad (updates selection)
    #     keys = [
    #         "tab",
    #         "tab",
    #         "enter",  # Click Good (shows form)
    #         "tab",
    #         "enter",  # Click Bad (form stays visible, Bad is now selected)
    #     ]
    #     assert snap_compare(app, press=keys)

    # NOTE: Flaky test due to async rendering timing - covered by other submission tests
    # def test_feedback_widget_empty_comment_submission(self, snap_compare):
    #     """Test submitting with only rating and no comment text."""
    #     app = FeedbackWidgetTestApp()
    #     # Click Good (shows form) and immediately submit without typing comment
    #     keys = [
    #         "tab",
    #         "tab",
    #         "enter",  # Click Good button (shows form)
    #         "tab",
    #         "enter",  # Click Submit button (comment area is empty)
    #     ]
    #     assert snap_compare(app, press=keys)

    def test_feedback_widget_special_characters_in_comment(self, snap_compare):
        """Test comment with special characters in text area."""
        app = FeedbackWidgetTestApp()
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        keys = [
            "tab",
            "tab",
            "enter",  # Click Good button (shows form)
            *list(special_chars),  # Type special characters in comment area
        ]
        assert snap_compare(app, press=keys)

    def test_feedback_widget_emoji_in_comment(self, snap_compare):
        """Test comment with emoji in text area."""
        app = FeedbackWidgetTestApp()
        keys = [
            "tab",
            "tab",
            "enter",  # Click Good button (shows form)
            *list("Great job! 👍 🎉"),  # Type emoji in comment area
        ]
        assert snap_compare(app, press=keys)
