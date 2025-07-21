# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vibecore** is a Textual-based terminal user interface (TUI) application written in Python. It implements an AI-powered chat interface using the openai-agents framework, with custom widgets for message display and input. The application provides various tools for file operations, shell commands, Python execution, and task management.

## IMPORTANT: Never Run This Application

⚠️ **WARNING**: This is a TUI application. DO NOT run `vibecore` or attempt to execute the application directly as it will interfere with Claude Code's terminal interface. Only work with the source code.

## Project Structure

```
vibecore/
├── src/vibecore/
│   ├── main.py              # Application entry point
│   ├── main.tcss            # Main application styles
│   ├── context.py           # VibecoreContext for state management
│   ├── settings.py          # Configuration with Pydantic
│   ├── agents/
│   │   └── default.py       # Agent configuration and setup
│   ├── models/
│   │   └── anthropic.py     # Anthropic model integration
│   ├── widgets/
│   │   ├── core.py          # Core UI widgets
│   │   ├── messages.py      # Message display widgets
│   │   ├── core.tcss        # Core widget styles
│   │   └── messages.tcss    # Message widget styles
│   ├── tools/
│   │   ├── base.py          # Base tool interfaces
│   │   ├── file/            # File manipulation tools
│   │   ├── shell/           # Shell command tools
│   │   ├── python/          # Python execution tools
│   │   └── todo/            # Task management tools
│   └── prompts/
│       └── common_system_prompt.txt
├── tests/                   # All test files (root level)
├── pyproject.toml           # Project configuration
└── uv.lock                  # Dependency lock file
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
   - **ToolMessage**: Shows tool execution status and results
   - **MyTextArea**: Custom TextArea that captures Enter key to post messages
   - **AppFooter**: Custom footer containing the input box
   - **MainScroll**: Scrollable container for messages

5. **Tool System** (`src/vibecore/tools/`):
   - **File Tools**: read, write, edit, multi_edit operations
   - **Shell Tools**: bash, glob, grep, ls commands
   - **Python Tools**: Execute Python code in isolated environments
   - **Todo Tools**: Task management and tracking
   - Each tool category has its own executor, rendering, and tool definition modules

6. **Styling**: 
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

- **Widget Communication**: Uses Textual's message system for inter-widget communication
- **Async Operations**: Leverages Python's async/await for responsive UI

### Development Notes

- The project requires Python 3.13+ and uses modern Python features
- All widgets follow Textual's composition pattern with `compose()` methods
- The application uses reactive properties for state management
- Custom CSS classes are used for styling individual components
- Uses `@work` decorator for background tasks to keep UI responsive
- Settings are managed via Pydantic with support for environment variables and YAML config

## IMPORTANT: Textual Library Source Code

⚠️ **MUST READ**: Textual is a relatively new library that is rapidly evolving. When developing features related to Textual:

1. **Always examine the Textual source code** located in `.venv/lib/python3.13/site-packages/textual/`
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