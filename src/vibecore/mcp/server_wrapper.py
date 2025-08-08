"""MCP server wrapper for renaming tools with a prefix pattern."""

from typing import TYPE_CHECKING, Any

from agents.mcp import MCPServer
from agents.run_context import RunContextWrapper
from mcp.types import CallToolResult, GetPromptResult, ListPromptsResult
from mcp.types import Tool as MCPTool

if TYPE_CHECKING:
    from agents import AgentBase


class NameOverridingMCPServer(MCPServer):
    """Wrapper for MCP servers that renames tools with mcp__servername__toolname pattern."""

    def __init__(self, actual_server: MCPServer, use_structured_content: bool = False):
        """Initialize the wrapper.

        Args:
            actual_server: The actual MCP server to wrap.
            use_structured_content: Whether to use structured content.
        """
        super().__init__(use_structured_content=use_structured_content)
        self.actual_server = actual_server
        # Store the mapping between renamed and original tool names
        self._tool_name_mapping: dict[str, str] = {}

    @property
    def name(self) -> str:
        """Return the name of the wrapped server."""
        return self.actual_server.name

    async def connect(self) -> None:
        """Connect to the wrapped server."""
        await self.actual_server.connect()

    async def cleanup(self) -> None:
        """Cleanup the wrapped server."""
        await self.actual_server.cleanup()

    async def list_tools(
        self,
        run_context: RunContextWrapper[Any] | None = None,
        agent: "AgentBase | None" = None,
    ) -> list[MCPTool]:
        """List tools with renamed names.

        Args:
            run_context: The run context.
            agent: The agent requesting tools.

        Returns:
            List of tools with renamed names following mcp__servername__toolname pattern.
        """
        # Get tools from the actual server
        tools = await self.actual_server.list_tools(run_context, agent)

        # Rename each tool
        renamed_tools = []
        for tool in tools:
            # Create the new name with the pattern mcp__servername__toolname
            original_name = tool.name
            new_name = f"mcp__{self.name}__{original_name}"

            # Store the mapping for call_tool
            self._tool_name_mapping[new_name] = original_name

            # Create a new tool with the renamed name
            renamed_tool = MCPTool(
                name=new_name,
                description=tool.description,
                inputSchema=tool.inputSchema,
            )
            renamed_tools.append(renamed_tool)

        return renamed_tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None) -> CallToolResult:
        """Call a tool using its original name.

        Args:
            tool_name: The renamed tool name (mcp__servername__toolname).
            arguments: The tool arguments.

        Returns:
            The result from calling the tool.
        """
        # Map the renamed tool name back to the original
        original_name = self._tool_name_mapping.get(tool_name)
        if original_name is None:
            # If not in mapping, try to extract from pattern
            if tool_name.startswith(f"mcp__{self.name}__"):
                # Extract original name from pattern
                original_name = tool_name[len(f"mcp__{self.name}__") :]
            else:
                # Use as-is if not matching our pattern
                original_name = tool_name

        # Call the tool with the original name
        return await self.actual_server.call_tool(original_name, arguments)

    async def list_prompts(self) -> ListPromptsResult:
        """List prompts from the wrapped server."""
        return await self.actual_server.list_prompts()

    async def get_prompt(self, name: str, arguments: dict[str, Any] | None = None) -> GetPromptResult:
        """Get a prompt from the wrapped server."""
        return await self.actual_server.get_prompt(name, arguments)
