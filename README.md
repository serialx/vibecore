# vibecore

<div align="center">

[![PyPI version](https://badge.fury.io/py/vibecore.svg)](https://badge.fury.io/py/vibecore)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI downloads](https://img.shields.io/pypi/dm/vibecore.svg)](https://pypistats.org/packages/vibecore)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

**Build your own AI-powered automation tools in the terminal with this extensible agent framework**

[Features](#features) " [Installation](#installation) " [Usage](#usage) " [Development](#development) " [Contributing](#contributing)

</div>

---

<p align="center" style="max-width: 800px; margin: 0 auto;">
    <img src="docs/images/screenshot.png" alt="vibecore terminal screenshot" style="max-width: 100%; height: auto;">
</p>

## Overview

vibecore is a **Do-it-yourself Agent Framework** that transforms your terminal into a powerful AI workspace. More than just a chat interface, it's a complete platform for building and orchestrating custom AI agents that can manipulate files, execute code, run shell commands, and manage complex workflows—all from the comfort of your terminal.

Built on [Textual](https://textual.textualize.io/) and the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python), vibecore provides the foundation for creating your own AI-powered automation tools. Whether you're automating development workflows, building custom AI assistants, or experimenting with agent-based systems, vibecore gives you the building blocks to craft exactly what you need.

### Key Features

- **Flow Mode (Experimental)** - Build structured agent-based applications with programmatic conversation control
- **AI-Powered Chat Interface** - Interact with state-of-the-art language models through an intuitive terminal interface
- **Rich Tool Integration** - Built-in tools for file operations, shell commands, Python execution, and task management
- **MCP Support** - Connect to external tools and services via Model Context Protocol servers
- **Beautiful Terminal UI** - Modern, responsive interface with dark/light theme support
- **Real-time Streaming** - See AI responses as they're generated with smooth streaming updates
- **Extensible Architecture** - Easy to add new tools and capabilities
- **High Performance** - Async-first design for responsive interactions
- **Context Management** - Maintains state across tool executions for coherent workflows

## Installation

### Prerequisites

- Python 3.11 or higher
- (Optional) [uv](https://docs.astral.sh/uv/) for quick testing and better package management

### Quick Test (No Installation)

Try vibecore instantly without installing it:

```bash
# Install uv if you don't have it (optional)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Configure your API key
export ANTHROPIC_API_KEY="your-api-key-here"
# or
export OPENAI_API_KEY="your-api-key-here"

# Run vibecore directly with uvx
uvx vibecore
```

This will download and run vibecore in an isolated environment without affecting your system Python installation.

### Install from PyPI

```bash
# Install vibecore
pip install vibecore

# Configure your API key
export ANTHROPIC_API_KEY="your-api-key-here"
# or
export OPENAI_API_KEY="your-api-key-here"

# Run vibecore
vibecore
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/serialx/vibecore.git
cd vibecore

# Install with pip
pip install -e .

# Or install with uv (recommended for development)
uv sync

# Configure your API key
export ANTHROPIC_API_KEY="your-api-key-here"
# or
export OPENAI_API_KEY="your-api-key-here"

# Run vibecore
vibecore
# or with uv
uv run vibecore
```

## Usage

### Basic Commands

Once vibecore is running, you can:

- **Chat naturally** - Type messages and press Enter to send
- **Toggle theme** - Press `Ctrl+Shift+D` to toggle dark/light
- **Cancel agent** - Press `Esc` to cancel the current operation
- **Navigate history** - Use `Up/Down` arrows
- **Exit** - Press `Ctrl+D` twice to confirm

### Commands

- `/help` - Show help and keyboard shortcuts

## Flow Mode (Experimental)

Flow Mode is vibecore's **key differentiator** - it transforms the framework from a chat interface into a platform for building structured agent-based applications with programmatic conversation control.

### What is Flow Mode?

Flow Mode allows you to:
- **Define custom conversation logic** that controls how agents process user input
- **Build multi-step workflows** with defined sequences and decision points
- **Orchestrate multiple agents** with handoffs and shared context
- **Maintain conversation state** across interactions
- **Create agent-based applications** rather than just chatbots

### Example: Simple Flow

```python
import asyncio
from agents import Agent
from vibecore.flow import Vibecore, VibecoreRunnerBase
from vibecore.context import VibecoreContext
from vibecore.settings import settings

# Define your agent with tools
agent = Agent[VibecoreContext](
    name="Assistant",
    instructions="You are a helpful assistant",
    tools=[...],  # Your tools here
    model=settings.model,
)

# Create Vibecore instance
vibecore = Vibecore[VibecoreContext, str]()

# Define your conversation logic with decorator
@vibecore.workflow()
async def logic(
    runner: VibecoreRunnerBase[VibecoreContext, str],
) -> str:
    # Get user input programmatically
    user_message = await runner.user_input("What would you like to do?")

    # Print status updates
    await runner.print(f"Processing: {user_message}")

    # Process with agent (handles streaming automatically)
    result = await runner.run_agent(
        agent,
        input=user_message,
        context=runner.context,
        session=runner.session,
    )

    await runner.print("Done!")
    return result.final_output

# Run the flow in different modes
async def main():
    # Option 1: TUI mode (full terminal interface)
    result = await vibecore.run_textual(shutdown=False)

    # Option 2: CLI mode (simple stdin/stdout)
    # result = await vibecore.run_cli()

    # Option 3: Static mode (programmatic, for testing)
    # result = await vibecore.run("Calculate 2+2")

    print(f"Final output: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example: Multi-Agent Customer Service

Flow Mode shines when building complex multi-agent systems. See `examples/customer_service.py` for a complete implementation featuring:

- **Triage Agent**: Routes requests to appropriate specialists
- **FAQ Agent**: Handles frequently asked questions
- **Booking Agent**: Manages seat reservations
- **Agent Handoffs**: Seamless transitions between agents with context preservation
- **Shared State**: Maintains customer information across the conversation

### Key Components

- **`Vibecore` class**: Main entry point that orchestrates your workflow
- **`@vibecore.workflow()` decorator**: Defines your conversation logic function
- **Runner argument**: Every workflow receives a runner instance for user input, printing, and agent execution
- **`runner.user_input()`**: Programmatically collect user input
- **`runner.print()`**: Display status messages to the user
- **`runner.run_agent()`**: Execute agent with automatic streaming handling
- **`runner.context`**: Shared state (VibecoreContext) across tools and agents
- **`runner.session`**: Conversation history and persistence
- **Multiple execution modes**:
  - `run_textual()`: Full TUI with streaming (original behavior)
  - `run_cli()`: Simple CLI with stdin/stdout
  - `run()`: Static mode with predefined inputs (perfect for testing)
- **Agent Handoffs**: Transfer control between specialized agents with context preservation

> 🛠️ Upgrading from an older release? Read the [Runner Migration Guide](docs/runner_migration.md) for step-by-step instructions.

### Multi-Mode Execution

One of vibecore's key strengths is the ability to run the **same workflow code** in different execution modes without modification:

#### TUI Mode (Textual User Interface)
Full-featured terminal interface with streaming responses, tool visualization, and interactive controls:
```python
result = await vibecore.run_textual(shutdown=False)
```

#### CLI Mode (Command-Line Interface)
Simple stdin/stdout interaction for scripting and automation:
```python
result = await vibecore.run_cli()
```

#### Static Mode (Programmatic)
Execute with predefined inputs, perfect for testing and batch processing:
```python
# Single input
result = await vibecore.run("Calculate 2+2")

# Multiple inputs (for multi-turn workflows)
result = await vibecore.run(["First query", "Follow-up", "Final question"])
```

This unified interface means you can:
- **Develop once, deploy anywhere**: Write your workflow logic once and run it in any mode
- **Test easily**: Use static mode for automated testing with predefined inputs
- **Choose the right interface**: TUI for development, CLI for scripts, static for tests
- **Extend to new modes**: Add custom runners (HTTP API, Discord bot, etc.) by implementing the runner interface

### Use Cases

Flow Mode enables building:
- **Customer service systems** with routing and escalation
- **Guided workflows** for complex tasks
- **Interactive tutorials** with step-by-step guidance
- **Task automation** with human-in-the-loop controls
- **Multi-stage data processing** pipelines

The examples in the `examples/` directory are adapted from the official OpenAI Agents SDK with minimal modifications, demonstrating how easily you can build sophisticated agent applications with vibecore.

### Available Tools

vibecore comes with powerful built-in tools:

#### File Operations
```
- Read files and directories
- Write and edit files
- Multi-edit for batch file modifications
- Pattern matching with glob
```

#### Shell Commands
```
- Execute bash commands
- Search with grep
- List directory contents
- File system navigation
```

#### Python Execution
```
- Run Python code in isolated environments
- Persistent execution context
- Full standard library access
```

#### Task Management
```
- Create and manage todo lists
- Track task progress
- Organize complex workflows
```

### MCP (Model Context Protocol) Support

vibecore supports the [Model Context Protocol](https://modelcontextprotocol.io/), allowing you to connect to external tools and services through MCP servers.

#### Configuring MCP Servers

Create a `config.yaml` file in your project directory or add MCP servers to your environment:

```yaml
mcp_servers:
  # Filesystem server for enhanced file operations
  - name: filesystem
    type: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    
  # GitHub integration
  - name: github
    type: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your-github-token"
    
  # Custom HTTP server
  - name: my-server
    type: http
    url: "http://localhost:8080/mcp"
    allowed_tools: ["specific_tool"]  # Optional: whitelist specific tools
```

#### Available MCP Server Types

- **stdio**: Spawns a local process (npm packages, executables)
- **sse**: Server-Sent Events connection
- **http**: HTTP-based MCP servers

#### Tool Filtering

Control which tools are available from each server:

```yaml
mcp_servers:
  - name: restricted-server
    type: stdio
    command: some-command
    allowed_tools: ["safe_read", "safe_write"]  # Only these tools available
    blocked_tools: ["dangerous_delete"]         # These tools are blocked
```

## Development

### Setting Up Development Environment

```bash
# Clone and enter the repository
git clone https://github.com/serialx/vibecore.git
cd vibecore

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests by category
uv run pytest tests/ui/        # UI and widget tests
uv run pytest tests/tools/     # Tool functionality tests
uv run pytest tests/session/   # Session tests

# Run linting and formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run pyright
```

### Project Structure

```
vibecore/
├── src/vibecore/
│   ├── main.py              # Application entry point & TUI orchestration
│   ├── context.py           # Central state management for agents
│   ├── settings.py          # Configuration with Pydantic
│   ├── agents/              # Agent configurations & handoffs
│   │   └── default.py       # Main agent with tool integrations
│   ├── models/              # LLM provider integrations
│   │   └── anthropic.py     # Claude model support via LiteLLM
│   ├── mcp/                 # Model Context Protocol integration
│   │   └── manager.py       # MCP server lifecycle management
│   ├── handlers/            # Stream processing handlers
│   │   └── stream_handler.py # Handle streaming agent responses
│   ├── session/             # Session management
│   │   ├── jsonl_session.py # JSONL-based conversation storage
│   │   └── loader.py        # Session loading logic
│   ├── widgets/             # Custom Textual UI components
│   │   ├── core.py          # Base widgets & layouts
│   │   ├── messages.py      # Message display components
│   │   ├── tool_message_factory.py  # Factory for creating tool messages
│   │   ├── core.tcss        # Core styling
│   │   └── messages.tcss    # Message-specific styles
│   ├── tools/               # Extensible tool system
│   │   ├── base.py          # Tool interfaces & protocols
│   │   ├── file/            # File manipulation tools
│   │   ├── shell/           # Shell command execution
│   │   ├── python/          # Python code interpreter
│   │   └── todo/            # Task management system
│   └── prompts/             # System prompts & instructions
├── tests/                   # Comprehensive test suite
│   ├── ui/                  # UI and widget tests
│   ├── tools/               # Tool functionality tests
│   ├── session/             # Session and storage tests
│   ├── cli/                 # CLI and command tests
│   ├── models/              # Model integration tests
│   └── _harness/            # Test utilities
├── pyproject.toml           # Project configuration & dependencies
├── uv.lock                  # Locked dependencies
└── CLAUDE.md                # AI assistant instructions
```

### Code Quality

We maintain high code quality standards:

- **Linting**: Ruff for fast, comprehensive linting
- **Formatting**: Ruff formatter for consistent code style
- **Type Checking**: Pyright for static type analysis
- **Testing**: Pytest for comprehensive test coverage

Run all checks:
```bash
uv run ruff check . && uv run ruff format --check . && uv run pyright . && uv run pytest
```

## Configuration

### Path Confinement (Security)

vibecore includes a path confinement system that restricts file and shell operations to specified directories for enhanced security. This prevents agents from accessing sensitive system files or directories outside your project.

#### Configuration Options

```yaml
# config.yaml
path_confinement:
  enabled: true                    # Enable/disable path confinement (default: true)
  allowed_directories:              # List of allowed directories (default: [current working directory])
    - /home/user/projects
    - /tmp
  allow_home: false                # Allow access to user's home directory (default: false)
  allow_temp: true                 # Allow access to system temp directory (default: true)
  strict_mode: false               # Strict validation mode (default: false)
```

Or via environment variables:
```bash
export VIBECORE_PATH_CONFINEMENT__ENABLED=true
export VIBECORE_PATH_CONFINEMENT__ALLOWED_DIRECTORIES='["/home/user/projects", "/tmp"]'
export VIBECORE_PATH_CONFINEMENT__ALLOW_HOME=false
export VIBECORE_PATH_CONFINEMENT__ALLOW_TEMP=true
```

When enabled, the path confinement system:
- Validates all file read/write/edit operations
- Checks paths in shell commands before execution
- Resolves symlinks to prevent escapes
- Blocks access to files outside allowed directories

### Environment Variables

```bash
# Model configuration
ANTHROPIC_API_KEY=sk-...        # For Claude models
OPENAI_API_KEY=sk-...          # For GPT models

# OpenAI Models
VIBECORE_DEFAULT_MODEL=o3
VIBECORE_DEFAULT_MODEL=gpt-4.1
# Claude
VIBECORE_DEFAULT_MODEL=anthropic/claude-sonnet-4-20250514
# Use any LiteLLM supported models
VIBECORE_DEFAULT_MODEL=litellm/deepseek/deepseek-chat
# Local models. Use with OPENAI_BASE_URL
VIBECORE_DEFAULT_MODEL=qwen3-30b-a3b-mlx@8bit
```

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** and ensure all tests pass
3. **Add tests** for any new functionality
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description

### Development Guidelines

- Follow the existing code style and patterns
- Write descriptive commit messages
- Add type hints to all functions
- Ensure your code passes all quality checks
- Update tests for any changes

### Reporting Issues

Found a bug or have a feature request? Please [open an issue](https://github.com/serialx/vibecore/issues) with:
- Clear description of the problem or feature
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment details (OS, Python version)

## Architecture

vibecore is built with a modular, extensible architecture:

- **Textual Framework**: Provides the responsive TUI foundation
- **OpenAI Agents SDK**: Powers the AI agent capabilities
- **Async Design**: Ensures smooth, non-blocking interactions
- **Tool System**: Modular tools with consistent interfaces
- **Context Management**: Maintains state across operations

## Recent Updates

- **Flow Mode Refactor (v0.5.0)**: Complete redesign with multi-mode execution support
  - New `Vibecore` class with decorator-based workflow definition
  - Unified interface: `user_input()`, `print()`, `run_agent()`
  - Three execution modes: TUI, CLI, and static (perfect for testing)
  - Cleaner API with less boilerplate and better type safety
- **Path Confinement**: Security feature to restrict file and shell operations to specified directories
- **Reasoning View**: ReasoningMessage widget with live reasoning summaries during streaming
- **Context Usage Bar & CWD**: Footer shows token usage progress and current working directory
- **Keyboard & Commands**: Ctrl+Shift+D toggles theme, Esc cancels, Ctrl+D double-press to exit, `/help` command
- **MCP Tool Output**: Improved rendering with Markdown and JSON prettification
- **MCP Support**: Full integration with Model Context Protocol for external tool connections
- **Print Mode**: `-p` flag to print response and exit for pipes/automation

## Roadmap

- [x] More custom tool views (Python, Read, Todo widgets)
- [x] Automation (vibecore -p "prompt")
- [x] MCP (Model Context Protocol) support
- [x] Path confinement for security
- [ ] Multi-agent system (agent-as-tools)
- [ ] Plugin system for custom tools
- [ ] Automated workflow

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://textual.textualize.io/) - The amazing TUI framework
- Powered by [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- Inspired by the growing ecosystem of terminal-based AI tools

---

<div align="center">

**Made with love by the vibecore community**

[Report Bug](https://github.com/serialx/vibecore/issues) " [Request Feature](https://github.com/serialx/vibecore/issues) " [Join Discussions](https://github.com/serialx/vibecore/discussions)

</div>