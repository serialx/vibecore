"""Tests for MCP manager functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibecore.mcp import MCPManager
from vibecore.settings import MCPServerConfig


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server."""
    server = AsyncMock()
    server.name = "test-server"
    server.connect = AsyncMock()
    server.cleanup = AsyncMock()
    server.list_tools = AsyncMock(return_value=[])
    return server


@pytest.fixture
def test_configs():
    """Create test MCP server configurations."""
    return [
        MCPServerConfig(
            name="test-stdio",
            type="stdio",
            command="test-command",
            args=["arg1", "arg2"],
        ),
        MCPServerConfig(
            name="test-sse",
            type="sse",
            url="http://test.com/sse",
        ),
    ]


class TestMCPManager:
    """Tests for MCPManager class."""

    def test_init(self, test_configs):
        """Test MCPManager initialization."""
        manager = MCPManager(test_configs)
        assert manager.server_configs == test_configs
        assert len(manager.servers) == 2
        assert not manager._connected

    @pytest.mark.asyncio
    async def test_connect(self, test_configs, mock_mcp_server):
        """Test connecting to MCP servers."""
        manager = MCPManager(test_configs)

        # Replace servers with mocks
        manager.servers = [mock_mcp_server, mock_mcp_server]

        await manager.connect()

        assert manager._connected
        assert mock_mcp_server.connect.call_count == 2

    @pytest.mark.asyncio
    async def test_connect_idempotent(self, test_configs, mock_mcp_server):
        """Test that connect is idempotent."""
        manager = MCPManager(test_configs)
        manager.servers = [mock_mcp_server]

        await manager.connect()
        await manager.connect()  # Second call should do nothing

        assert mock_mcp_server.connect.call_count == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, test_configs, mock_mcp_server):
        """Test disconnecting from MCP servers."""
        manager = MCPManager(test_configs)
        manager.servers = [mock_mcp_server, mock_mcp_server]
        manager._connected = True

        await manager.disconnect()

        assert not manager._connected
        assert mock_mcp_server.cleanup.call_count == 2

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self, test_configs, mock_mcp_server):
        """Test disconnecting when not connected."""
        manager = MCPManager(test_configs)
        manager.servers = [mock_mcp_server]

        await manager.disconnect()  # Should do nothing

        assert mock_mcp_server.cleanup.call_count == 0

    @pytest.mark.asyncio
    async def test_context_manager(self, test_configs, mock_mcp_server):
        """Test using MCPManager as a context manager."""
        manager = MCPManager(test_configs)
        manager.servers = [mock_mcp_server]

        async with manager as ctx_manager:
            assert ctx_manager is manager
            assert manager._connected
            assert mock_mcp_server.connect.call_count == 1

        assert not manager._connected
        assert mock_mcp_server.cleanup.call_count == 1

    @pytest.mark.asyncio
    async def test_get_tools(self, test_configs, mock_mcp_server):
        """Test getting tools from MCP servers."""
        manager = MCPManager([])  # Create with empty config
        manager.servers = [mock_mcp_server]  # Add mock servers directly

        with patch("vibecore.mcp.manager.MCPUtil.get_all_function_tools") as mock_get_tools:
            mock_get_tools.return_value = []

            mock_context = MagicMock()
            mock_agent = MagicMock()

            tools = await manager.get_tools(mock_context, mock_agent)

            assert tools == []
            mock_get_tools.assert_called_once_with(
                servers=manager.servers,
                convert_schemas_to_strict=True,
                run_context=mock_context,
                agent=mock_agent,
            )

    def test_create_server_stdio(self):
        """Test creating a stdio server."""
        config = MCPServerConfig(
            name="test-stdio",
            type="stdio",
            command="test-command",
            args=["arg1"],
            env={"KEY": "value"},
        )

        manager = MCPManager([config])
        server = manager._create_server(config)

        assert server.name == "test-stdio"

    def test_create_server_sse(self):
        """Test creating an SSE server."""
        config = MCPServerConfig(
            name="test-sse",
            type="sse",
            url="http://test.com/sse",
        )

        manager = MCPManager([config])
        server = manager._create_server(config)

        assert server.name == "test-sse"

    def test_create_server_http(self):
        """Test creating an HTTP server."""
        config = MCPServerConfig(
            name="test-http",
            type="http",
            url="http://test.com/mcp",
        )

        manager = MCPManager([config])
        server = manager._create_server(config)

        assert server.name == "test-http"

    def test_create_server_invalid_type(self):
        """Test creating a server with invalid type."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Input should be 'stdio', 'sse' or 'http'"):
            MCPServerConfig(
                name="test-invalid",
                type="invalid",  # type: ignore
            )

    def test_create_server_missing_command(self):
        """Test creating a stdio server without command."""
        config = MCPServerConfig(
            name="test-stdio",
            type="stdio",
            command=None,
        )

        # Should raise when trying to create manager with invalid config
        with pytest.raises(ValueError, match="requires a command"):
            MCPManager([config])

    def test_create_server_missing_url(self):
        """Test creating an SSE/HTTP server without URL."""
        config_sse = MCPServerConfig(
            name="test-sse",
            type="sse",
            url=None,
        )

        config_http = MCPServerConfig(
            name="test-http",
            type="http",
            url=None,
        )

        manager = MCPManager([])

        with pytest.raises(ValueError, match="requires a URL"):
            manager._create_server(config_sse)

        with pytest.raises(ValueError, match="requires a URL"):
            manager._create_server(config_http)

    def test_create_server_with_tool_filter(self):
        """Test creating a server with tool filtering."""
        config = MCPServerConfig(
            name="test-filtered",
            type="stdio",
            command="test-command",
            allowed_tools=["tool1", "tool2"],
            blocked_tools=["tool3"],
        )

        manager = MCPManager([config])
        server = manager._create_server(config)

        assert server.name == "test-filtered"
