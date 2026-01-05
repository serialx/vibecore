# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vibecore** is a **Do-it-yourself Agent Framework** that transforms your terminal into a powerful AI workspace. More than just a chat interface, it's a complete platform for building and orchestrating custom AI agents that can manipulate files, execute code, run shell commands, and manage complex workflows—all from the comfort of your terminal.

Built on [Textual](https://textual.textualize.io/) and the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python), vibecore provides the foundation for creating your own AI-powered automation tools. Whether you're automating development workflows, building custom AI assistants, or experimenting with agent-based systems, vibecore gives you the building blocks to craft exactly what you need.

⭐ **KEY DIFFERENTIATOR - Flow Mode**: The core innovation of vibecore is **Flow Mode** - a system that enables building structured agent-based applications with programmatic conversation control. This transforms vibecore from a chat interface into a framework for creating sophisticated multi-agent applications with minimal code changes from the OpenAI Agents SDK examples.

### Key Features

- **Flow Mode (Experimental)** - Build structured agent-based applications with programmatic conversation control
- **AI-Powered Chat Interface** - Interact with state-of-the-art language models through an intuitive terminal interface
- **Rich Tool Integration** - Built-in tools for file operations, shell commands, Python execution, and task management
- **Beautiful Terminal UI** - Modern, responsive interface with dark/light theme support
- **Real-time Streaming** - See AI responses as they're generated with smooth streaming updates
- **Extensible Architecture** - Easy to add new tools and capabilities
- **High Performance** - Async-first design for responsive interactions
- **Context Management** - Maintains state across tool executions for coherent workflows

## IMPORTANT: Never Run This Application

⚠️ **WARNING**: This is a TUI application. DO NOT run `vibecore` or attempt to execute the application directly as it will interfere with Claude Code's terminal interface. Only work with the source code.

## Project Structure

```
vibecore/
├── src/vibecore/
│   ├── main.py              # Application entry point & TUI orchestration
│   ├── main.tcss            # Main application styles
│   ├── cli.py               # Command-line interface entry
│   ├── context.py           # Central state management for agents
│   ├── settings.py          # Configuration with Pydantic
│   ├── flow.py              # Flow mode for programmatic conversation control
│   ├── agents/              # Agent configurations & handoffs
│   │   ├── default.py       # Main agent with tool integrations
│   │   ├── prompts.py       # Agent prompt templates
│   │   └── task.py          # Task agent for sub-agent workflows
│   ├── auth/                # Authentication system (OAuth/PKCE)
│   │   ├── config.py        # Auth configuration
│   │   ├── interceptor.py   # HTTP interceptor for auth
│   │   ├── manager.py       # Auth manager orchestration
│   │   ├── models.py        # Auth data models
│   │   ├── oauth_flow.py    # OAuth flow implementation
│   │   ├── pkce.py          # PKCE utilities
│   │   ├── storage.py       # Token storage
│   │   └── token_manager.py # Token lifecycle management
│   ├── mcp/                 # Model Context Protocol integration
│   │   ├── manager.py       # MCP server management
│   │   └── server_wrapper.py # MCP server wrapper
│   ├── models/              # LLM provider integrations
│   │   ├── anthropic.py     # Claude model support via LiteLLM
│   │   └── anthropic_auth.py # Anthropic authentication
│   ├── handlers/            # Stream processing handlers
│   │   └── stream_handler.py # Handle streaming agent responses
│   ├── session/             # Session management
│   │   ├── jsonl_session.py # JSONL-based conversation storage
│   │   ├── loader.py        # Session loading logic
│   │   ├── file_lock.py     # File locking for concurrent access
│   │   └── path_utils.py    # Session path utilities
│   ├── widgets/             # Custom Textual UI components
│   │   ├── core.py          # Base widgets & layouts
│   │   ├── messages.py      # Message display components
│   │   ├── tool_messages.py # Tool-specific message widgets
│   │   ├── expandable.py    # Expandable content widgets
│   │   ├── feedback.py      # User feedback widgets
│   │   ├── info.py          # Information display widgets
│   │   ├── tool_message_factory.py  # Factory for creating tool messages
│   │   ├── core.tcss        # Core styling
│   │   ├── messages.tcss    # Message-specific styles
│   │   ├── tool_messages.tcss # Tool message styles
│   │   ├── expandable.tcss  # Expandable widget styles
│   │   ├── feedback.tcss    # Feedback widget styles
│   │   └── info.tcss        # Info widget styles
│   ├── tools/               # Extensible tool system
│   │   ├── base.py          # Tool interfaces & protocols
│   │   ├── path_validator.py # Path confinement validation
│   │   ├── file/            # File manipulation tools
│   │   │   ├── tools.py     # Tool definitions
│   │   │   ├── executor.py  # Execution logic
│   │   │   └── utils.py     # Utility functions
│   │   ├── shell/           # Shell command execution
│   │   │   ├── tools.py     # Tool definitions
│   │   │   └── executor.py  # Command execution
│   │   ├── python/          # Python code interpreter
│   │   │   ├── tools.py     # Tool definitions
│   │   │   ├── manager.py   # Execution environment manager
│   │   │   ├── helpers.py   # Python execution helpers
│   │   │   └── backends/    # Execution backends
│   │   ├── todo/            # Task management system
│   │   │   ├── tools.py     # Tool definitions
│   │   │   ├── manager.py   # Todo list manager
│   │   │   └── models.py    # Data models
│   │   ├── task/            # Sub-agent task execution
│   │   │   ├── tools.py     # Tool definitions
│   │   │   └── executor.py  # Task execution logic
│   │   ├── websearch/       # Web search tools
│   │   │   ├── tools.py     # Tool definitions
│   │   │   ├── executor.py  # Search execution
│   │   │   ├── base.py      # Base search interface
│   │   │   ├── models.py    # Search data models
│   │   │   └── ddgs/        # DuckDuckGo backend
│   │   └── webfetch/        # Web fetch tools
│   │       ├── tools.py     # Tool definitions
│   │       ├── executor.py  # Fetch execution
│   │       └── models.py    # Fetch data models
│   ├── utils/               # Utility modules
│   │   └── text.py          # Text processing utilities
│   └── prompts/             # System prompts & instructions
│       └── common_system_prompt.txt
├── examples/                # Example flows and agent applications
│   ├── basic.py             # Simple single-agent flow example
│   ├── basic_cli.py         # CLI-based flow example
│   ├── customer_service.py  # Multi-agent system with handoffs
│   └── feedback_demo.py     # User feedback collection demo
├── tests/                   # Comprehensive test suite
├── pyproject.toml           # Project configuration & dependencies
├── uv.lock                  # Locked dependencies
└── CLAUDE.md                # AI assistant instructions
```

## Development Commands

### Environment Setup
This project uses `uv` as the package manager. Install dependencies with:
```bash
uv sync
```

### Code Quality Commands
```bash
# Linting and formatting with ruff
uv run ruff check .              # Check for linting issues
uv run ruff check . --fix        # Auto-fix linting issues
uv run ruff format .             # Format code

# Type checking with pyright
uv run pyright

# Run all quality checks
uv run ruff check . && uv run ruff format --check . && uv run pyright .
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_filename.py

# Run a specific test function
uv run pytest tests/test_filename.py::test_function_name

# Run tests with coverage
uv run pytest --cov=vibecore

# Run tests matching a pattern
uv run pytest -k "test_pattern"
```

## Architecture Overview

### Core Components

1. **VibecoreApp** (`src/vibecore/main.py`): The main application class that extends Textual's App
   - Manages the overall UI layout with Header, Footer, and scrollable message area
   - Handles theme toggling (dark/light mode) with "d" keybinding
   - Coordinates message flow between widgets
   - Integrates with openai-agents framework for AI responses
   - Processes streamed responses from the agent using `@work` decorator
   - Maintains conversation history in `input_items` list

2. **Context System** (`src/vibecore/context.py`):
   - **VibecoreContext**: Central context object that maintains state across the application
   - Contains managers for todo lists and Python execution environments
   - Passed to all agent tools for consistent state management

3. **Agent System** (`src/vibecore/agents/default.py`):
   - Configures the AI agent with appropriate tools and instructions
   - Supports both OpenAI and Anthropic models via LiteLLM
   - Includes handoff capabilities for multi-agent workflows

4. **Custom Widgets** (`src/vibecore/widgets/`):
   - **UserMessage**: Displays user messages
   - **AgentMessage**: Displays AI agent responses
   - **ToolMessage**: Shows generic tool execution status and results
   - **PythonToolMessage**: Specialized widget for Python code execution with syntax highlighting
   - **ReadToolMessage**: Specialized widget for file reads with collapsible content
   - **TodoWriteToolMessage**: Specialized widget for todo list management
   - **MyTextArea**: Custom TextArea that captures Enter key to post messages
   - **AppFooter**: Custom footer containing the input box
   - **MainScroll**: Scrollable container for messages
   - **tool_message_factory**: Factory module for creating appropriate tool message widgets
   
   ⚠️ **Note**: When modifying ANY message widget, you MUST update the corresponding tests in `tests/ui/test_message_snapshots.py`. See the "Message Widget Testing" section for details.

5. **Tool System** (`src/vibecore/tools/`):
   - **File Tools**: read, write, edit, multi_edit operations
   - **Shell Tools**: bash, glob, grep, ls commands
   - **Python Tools**: Execute Python code in isolated environments
   - **Todo Tools**: Task management and tracking
   - Each tool category has its own executor, rendering, and tool definition modules

6. **Flow Mode** (`src/vibecore/flow.py`) - **KEY FEATURE**:
   - **Programmatic Conversation Control**: Define custom logic that controls agent behavior
   - **Multi-Step Workflows**: Build structured interactions with defined sequences
   - **Multi-Agent Orchestration**: Support for agent handoffs with context preservation
   - **State Management**: Maintain conversation state across interactions
   - **Application Framework**: Transform from chat interface to agent-based applications
   - Key components:
     - `Vibecore.workflow()`: Decorator that registers workflow logic
     - Runner argument: Every workflow receives a runner instance for user input, printing, and agent execution
     - Custom `logic()` functions: User-defined async functions controlling conversation flow with `runner.user_input()` / `runner.run_agent()`
   - Examples in `examples/` directory (adapted from OpenAI Agents SDK):
     - `basic.py`: Simple flow with single agent
     - `customer_service.py`: Complex multi-agent system with handoffs

7. **Styling**: 
   - Uses TCSS (Textual CSS) with multiple stylesheets loaded via `CSS_PATH`
   - CSS files are resolved relative to the module location:
     - `widgets/core.tcss`: Core widget styles
     - `widgets/messages.tcss`: Message-specific styles  
     - `main.tcss`: Main application styles
   - Order matters: later stylesheets override earlier ones

### Key Patterns

- **Message Flow**: 
  1. User types in MyTextArea
  2. Enter key triggers `MyTextArea.UserMessage` event
  3. VibecoreApp handles the event, adds message to input_items
  4. Creates UserMessage widget and adds to MainScroll
  5. Runs agent with streamed response using openai-agents Runner
  6. Processes stream events to update UI in real-time

- **Streaming Architecture**:
  - Uses `RunResultStreaming` for real-time response processing
  - Handles multiple event types: `ResponseTextDeltaEvent`, `ResponseOutputItemDoneEvent`, `ToolCallOutputItem`
  - Updates message widgets incrementally as content streams in

- **Tool Execution Pattern**:
  - Tools are defined with type hints and Pydantic models
  - Each tool has executor, rendering, and tool definition modules
  - Tools receive VibecoreContext for accessing shared state
  - Tool results are rendered in the UI with status indicators

- **Tool Message Factory Pattern**:
  - Centralized creation of tool-specific message widgets in `tool_message_factory.py`
  - Used by both `StreamHandler` (live streaming) and `SessionLoader` (history loading)
  - Ensures consistent widget creation and prevents code duplication
  - Easy to extend with new tool-specific widgets

- **Flow Pattern**:
  - User defines custom `logic()` function with conversation control
  - `flow()` creates VibecoreApp instance with the custom logic
  - `UserInputFunc` allows programmatic input collection
  - Supports both single-agent and multi-agent scenarios
  - Maintains session state across tool executions
  - Examples demonstrate minimal changes needed from OpenAI Agents SDK

- **Widget Communication**: Uses Textual's message system for inter-widget communication
- **Async Operations**: Leverages Python's async/await for responsive UI

### Development Notes

- The project requires Python 3.11+ and uses modern Python features
- All widgets follow Textual's composition pattern with `compose()` methods
- The application uses reactive properties for state management
- Custom CSS classes are used for styling individual components
- Uses `@work` decorator for background tasks to keep UI responsive
- Settings are managed via Pydantic with support for environment variables and YAML config

## IMPORTANT: Textual Library Source Code

⚠️ **MUST READ**: Textual is a relatively new library that is rapidly evolving. When developing features related to Textual:

1. **Always examine the Textual source code** located in `.venv/lib/python3.11/site-packages/textual/` (adjust the `python3.11` segment to match your interpreter's minor version)
2. **Don't rely solely on documentation** - the source code is the most accurate reference
3. **Key areas to examine**:
   - Widget implementations in `textual/widgets/` for examples and patterns
   - Base classes like `Widget`, `App`, and `Container` for understanding core functionality
   - CSS system in `textual/css/` for styling capabilities
   - Message system in `textual/message.py` and `textual/message_pump.py`
   - Event handling in `textual/events.py`

This is especially important when:
- Creating custom widgets
- Implementing complex interactions
- Working with styling and layout
- Debugging unexpected behavior

## TCSS (Textual CSS) vs Regular CSS

### Key Differences

1. **Purpose**: TCSS styles terminal widgets, not web elements
2. **Layout**: Uses `layout: vertical|horizontal|grid` and `dock` property instead of Flexbox/CSS Grid
3. **Units**: Default unit is terminal cells; supports fr (fractions), %, w/h, vw/vh
4. **No Visual Effects**: No shadows, transforms, gradients, or animations
5. **Border Styles**: Terminal-specific borders like `ascii`, `round`, `heavy`, `panel`
6. **Text Styling**: Limited to terminal capabilities (bold, italic, underline)
7. **Color System**: Simple colors, ANSI colors, basic tinting only

### Unique TCSS Properties
- `dock`: Attach widgets to screen edges (top, right, bottom, left)
- `hatch`: Terminal background patterns
- `scrollbar-*`: Extensive scrollbar customization
- `auto-color`: Automatic contrast adjustment
- `keyline`: Special border styles

### Missing from TCSS
- No custom fonts or font sizing
- No images or complex backgrounds
- No transforms or 3D effects
- No media queries
- No CSS variables (uses `$variable` syntax instead)
- No attribute selectors
- No z-index (uses `layers` instead)

### Example TCSS
```tcss
Button:hover {
    background: blue;
    border: heavy white;
}

#main-container {
    layout: vertical;
    dock: top;
    scrollbar-size: 1;
}
```

## ⚠️ CRITICAL: Animations in Textual

### DO NOT USE @keyframes
**TCSS does NOT support `@keyframes` or CSS animations!** This will not work:
```tcss
/* ❌ WRONG - This does NOT work in Textual */
@keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0.3; }
}
.my-class {
    animation: blink 1s infinite;  /* ❌ NOT SUPPORTED */
}
```

### How Animations Actually Work in Textual

Textual uses **Python-based animations** via the `animate()` method:

```python
# ✅ CORRECT - Animate opacity
widget.styles.animate("opacity", value=0.0, duration=2.0)

# ✅ CORRECT - Animate with easing
widget.animate("offset", (10, 0), duration=0.5, easing="out_bounce")

# ✅ CORRECT - Animate with callback
widget.styles.animate("background", "#ff0000", duration=1.0, on_complete=callback)
```

### What Can Be Animated

**Animatable Style Properties:**
- `opacity`, `text_opacity`
- `offset`, `padding`, `margin`
- `width`, `height`, `min_width`, `min_height`, `max_width`, `max_height`
- `color`, `background`, `background_tint`
- `scrollbar_*` properties
- Colors and numeric values

**Widget Properties:**
- Any numeric attribute
- `scroll_x`, `scroll_y`
- Custom properties that implement the Animatable protocol

### Common Animation Patterns

```python
# Blinking effect using set_interval (recommended for repeating animations)
def _toggle_blink_visible(self):
    self._blink_visible = not self._blink_visible
    self.query_one(".blink-element").visible = self._blink_visible

def _on_mount(self, event):
    # Blink every 0.5 seconds
    self.blink_timer = self.set_interval(
        0.5,
        self._toggle_blink_visible,
        pause=(self.status != "executing"),  # Can be controlled dynamically
    )

# Slide in from right
widget.styles.offset = (100, 0)
widget.styles.animate("offset", (0, 0), duration=0.5, easing="out_cubic")

# Color transition
widget.styles.animate("background", "#00ff00", duration=1.0, easing="in_out_sine")
```

### Available Easing Functions
`linear`, `in_cubic`, `out_cubic`, `in_out_cubic` (default), `in_bounce`, `out_bounce`, `in_elastic`, `out_elastic`, and 20+ more

### Using the Textual Log
```python
from textual import log
log("Debug message")  # Appears in console when using textual console
```

### Common Issues

1. **CSS not loading**: Ensure CSS files are in correct paths relative to the module
2. **Widget not updating**: Check if using `refresh()` or `update()` methods correctly
3. **Async errors**: Remember all event handlers should be async
4. **Tool execution failures**: Check VibecoreContext is properly passed to tools
5. **Markup in content rendering**: Rich/Textual interprets square brackets as markup by default. When displaying user content (e.g., file contents, command outputs) that may contain text like `[text]`, it will be interpreted as markup and render incorrectly. **Solution**: Use the `Content` class to escape markup entirely:
   ```python
   from textual.content import Content
   
   # Safe way to display user content
   widget.update(Content(user_text))  # Square brackets will be displayed literally
   
   # Or when creating Static widgets
   yield Static(Content(file_content))
   ```
   See: https://textual.textualize.io/guide/content/ for more details

## IMPORTANT: Textual Event Handlers

### ⚠️ DO NOT call super() in event handlers

According to the official Textual documentation (https://textual.textualize.io/guide/events/#event-handlers):

> "You will not have to use this in event handlers as Textual will automatically call handler methods defined in a widget's base class(es)."

This means when overriding event handlers like `on_mount()`, `on_key()`, `on_click()`, etc., you should **NEVER** call `super()`:

```python
# ❌ WRONG - Don't do this
async def on_mount(self) -> None:
    await super().on_mount()  # ❌ NOT NEEDED
    # Your code here

# ✅ CORRECT - Just implement your handler
async def on_mount(self) -> None:
    # Your code here - Textual handles parent class methods automatically
```

This applies to ALL event handlers in Textual:
- `on_mount()`
- `on_unmount()`
- `on_key()`
- `on_click()`
- `on_focus()`
- `on_blur()`
- And any other `on_*` event handler methods

## IMPORTANT: OpenAI Agents Library Source Code

⚠️ **MUST READ**: The openai-agents library is a relatively new framework that is actively evolving. When developing features related to agents:

1. **Always examine the openai-agents source code** located in `.venv/lib/python3.11/site-packages/agents/` (update the `python3.11` portion if you are using a different Python minor release)
2. **Don't rely solely on documentation** - the source code is the most accurate reference
3. **Key areas to examine**:
   - Core agent implementation in `agents/agent.py`
   - Execution engine in `agents/run.py` and `agents/_run_impl.py`
   - Tool system in `agents/tool.py`
   - Model interfaces in `agents/models/interface.py`
   - Streaming events in `agents/stream_events.py`

This is especially important when:
- Creating custom tools
- Implementing streaming responses
- Working with handoffs and guardrails
- Debugging agent behavior

## OpenAI Agents SDK Overview

The openai-agents SDK is a comprehensive framework for building AI agents with advanced capabilities like tool use, handoffs, guardrails, and structured output.

### Core Architecture

1. **Agent** (`agents/agent.py`):
   - Central class representing an AI agent
   - Configurable with instructions (system prompt), tools, handoffs, guardrails
   - Supports structured output via output schemas
   - Generic on context type for state management

2. **Runner** (`agents/run.py`):
   - Orchestrates agent execution
   - Manages turn-based conversation flow
   - Handles tool calls and agent handoffs
   - Supports both sync (`run_sync`) and streaming (`run_streamed`) modes
   - Enforces max turns limit (default: 10)

3. **Tool System** (`agents/tool.py`):
   - **FunctionTool**: User-defined Python functions exposed to agents
   - **Hosted Tools**: Pre-built tools (FileSearch, WebSearch, CodeInterpreter, Computer)
   - **MCP Tools**: Model Context Protocol integration
   - Tools receive context via `RunContextWrapper` or `ToolContext`

4. **Model Abstraction** (`agents/models/`):
   - Abstract `Model` interface for different LLM providers
   - Native OpenAI support (Chat Completions & Responses APIs)
   - LiteLLM integration for 100+ models (Anthropic, Google, etc.)
   - Model settings for tuning (temperature, top_p, etc.)

### Key Concepts

#### Context Management
```python
# Context is passed to tools, guardrails, and handoffs
class MyContext:
    def __init__(self):
        self.todo_manager = TodoManager()
        self.python_manager = PythonManager()

# Tools receive context wrapper
@function_tool
async def my_tool(context: RunContextWrapper[MyContext], param: str) -> str:
    # Access context data
    todos = context.context.todo_manager.get_todos()
    return result
```

#### Streaming Architecture
```python
# Stream events during execution
result = Runner.run_streamed(agent, "Hello")
async for event in result.stream_events():
    if isinstance(event, RunItemStreamEvent):
        if event.name == "message_output_created":
            # Handle new message
        elif event.name == "tool_called":
            # Handle tool call
    elif isinstance(event, RawResponsesStreamEvent):
        # Handle raw LLM events
```

#### Tool Creation Patterns
```python
# Simple function tool
@function_tool
def calculate(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y

# Async tool with context
@function_tool
async def read_file(
    context: RunContextWrapper[MyContext], 
    path: str
) -> str:
    """Read a file from disk."""
    content = await async_read(path)
    return content

# Tool with custom error handling
@function_tool
def risky_operation(param: str) -> str:
    try:
        result = perform_operation(param)
        return result
    except Exception as e:
        # Return error string instead of raising
        return f"Error: {str(e)}"
```

### Streaming Events

The SDK provides detailed streaming events:

1. **RawResponsesStreamEvent**: Direct LLM response events
2. **RunItemStreamEvent**: Semantic events with names:
   - `message_output_created`: New message from agent
   - `tool_called`: Tool invocation started
   - `tool_output`: Tool execution completed
   - `handoff_requested`: Agent handoff initiated
   - `reasoning_item_created`: Reasoning/thinking content

3. **AgentUpdatedStreamEvent**: Agent changed due to handoff

### Advanced Features

#### Handoffs
```python
# Define sub-agents
research_agent = Agent(
    name="Researcher",
    instructions="You research information",
    tools=[web_search_tool]
)

main_agent = Agent(
    name="Main",
    instructions="You coordinate tasks",
    handoffs=[research_agent]  # Can delegate to researcher
)
```

#### Guardrails
```python
@input_guardrail
async def check_input(context: RunContextWrapper, input: str) -> InputGuardrailResult:
    if "harmful" in input.lower():
        return InputGuardrailResult(
            should_block=True,
            should_warn=True,
            message="Potentially harmful content detected"
        )
    return InputGuardrailResult(should_block=False)

agent = Agent(
    name="Safe Agent",
    input_guardrails=[check_input]
)
```

#### Structured Output
```python
from dataclasses import dataclass

@dataclass
class AnalysisResult:
    summary: str
    sentiment: str
    key_points: list[str]

agent = Agent(
    name="Analyzer",
    output_type=AnalysisResult  # Agent must return this type
)
```

### Model Configuration

The SDK supports multiple model providers:

```python
# Default OpenAI
agent = Agent(model="gpt-4o")

# Anthropic via LiteLLM
from agents.extensions.models import LitellmModel
agent = Agent(
    model=LitellmModel("claude-3-5-sonnet-20241022")
)

# Custom settings
from agents import ModelSettings
agent = Agent(
    model_settings=ModelSettings(
        temperature=0.7,
        top_p=0.9,
        max_tokens=2000
    )
)
```

### Common Patterns in vibecore

1. **Context Usage**:
   - VibecoreContext passed to all tools
   - Contains todo_manager and python_manager
   - Maintains state across tool executions

2. **Tool Organization**:
   - Each tool category typically has:
     - `tools.py`: Tool definitions with @function_tool decorator
     - `executor.py`: Business logic implementation
     - Supporting modules like `manager.py` for stateful components
     - `utils.py` for utility functions (where needed)

3. **Streaming Integration**:
   - `_handle_streaming_response` processes events
   - Updates UI widgets incrementally
   - Handles tool calls and responses in real-time

### Important Notes

1. **Async by Default**: Most operations are async (tools, guardrails, etc.)
2. **Error Handling**: Tools should return error strings rather than raising exceptions
3. **Context Typing**: Use proper generic types for context (e.g., `RunContextWrapper[VibecoreContext]`)
4. **Tool Schemas**: Enable `strict_json_schema=True` for reliable tool calls
5. **Tracing**: Built-in tracing support with spans for debugging

### Debugging Tips

1. Enable verbose logging:
   ```python
   import agents
   agents.enable_verbose_stdout_logging()
   ```

2. Check tool schemas:
   ```python
   from agents import _debug
   _debug.VALIDATE_SCHEMAS = True
   ```

3. Trace execution:
   ```python
   run_config = RunConfig(
       trace_metadata={"session_id": "debug-123"}
   )
   ```

## Testing

### Snapshot Testing with pytest-textual-snapshot

The project uses snapshot testing to verify that widgets render correctly. This helps catch visual regressions and ensures consistent UI behavior across changes.

#### Running Snapshot Tests

```bash
# Run all snapshot tests
uv run pytest tests/ui/test_widget_snapshots.py

# Update snapshots after intentional UI changes
uv run pytest tests/ui/test_widget_snapshots.py --snapshot-update

# Run a specific snapshot test
uv run pytest tests/ui/test_widget_snapshots.py::TestWidgetSnapshots::test_basic_conversation
```

#### Test Architecture

- **Test Harness**: `tests/_harness/test_harness.py` contains `TestVibecoreApp`, a simplified version of the main app optimized for testing
- **Session Fixtures**: JSONL files in `tests/fixtures/sessions/` contain pre-recorded conversations for different scenarios
- **Snapshots**: SVG files in `tests/__snapshots__/` capture the expected visual output

#### Adding New Snapshot Tests

1. Create a new JSONL fixture file in `tests/fixtures/sessions/` with the conversation to test
2. Add a test method in `tests/ui/test_widget_snapshots.py` that loads the fixture
3. Run the test with `--snapshot-update` to generate the initial snapshot
4. Review the generated SVG to ensure it looks correct
5. Commit both the fixture and snapshot files

#### When to Update Snapshots

Update snapshots when:
- You intentionally change the UI layout or styling
- You add new widgets or modify existing ones
- You fix bugs that affect visual output

Always review the snapshot diff before updating to ensure changes are intentional.

### Message Widget Testing

⚠️ **IMPORTANT**: When adding or modifying any message widget code (UserMessage, AgentMessage, ToolMessage, etc.), you MUST update the corresponding tests.

#### Message Test Harness

The project includes a lightweight message testing framework separate from the full app tests:

- **Test Harness**: `tests/_harness/message_test_harness.py` - Simple `MessageTestApp` for testing message widgets in isolation
- **Test Suite**: `tests/ui/test_message_snapshots.py` - Comprehensive snapshot tests for all message types
- **Documentation**: `tests/README_message_tests.md` - Detailed guide on message widget testing

#### When to Update Message Tests

**ALWAYS** update message tests when you:
1. Add a new message widget class
2. Modify the rendering logic of existing message widgets
3. Change message widget styling in TCSS files
4. Add new properties or reactive attributes to message widgets
5. Modify tool message output formatting
6. Change how messages handle different states (executing, success, error)

#### How to Update Message Tests

1. **For new message types**, add a test app in `tests/_harness/message_test_harness.py`:
```python
class MyNewMessageTestApp(MessageTestApp):
    def create_test_messages(self):
        from vibecore.widgets.messages import MyNewMessage
        yield MyNewMessage("Test content", status=MessageStatus.SUCCESS)
```

2. **Add corresponding test** in `tests/ui/test_message_snapshots.py`:
```python
def test_my_new_messages(self, snap_compare):
    """Test rendering of MyNewMessage widgets."""
    app = MyNewMessageTestApp()
    assert snap_compare(app, press=[])
```

3. **For modifications to existing widgets**, update the relevant test app to include the new behavior or edge cases.

4. **Run tests and update snapshots**:
```bash
# Run message-specific tests
uv run pytest tests/ui/test_message_snapshots.py

# Update snapshots after verifying changes
uv run pytest tests/ui/test_message_snapshots.py --snapshot-update
```

#### Message Test Coverage Requirements

Ensure your tests cover:
- All visual states (idle, executing, success, error)
- Edge cases (empty content, very long content, special characters)
- Interactive elements (expandable content, clickable areas)
- Markdown rendering if applicable
- Any tool-specific formatting
