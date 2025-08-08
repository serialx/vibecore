"""MCP server management for Vibecore."""

from typing import TYPE_CHECKING, Any

from agents import Tool
from agents.mcp import (
    MCPServer,
    MCPServerSse,
    MCPServerSseParams,
    MCPServerStdio,
    MCPServerStdioParams,
    MCPServerStreamableHttp,
    MCPServerStreamableHttpParams,
    MCPUtil,
    create_static_tool_filter,
)
from agents.run_context import RunContextWrapper
from textual import log

from vibecore.settings import MCPServerConfig

from .server_wrapper import NameOverridingMCPServer

if TYPE_CHECKING:
    from agents import AgentBase


class MCPManager:
    """Manages MCP server connections and tool discovery."""

    def __init__(self, server_configs: list[MCPServerConfig]):
        """Initialize the MCP manager.

        Args:
            server_configs: List of MCP server configurations.
        """
        self.server_configs = server_configs
        self.servers: list[MCPServer] = []
        self._connected = False
        self._server_contexts: list[Any] = []  # Store context managers

        # Create servers immediately and wrap them
        for config in self.server_configs:
            actual_server = self._create_server(config)
            # Wrap the server to override tool names
            wrapped_server = NameOverridingMCPServer(actual_server)
            self.servers.append(wrapped_server)

    async def connect(self) -> None:
        """Connect to all configured MCP servers."""
        if self._connected:
            return

        for server in self.servers:
            await server.connect()

        self._connected = True

    async def disconnect(self) -> None:
        """Disconnect from all MCP servers."""
        if not self._connected:
            return

        # Disconnect all servers sequentially to avoid anyio cancel scope issues
        # anyio doesn't allow cancel scopes to be exited in a different task
        for server in self.servers:
            try:
                log(f"Disconnecting from MCP server: {server.name}")
                # Give each server 3 seconds to cleanup gracefully
                # await asyncio.wait_for(server.cleanup(), timeout=3.0)
                await server.cleanup()
                log(f"Disconnected from MCP server: {server.name}")
            except TimeoutError:
                log(f"Timeout disconnecting from MCP server: {server.name}")
            except Exception as e:
                log(f"Error disconnecting from MCP server {server.name}: {e}")

        # Clear the servers list to prevent any further operations
        # self.servers.clear()
        self._connected = False

    async def get_tools(self, run_context: RunContextWrapper[Any], agent: "AgentBase") -> list[Tool]:
        """Get all tools from connected MCP servers.

        Args:
            run_context: The current run context.
            agent: The agent requesting tools.

        Returns:
            List of tools from all connected MCP servers.
        """
        if not self._connected:
            await self.connect()

        # Get all tools using MCPUtil which handles the wrapped servers
        return await MCPUtil.get_all_function_tools(
            servers=self.servers,
            convert_schemas_to_strict=True,
            run_context=run_context,
            agent=agent,
        )

    def _create_server(self, config: MCPServerConfig) -> MCPServer:
        """Create an MCP server instance from configuration.

        Args:
            config: MCP server configuration.

        Returns:
            Configured MCP server instance.
        """
        tool_filter = create_static_tool_filter(
            allowed_tool_names=config.allowed_tools,
            blocked_tool_names=config.blocked_tools,
        )

        if config.type == "stdio":
            if not config.command:
                raise ValueError(f"stdio server '{config.name}' requires a command")

            return MCPServerStdio(
                name=config.name,
                params=MCPServerStdioParams(
                    command=config.command,
                    args=config.args,
                    env=config.env,
                ),
                cache_tools_list=config.cache_tools,
                client_session_timeout_seconds=config.timeout_seconds,
                tool_filter=tool_filter,
            )

        elif config.type == "sse":
            if not config.url:
                raise ValueError(f"SSE server '{config.name}' requires a URL")

            return MCPServerSse(
                name=config.name,
                params=MCPServerSseParams(url=config.url),
                cache_tools_list=config.cache_tools,
                client_session_timeout_seconds=config.timeout_seconds,
                tool_filter=tool_filter,
            )

        elif config.type == "http":
            if not config.url:
                raise ValueError(f"HTTP server '{config.name}' requires a URL")

            return MCPServerStreamableHttp(
                name=config.name,
                params=MCPServerStreamableHttpParams(url=config.url),
                cache_tools_list=config.cache_tools,
                client_session_timeout_seconds=config.timeout_seconds,
                tool_filter=tool_filter,
            )

        else:
            raise ValueError(f"Unknown MCP server type: {config.type}")

    async def __aenter__(self) -> "MCPManager":
        """Enter async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.disconnect()
