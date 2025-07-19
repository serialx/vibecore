# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**vibecore** is a Textual-based terminal user interface (TUI) application written in Python. It implements a chat-like interface with custom widgets for message display and input.

## IMPORTANT: Never Run This Application

⚠️ **WARNING**: This is a TUI application. DO NOT run `vibecore` or attempt to execute the application directly as it will interfere with Claude Code's terminal interface. Only work with the source code.

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
uv run ruff check . && uv run ruff format --check . && uv run pyright
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_filename.py

# Run tests with coverage
uv run pytest --cov=vibecore
```

## Architecture Overview

### Main Components

1. **VibecoreApp** (`src/vibecore/main.py`): The main application class that extends Textual's App
   - Manages the overall UI layout with Header, Footer, and scrollable message area
   - Handles theme toggling (dark/light mode)
   - Coordinates message flow between widgets

2. **Custom Widgets**:
   - **UserMessage**: Displays user messages with a ">" prefix
   - **MyTextArea**: Custom TextArea that captures Enter key to post messages
   - **InputBox**: Container for the text input area
   - **MyFooter**: Custom footer containing the input box

3. **Styling**: Uses TCSS (Textual CSS) defined in `stopwatch03.tcss` for visual styling

### Key Patterns

- **Message Flow**: User types in MyTextArea → Enter key triggers custom Message → VibecoreApp handles message → Creates UserMessage widget → Adds to VerticalScroll container
- **Widget Communication**: Uses Textual's message system for inter-widget communication
- **Async Operations**: Leverages Python's async/await for responsive UI

### Development Notes

- The project requires Python 3.13+ and uses modern Python features
- All widgets follow Textual's composition pattern with `compose()` methods
- The application uses reactive properties for state management
- Custom CSS classes are used for styling individual components

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
# Blinking effect
def blink(self):
    self.styles.animate("opacity", 0.3, duration=0.25)
    self.set_timer(0.25, lambda: self.styles.animate("opacity", 1.0, duration=0.25))
    self.set_timer(0.5, self.blink)  # Repeat

# Slide in from right
widget.styles.offset = (100, 0)
widget.styles.animate("offset", (0, 0), duration=0.5, easing="out_cubic")

# Color transition
widget.styles.animate("background", "#00ff00", duration=1.0, easing="in_out_sine")
```

### Available Easing Functions
`linear`, `in_cubic`, `out_cubic`, `in_out_cubic` (default), `in_bounce`, `out_bounce`, `in_elastic`, `out_elastic`, and 20+ more