"""Tests for the MCP server wrapper."""

from unittest.mock import AsyncMock

import pytest
from mcp.types import Tool as MCPTool

from vibecore.mcp.server_wrapper import NameOverridingMCPServer


@pytest.fixture
def mock_server():
    """Create a mock MCP server."""
    server = AsyncMock()
    server.name = "test_server"
    server.connect = AsyncMock()
    server.cleanup = AsyncMock()
    server.list_tools = AsyncMock()
    server.call_tool = AsyncMock()
    server.list_prompts = AsyncMock()
    server.get_prompt = AsyncMock()
    return server


@pytest.fixture
def sample_tools():
    """Create sample MCP tools."""
    return [
        MCPTool(
            name="read_file",
            description="Read a file",
            inputSchema={"type": "object", "properties": {"path": {"type": "string"}}},
        ),
        MCPTool(
            name="write_file",
            description="Write a file",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            },
        ),
    ]


class TestNameOverridingMCPServer:
    """Tests for NameOverridingMCPServer."""

    def test_init(self, mock_server):
        """Test wrapper initialization."""
        wrapper = NameOverridingMCPServer(mock_server)
        assert wrapper.actual_server is mock_server
        assert wrapper.name == "test_server"
        assert wrapper._tool_name_mapping == {}

    @pytest.mark.asyncio
    async def test_connect_passthrough(self, mock_server):
        """Test that connect is passed through to the actual server."""
        wrapper = NameOverridingMCPServer(mock_server)
        await wrapper.connect()
        mock_server.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_passthrough(self, mock_server):
        """Test that cleanup is passed through to the actual server."""
        wrapper = NameOverridingMCPServer(mock_server)
        await wrapper.cleanup()
        mock_server.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_renames(self, mock_server, sample_tools):
        """Test that list_tools renames tools with the mcp__servername__toolname pattern."""
        mock_server.list_tools.return_value = sample_tools
        wrapper = NameOverridingMCPServer(mock_server)

        tools = await wrapper.list_tools()

        # Check that tools are renamed
        assert len(tools) == 2
        assert tools[0].name == "mcp__test_server__read_file"
        assert tools[0].description == "Read a file"
        assert tools[1].name == "mcp__test_server__write_file"
        assert tools[1].description == "Write a file"

        # Check that the mapping is stored
        assert wrapper._tool_name_mapping == {
            "mcp__test_server__read_file": "read_file",
            "mcp__test_server__write_file": "write_file",
        }

    @pytest.mark.asyncio
    async def test_call_tool_with_mapping(self, mock_server, sample_tools):
        """Test that call_tool uses the mapping to call with original name."""
        mock_server.list_tools.return_value = sample_tools
        mock_server.call_tool.return_value = {"result": "success"}

        wrapper = NameOverridingMCPServer(mock_server)

        # First list tools to populate the mapping
        await wrapper.list_tools()

        # Call a tool with the renamed name
        result = await wrapper.call_tool("mcp__test_server__read_file", {"path": "/etc/hosts"})

        # Verify the original name was used
        mock_server.call_tool.assert_called_once_with("read_file", {"path": "/etc/hosts"})
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_call_tool_without_mapping(self, mock_server):
        """Test that call_tool can extract the original name from the pattern."""
        mock_server.call_tool.return_value = {"result": "success"}
        wrapper = NameOverridingMCPServer(mock_server)

        # Call a tool without listing first (no mapping)
        result = await wrapper.call_tool("mcp__test_server__some_tool", {"arg": "value"})

        # Verify the original name was extracted
        mock_server.call_tool.assert_called_once_with("some_tool", {"arg": "value"})
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_call_tool_non_matching_pattern(self, mock_server):
        """Test that call_tool passes through non-matching tool names."""
        mock_server.call_tool.return_value = {"result": "success"}
        wrapper = NameOverridingMCPServer(mock_server)

        # Call a tool that doesn't match our pattern
        result = await wrapper.call_tool("regular_tool", {"arg": "value"})

        # Verify the name was passed as-is
        mock_server.call_tool.assert_called_once_with("regular_tool", {"arg": "value"})
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_list_prompts_passthrough(self, mock_server):
        """Test that list_prompts is passed through to the actual server."""
        mock_server.list_prompts.return_value = {"prompts": []}
        wrapper = NameOverridingMCPServer(mock_server)

        result = await wrapper.list_prompts()

        mock_server.list_prompts.assert_called_once()
        assert result == {"prompts": []}

    @pytest.mark.asyncio
    async def test_get_prompt_passthrough(self, mock_server):
        """Test that get_prompt is passed through to the actual server."""
        mock_server.get_prompt.return_value = {"prompt": "test"}
        wrapper = NameOverridingMCPServer(mock_server)

        result = await wrapper.get_prompt("test_prompt", {"arg": "value"})

        mock_server.get_prompt.assert_called_once_with("test_prompt", {"arg": "value"})
        assert result == {"prompt": "test"}

    @pytest.mark.asyncio
    async def test_tools_with_underscores(self, mock_server):
        """Test that tools with underscores in their names are handled correctly."""
        tools_with_underscores = [
            MCPTool(
                name="get_user_profile",
                description="Get user profile",
                inputSchema={"type": "object"},
            ),
            MCPTool(
                name="update_user_settings",
                description="Update user settings",
                inputSchema={"type": "object"},
            ),
        ]
        mock_server.list_tools.return_value = tools_with_underscores
        wrapper = NameOverridingMCPServer(mock_server)

        tools = await wrapper.list_tools()

        # Check that underscores in original names are preserved
        assert tools[0].name == "mcp__test_server__get_user_profile"
        assert tools[1].name == "mcp__test_server__update_user_settings"

        # Check mapping
        assert wrapper._tool_name_mapping == {
            "mcp__test_server__get_user_profile": "get_user_profile",
            "mcp__test_server__update_user_settings": "update_user_settings",
        }
