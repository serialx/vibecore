"""Anthropic model implementation with automatic cache control."""

import json
import logging
from typing import Any, Literal, overload

import litellm
from agents.agent_output import AgentOutputSchemaBase
from agents.extensions.models.litellm_model import LitellmModel
from agents.handoffs import Handoff
from agents.items import TResponseInputItem
from agents.model_settings import ModelSettings
from agents.models.interface import ModelTracing
from agents.tool import Tool
from agents.tracing.span_data import GenerationSpanData
from agents.tracing.spans import Span
from openai import AsyncStream
from openai.types.chat import ChatCompletionChunk
from openai.types.responses import Response

# Set up debug logging
logger = logging.getLogger(__name__)


def _transform_messages_for_cache(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transform messages to add cache_control for Anthropic models.

    Caches up to 4 messages in priority order:
    1. Last message
    2. Message before last user message (often tool result)
    3. Message before second-to-last user message (often tool result)
    4. Last system message

    Args:
        messages: List of message dictionaries

    Returns:
        Transformed messages with cache_control added
    """
    if not messages:
        return []

    indices_to_cache = set()

    # 1. Always cache the last message
    indices_to_cache.add(len(messages) - 1)

    # 2. Find user messages going backwards
    user_message_indices = []
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            user_message_indices.append(i)

    # 3. Cache message before the last user message (if exists)
    # This is often a tool result which contains important context
    if len(user_message_indices) >= 1 and user_message_indices[0] > 0:
        indices_to_cache.add(user_message_indices[0] - 1)

    # 4. Cache message before the second-to-last user message (if exists)
    # This is also often a tool result
    if len(user_message_indices) >= 2 and user_message_indices[1] > 0:
        indices_to_cache.add(user_message_indices[1] - 1)

    # 5. Find and cache the last system message
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "system":
            indices_to_cache.add(i)
            break

    # Transform messages with cache_control only for selected indices
    transformed = []
    for i, msg in enumerate(messages):
        new_msg = msg.copy()

        if i in indices_to_cache:
            # Add cache_control to this message
            content = new_msg.get("content")

            if isinstance(content, str):
                # Only add cache_control if text is not empty
                if content:
                    # Convert string content to list format with cache_control
                    new_msg["content"] = [{"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}]
                # else: keep empty string as is, don't convert to list format
            elif isinstance(content, list):
                # Add cache_control to first text item if not already present
                new_content = []
                cache_added = False

                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text" and not cache_added:
                        # Only add cache_control if text is not empty
                        text_content = item.get("text", "")
                        if text_content and "cache_control" not in item:
                            # Add cache_control to the first non-empty text item without cache_control
                            new_item = item.copy()
                            new_item["cache_control"] = {"type": "ephemeral"}
                            new_content.append(new_item)
                            cache_added = True
                        elif text_content and "cache_control" in item:
                            # Non-empty item already has cache_control
                            new_content.append(item)
                            cache_added = True
                        else:
                            # Empty text or already has cache_control - keep as is
                            new_content.append(item)
                    else:
                        new_content.append(item)

                new_msg["content"] = new_content

        transformed.append(new_msg)

    return transformed


class AnthropicModel(LitellmModel):
    """Anthropic model that automatically adds cache_control to messages.

    This implementation minimally overrides the _fetch_response method to intercept
    and transform messages before they're sent to the Anthropic API.

    The override approach:
    1. Temporarily replaces litellm.acompletion with an intercepting function
    2. The interceptor transforms messages only for this specific model
    3. Calls the parent's _fetch_response which uses the interceptor
    4. Always restores the original function, even if an error occurs

    This minimal approach ensures compatibility with upstream LitellmModel changes
    while adding the necessary cache_control functionality for Anthropic models.
    """

    def __init__(self, model_name: str, base_url: str | None = None, api_key: str | None = None):
        """Initialize AnthropicModel."""
        super().__init__(model_name, base_url, api_key)
        logger.debug(f"AnthropicModel initialized with model: {model_name}")

    @overload
    async def _fetch_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        span: Span[GenerationSpanData],
        tracing: ModelTracing,
        stream: Literal[True],
        prompt: Any | None = None,
    ) -> tuple[Response, AsyncStream[ChatCompletionChunk]]: ...

    @overload
    async def _fetch_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        span: Span[GenerationSpanData],
        tracing: ModelTracing,
        stream: Literal[False],
        prompt: Any | None = None,
    ) -> Any: ...  # litellm.ModelResponse

    async def _fetch_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        span: Span[GenerationSpanData],
        tracing: ModelTracing,
        stream: bool = False,
        prompt: Any | None = None,
    ) -> Any | tuple[Response, AsyncStream[ChatCompletionChunk]]:
        """Override _fetch_response to add cache_control to messages."""
        # Store the original litellm.acompletion function
        original_acompletion = litellm.acompletion

        async def _intercepting_acompletion(*args, **kwargs):
            """Intercept litellm.acompletion calls to transform messages."""
            # Only transform messages for this Anthropic model
            if kwargs.get("model") == self.model and "messages" in kwargs:
                messages = kwargs["messages"]
                logger.debug(f"Intercepting Anthropic API call for model {self.model} with {len(messages)} messages")

                # Transform messages to add cache_control
                transformed = _transform_messages_for_cache(messages)
                kwargs["messages"] = transformed

                # Log transformation for debugging
                if logger.isEnabledFor(logging.DEBUG):
                    for i, (orig, trans) in enumerate(zip(messages[:2], transformed[:2], strict=False)):
                        logger.debug(f"Message {i} transformation:")
                        logger.debug(f"  Original: {json.dumps(orig, indent=2)}")
                        logger.debug(f"  Transformed: {json.dumps(trans, indent=2)}")

            # Call the original function with potentially transformed kwargs
            return await original_acompletion(*args, **kwargs)

        try:
            # Temporarily replace litellm.acompletion with our intercepting version
            litellm.acompletion = _intercepting_acompletion

            # Call the parent's implementation, which will use our intercepting function
            if stream:
                return await super()._fetch_response(
                    system_instructions=system_instructions,
                    input=input,
                    model_settings=model_settings,
                    tools=tools,
                    output_schema=output_schema,
                    handoffs=handoffs,
                    span=span,
                    tracing=tracing,
                    stream=True,
                    prompt=prompt,
                )
            else:
                return await super()._fetch_response(
                    system_instructions=system_instructions,
                    input=input,
                    model_settings=model_settings,
                    tools=tools,
                    output_schema=output_schema,
                    handoffs=handoffs,
                    span=span,
                    tracing=tracing,
                    stream=False,
                    prompt=prompt,
                )
        finally:
            # Always restore the original function
            litellm.acompletion = original_acompletion
