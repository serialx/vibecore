"""Unit tests for AnthropicModel."""

import copy
from unittest.mock import AsyncMock, patch

import pytest
from litellm.types.utils import ModelResponse

from vibecore.models import AnthropicModel
from vibecore.models.anthropic import _transform_messages_for_cache


class TestAnthropicModel:
    """Test suite for AnthropicModel."""

    def test_model_initialization(self):
        """Test that AnthropicModel initializes correctly."""
        model = AnthropicModel("anthropic/claude-3-5-sonnet-20241022")
        assert model.model == "anthropic/claude-3-5-sonnet-20241022"

    def test_transform_system_message_string(self):
        """Test that a single system message is cached (it's both last message and last system)."""
        messages = [{"role": "system", "content": "You are a helpful assistant."}]

        transformed = _transform_messages_for_cache(messages)

        assert len(transformed) == 1
        assert transformed[0]["role"] == "system"
        # Should be cached as it's both the last message and last system message
        assert isinstance(transformed[0]["content"], list)
        assert len(transformed[0]["content"]) == 1
        assert transformed[0]["content"][0]["type"] == "text"
        assert transformed[0]["content"][0]["text"] == "You are a helpful assistant."
        assert transformed[0]["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_transform_system_message_list(self):
        """Test that system messages with list content are transformed correctly."""
        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are helpful."}, {"type": "text", "text": "Be concise."}],
            }
        ]

        transformed = _transform_messages_for_cache(messages)

        assert len(transformed) == 1
        assert transformed[0]["role"] == "system"
        assert isinstance(transformed[0]["content"], list)
        assert len(transformed[0]["content"]) == 2

        # Only first text item should have cache_control
        assert transformed[0]["content"][0]["cache_control"] == {"type": "ephemeral"}
        assert "cache_control" not in transformed[0]["content"][1]

    def test_transform_single_user_message(self):
        """Test that a single user message is cached (as last message)."""
        messages = [{"role": "user", "content": "Hello"}]

        transformed = _transform_messages_for_cache(messages)

        assert len(transformed) == 1
        assert transformed[0]["role"] == "user"
        # Should be cached as it's the last message
        assert isinstance(transformed[0]["content"], list)
        assert transformed[0]["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_transform_user_assistant_pattern(self):
        """Test typical user-assistant conversation pattern."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        transformed = _transform_messages_for_cache(messages)

        assert len(transformed) == 2
        # First message (user) should NOT be cached in this case
        # (only the message BEFORE a user message gets cached, not the user message itself)
        assert transformed[0]["content"] == "Hello"
        # Last message should be cached
        assert isinstance(transformed[1]["content"], list)
        assert transformed[1]["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_max_four_cache_breakpoints(self):
        """Test that we never exceed 4 cache breakpoints."""
        # Create a long conversation with many user messages
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "3"},
            {"role": "assistant", "content": "Response 3"},
            {"role": "user", "content": "4"},
            {"role": "assistant", "content": "Response 4"},
            {"role": "user", "content": "5"},
            {"role": "assistant", "content": "Response 5"},
        ]

        transformed = _transform_messages_for_cache(messages)

        # Count messages with cache_control
        cached_count = 0
        cached_indices = []
        for i, msg in enumerate(transformed):
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "cache_control" in item:
                        cached_count += 1
                        cached_indices.append(i)
                        break

        assert cached_count <= 4, f"Expected at most 4 cached messages, got {cached_count}"
        # Should cache: system (0), assistant before user 4 (6), assistant before user 5 (8), last message (10)
        assert cached_indices == [0, 6, 8, 10]

    def test_transform_assistant_message(self):
        """Test that a single assistant message is cached as the last message."""
        messages = [{"role": "assistant", "content": "Here is my response."}]

        transformed = _transform_messages_for_cache(messages)

        assert len(transformed) == 1
        # Should be cached as it's the last message
        assert isinstance(transformed[0]["content"], list)
        assert transformed[0]["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_transform_mixed_messages(self):
        """Test transformation of mixed message types."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
            {"role": "assistant", "content": "Second answer"},
        ]

        transformed = _transform_messages_for_cache(messages)

        assert len(transformed) == 5

        # Check which messages are cached
        # System message (last system)
        assert isinstance(transformed[0]["content"], list)
        assert transformed[0]["content"][0]["cache_control"] == {"type": "ephemeral"}

        # First answer (before second-to-last user)
        assert isinstance(transformed[2]["content"], list)
        assert transformed[2]["content"][0]["cache_control"] == {"type": "ephemeral"}

        # Second answer (last message)
        assert isinstance(transformed[4]["content"], list)
        assert transformed[4]["content"][0]["cache_control"] == {"type": "ephemeral"}

        # User messages should not be cached
        assert transformed[1]["content"] == "First question"
        assert transformed[3]["content"] == "Second question"

    def test_preserve_existing_cache_control(self):
        """Test that existing cache_control is preserved."""
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "System prompt",
                        "cache_control": {"type": "custom"},  # Existing cache control
                    }
                ],
            }
        ]

        transformed = _transform_messages_for_cache(messages)

        # Should preserve existing cache_control
        assert transformed[0]["content"][0]["cache_control"] == {"type": "custom"}

    def test_handle_non_text_content(self):
        """Test handling of non-text content items."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "x" * 1500},
                    {"type": "image", "source": {"data": "base64data"}},  # Non-text item
                ],
            }
        ]

        transformed = _transform_messages_for_cache(messages)

        assert len(transformed[0]["content"]) == 2
        # Text item should be cached
        assert transformed[0]["content"][0]["cache_control"] == {"type": "ephemeral"}
        # Image item should be unchanged
        assert transformed[0]["content"][1] == {"type": "image", "source": {"data": "base64data"}}

    def test_original_messages_not_modified(self):
        """Test that original messages are not modified during transformation."""
        original_messages = [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "x" * 1500}]

        # Make a copy to compare later
        messages_copy = copy.deepcopy(original_messages)

        # Transform messages
        _transform_messages_for_cache(original_messages)

        # Original should be unchanged
        assert original_messages == messages_copy

    @pytest.mark.asyncio
    async def test_anthropic_model_fetch_response(self):
        """Test that AnthropicModel transforms messages when calling _fetch_response."""
        model = AnthropicModel("anthropic/claude-3-5-sonnet")

        # Mock litellm.acompletion to verify transformed messages
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            # Set up mock return value
            mock_response = ModelResponse()
            mock_response.choices = []
            mock_acompletion.return_value = mock_response

            # Create minimal required objects for _fetch_response
            from unittest.mock import MagicMock

            from agents.model_settings import ModelSettings
            from agents.models.interface import ModelTracing

            model_settings = ModelSettings()
            tracing = ModelTracing.DISABLED
            span = MagicMock()  # Mock the span object
            span.span_data = MagicMock()

            # Call _fetch_response
            from typing import cast

            from agents.items import TResponseInputItem

            input_items = cast(
                list[TResponseInputItem],
                [
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "Hello"},
                ],
            )

            await model._fetch_response(
                system_instructions=None,
                input=input_items,
                model_settings=model_settings,
                tools=[],
                output_schema=None,
                handoffs=[],
                span=span,
                tracing=tracing,
                stream=False,
            )

            # Verify litellm.acompletion was called with transformed messages
            mock_acompletion.assert_called_once()
            call_kwargs = mock_acompletion.call_args.kwargs

            # System message should be transformed (last system)
            assert isinstance(call_kwargs["messages"][0]["content"], list)
            assert call_kwargs["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}

            # User message should be transformed (last message)
            assert isinstance(call_kwargs["messages"][1]["content"], list)
            assert call_kwargs["messages"][1]["content"][0]["cache_control"] == {"type": "ephemeral"}

    @pytest.mark.asyncio
    async def test_anthropic_model_with_list_content(self):
        """Test AnthropicModel handles messages with list content."""
        model = AnthropicModel("anthropic/claude-3-5-sonnet")

        # Mock litellm.acompletion
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            # Set up mock return value
            mock_response = ModelResponse()
            mock_response.choices = []
            mock_acompletion.return_value = mock_response

            # Create minimal required objects
            from unittest.mock import MagicMock

            from agents.model_settings import ModelSettings
            from agents.models.interface import ModelTracing

            model_settings = ModelSettings()
            tracing = ModelTracing.DISABLED
            span = MagicMock()  # Mock the span object
            span.span_data = MagicMock()

            # Call with list content - using the correct format expected by Converter
            from typing import cast

            from agents.items import TResponseInputItem

            input_items = cast(
                list[TResponseInputItem],
                [
                    {
                        "role": "system",
                        "content": [
                            {"type": "input_text", "text": "Be helpful"},
                            {"type": "input_text", "text": "Be concise"},
                        ],
                    }
                ],
            )

            await model._fetch_response(
                system_instructions=None,
                input=input_items,
                model_settings=model_settings,
                tools=[],
                output_schema=None,
                handoffs=[],
                span=span,
                tracing=tracing,
                stream=False,
            )

            # Only first text item should have cache_control
            mock_acompletion.assert_called_once()
            call_kwargs = mock_acompletion.call_args.kwargs
            # First text item should have cache_control
            assert call_kwargs["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}
            # Second text item should NOT have cache_control
            assert "cache_control" not in call_kwargs["messages"][0]["content"][1]

    def test_cache_priority_with_tool_results(self):
        """Test caching priority with tool results before user messages."""
        messages = [
            {"role": "system", "content": "You are a coding assistant."},
            {"role": "user", "content": "Read the file"},
            {"role": "assistant", "content": "I'll read the file for you."},
            {"role": "tool", "content": "File contents: large data..."},  # Tool result
            {"role": "user", "content": "Fix the bug"},
            {"role": "assistant", "content": "I'll fix it."},
            {"role": "tool", "content": "File edited successfully"},  # Tool result
            {"role": "user", "content": "Run tests"},
            {"role": "assistant", "content": "Running tests now."},
        ]

        transformed = _transform_messages_for_cache(messages)

        # Count cached messages
        cached_indices = []
        for i, msg in enumerate(transformed):
            content = msg.get("content")
            if isinstance(content, list) and any("cache_control" in item for item in content if isinstance(item, dict)):
                cached_indices.append(i)

        # Should cache: system (0), tool result before user "Fix the bug" (3),
        # tool result before user "Run tests" (6), last message (8)
        assert cached_indices == [0, 3, 6, 8]

    def test_cache_last_message_always(self):
        """Test that the last message is always cached."""
        # Test with various last message types
        test_cases = [
            [{"role": "user", "content": "Hello"}],
            [{"role": "assistant", "content": "Hi"}],
            [{"role": "system", "content": "System"}, {"role": "tool", "content": "Result"}],
        ]

        for messages in test_cases:
            transformed = _transform_messages_for_cache(messages)
            last_msg = transformed[-1]
            assert isinstance(last_msg["content"], list), f"Last message not cached for {messages}"
            assert last_msg["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_cache_with_no_user_messages(self):
        """Test caching when there are no user messages."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "assistant", "content": "How can I help you today?"},
        ]

        transformed = _transform_messages_for_cache(messages)

        # Should cache system (last system) and last message
        assert isinstance(transformed[0]["content"], list)
        assert transformed[0]["content"][0]["cache_control"] == {"type": "ephemeral"}
        assert isinstance(transformed[1]["content"], list)
        assert transformed[1]["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_cache_empty_messages(self):
        """Test caching with empty message list."""
        messages = []
        transformed = _transform_messages_for_cache(messages)
        assert transformed == []

    def test_cache_with_empty_text_content(self):
        """Test that empty text content is not cached to avoid 'cache_control cannot be set for empty text' error."""
        # Test with empty string content
        messages = [
            {"role": "system", "content": ""},  # Empty string
            {"role": "user", "content": "Hello"},
        ]

        transformed = _transform_messages_for_cache(messages)

        # Empty string should not be cached - should remain as string
        assert transformed[0]["content"] == ""
        # User message should be cached as last message
        assert isinstance(transformed[1]["content"], list)
        assert transformed[1]["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_cache_with_empty_text_in_list(self):
        """Test that empty text in list content is not cached."""
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": ""},  # Empty text
                    {"type": "text", "text": "Not empty"},
                ],
            }
        ]

        transformed = _transform_messages_for_cache(messages)

        # Empty text should not have cache_control
        assert "cache_control" not in transformed[0]["content"][0]
        # Non-empty text should have cache_control (as it's the first non-empty text)
        assert transformed[0]["content"][1]["cache_control"] == {"type": "ephemeral"}

    def test_cache_with_mixed_empty_and_nonempty_text(self):
        """Test caching with multiple text items, some empty and some non-empty."""
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": ""},  # Empty
                    {"type": "text", "text": ""},  # Empty
                    {"type": "text", "text": "First non-empty"},  # Should get cache_control
                    {"type": "text", "text": "Second non-empty"},  # Should NOT get cache_control
                ],
            },
            {"role": "user", "content": ""},  # Empty user message
            {"role": "assistant", "content": "Response"},  # Non-empty response (last message)
        ]

        transformed = _transform_messages_for_cache(messages)

        # First two empty texts should not have cache_control
        assert "cache_control" not in transformed[0]["content"][0]
        assert "cache_control" not in transformed[0]["content"][1]
        # First non-empty text should have cache_control
        assert transformed[0]["content"][2]["cache_control"] == {"type": "ephemeral"}
        # Second non-empty text should NOT have cache_control (only first gets it)
        assert "cache_control" not in transformed[0]["content"][3]
        # Empty user message should remain as string
        assert transformed[1]["content"] == ""
        # Assistant message should be cached (last message)
        assert isinstance(transformed[2]["content"], list)
        assert transformed[2]["content"][0]["cache_control"] == {"type": "ephemeral"}

    @pytest.mark.asyncio
    async def test_anthropic_model_streaming(self):
        """Test that AnthropicModel works correctly with streaming."""
        model = AnthropicModel("anthropic/claude-3-5-sonnet")

        # Mock litellm.acompletion to verify it's called with stream=True
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            # Set up mock return value for streaming
            mock_stream = AsyncMock()
            mock_acompletion.return_value = mock_stream

            # Create minimal required objects
            from typing import cast
            from unittest.mock import MagicMock

            from agents.items import TResponseInputItem
            from agents.model_settings import ModelSettings
            from agents.models.interface import ModelTracing

            model_settings = ModelSettings()
            tracing = ModelTracing.DISABLED
            span = MagicMock()
            span.span_data = MagicMock()

            input_items = cast(
                list[TResponseInputItem],
                [
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ],
            )

            await model._fetch_response(
                system_instructions=None,
                input=input_items,
                model_settings=model_settings,
                tools=[],
                output_schema=None,
                handoffs=[],
                span=span,
                tracing=tracing,
                stream=True,  # Test streaming
            )

            # Verify litellm.acompletion was called with stream=True
            mock_acompletion.assert_called_once()
            call_kwargs = mock_acompletion.call_args.kwargs
            assert call_kwargs["stream"] is True

            # Verify message transformation happened
            # System message should be cached (both last system and message before user at index 1)
            assert isinstance(call_kwargs["messages"][0]["content"], list)
            assert call_kwargs["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}
            # User message should NOT be cached
            assert call_kwargs["messages"][1]["content"] == "Hello"
            # Assistant message should be cached (last message)
            assert isinstance(call_kwargs["messages"][2]["content"], list)
            assert call_kwargs["messages"][2]["content"][0]["cache_control"] == {"type": "ephemeral"}
