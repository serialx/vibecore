"""MCP (Model Context Protocol) integration for Vibecore."""

from .manager import MCPManager
from .server_wrapper import NameOverridingMCPServer

__all__ = ["MCPManager", "NameOverridingMCPServer"]
