"""Anthropic model with Pro/Max authentication support."""

import logging
from typing import Any, Literal, overload

import litellm
from agents.agent_output import AgentOutputSchemaBase
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

from vibecore.auth.config import ANTHROPIC_CONFIG
from vibecore.auth.interceptor import AnthropicRequestInterceptor
from vibecore.auth.manager import AnthropicAuthManager
from vibecore.auth.storage import SecureAuthStorage
from vibecore.models.anthropic import AnthropicModel, _transform_messages_for_cache

logger = logging.getLogger(__name__)


class AnthropicProMaxModel(AnthropicModel):
    """Anthropic model with Pro/Max authentication and Claude Code spoofing."""

    def __init__(self, model_name: str, base_url: str | None = None, api_key: str | None = None, use_auth: bool = True):
        """
        Initialize AnthropicProMaxModel.

        Args:
            model_name: Name of the model.
            base_url: Optional base URL override.
            api_key: Optional API key (ignored if Pro/Max auth is active).
            use_auth: Whether to use Pro/Max authentication.
        """
        super().__init__(model_name, base_url, api_key)
        self.use_auth = use_auth
        self.auth_manager: AnthropicAuthManager | None = None
        self.interceptor: AnthropicRequestInterceptor | None = None

        if self.use_auth:
            self._initialize_auth()

    def _initialize_auth(self) -> None:
        """Initialize authentication components."""
        storage = SecureAuthStorage()
        self.auth_manager = AnthropicAuthManager()
        self.interceptor = AnthropicRequestInterceptor(storage)

        # Check if authenticated (we'll check async later when needed)
        logger.info("AnthropicProMaxModel initialized with authentication support")

    async def _inject_system_prompt(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Inject Claude Code identity into system messages.

        Args:
            messages: Original messages.

        Returns:
            Messages with Claude Code identity injected.
        """
        if not self.use_auth or not self.interceptor:
            return messages

        # Check if using Pro/Max auth
        storage = SecureAuthStorage()
        auth = await storage.load("anthropic")
        if not auth or auth.type != "oauth":
            return messages  # Only inject for Pro/Max users

        # Find or create system message
        messages_copy = messages.copy()
        system_index = next((i for i, msg in enumerate(messages_copy) if msg.get("role") == "system"), None)

        if system_index is not None:
            # Prepend Claude Code identity to existing system message
            current_content = messages_copy[system_index].get("content", "")
            messages_copy[system_index]["content"] = f"{ANTHROPIC_CONFIG.CLAUDE_CODE_IDENTITY}\n\n{current_content}"
        else:
            # Add new system message at the beginning
            messages_copy.insert(0, {"role": "system", "content": ANTHROPIC_CONFIG.CLAUDE_CODE_IDENTITY})

        return messages_copy

    async def _apply_auth_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """
        Apply authentication and Claude Code headers.

        Args:
            headers: Original headers.

        Returns:
            Modified headers with auth and Claude Code spoofing.
        """
        if not self.use_auth or not self.interceptor:
            return headers

        # Use interceptor to apply auth and Claude Code headers
        modified_request = await self.interceptor.intercept_request(url="https://api.anthropic.com", headers=headers)

        return modified_request.get("headers", headers)

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
    ) -> Any: ...

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
        """Override _fetch_response to add auth and Claude Code support."""
        # Store the original litellm.acompletion function
        original_acompletion = litellm.acompletion

        async def _intercepting_acompletion(*args, **kwargs):
            """Intercept litellm.acompletion calls to transform messages and headers."""
            # Only transform for this Anthropic model
            if kwargs.get("model") == self.model:
                if "messages" in kwargs:
                    messages = kwargs["messages"]
                    logger.debug(f"Intercepting Anthropic API call with {len(messages)} messages")

                    # Add Claude Code identity to system prompt
                    messages = await self._inject_system_prompt(messages)

                    # Transform messages to add cache_control
                    messages = _transform_messages_for_cache(messages)
                    kwargs["messages"] = messages

                # Apply auth headers if available
                if self.use_auth and self.interceptor:
                    # Get existing headers or create new dict
                    headers = kwargs.get("extra_headers", {})

                    # Apply auth and Claude Code headers
                    headers = await self._apply_auth_headers(headers)

                    # Update kwargs
                    kwargs["extra_headers"] = headers

                    # For Pro/Max users, prevent API key from being added
                    storage = SecureAuthStorage()
                    auth = await storage.load("anthropic")
                    if auth and auth.type == "oauth":
                        # CRITICAL: Set api_key to None to prevent litellm from adding x-api-key header
                        # when using OAuth authentication
                        kwargs["api_key"] = None

            # Call the original function with transformed kwargs
            return await original_acompletion(*args, **kwargs)

        try:
            # Temporarily replace litellm.acompletion
            litellm.acompletion = _intercepting_acompletion

            # Call the parent's implementation
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
