# Comprehensive Guide: Creating a New ToolMessage in Vibecore

This guide provides step-by-step instructions for creating a new tool-specific message widget in the vibecore application.

## Overview

ToolMessages are specialized widgets that display the execution and results of AI agent tools in the terminal UI. They provide visual feedback for tool invocation, execution status, and results.

## Architecture

### Key Components

1. **BaseToolMessage** (`widgets/tool_messages.py`): Base class providing common functionality
2. **Tool-specific Message Classes**: Specialized widgets for different tools
3. **Factory Pattern** (`widgets/tool_message_factory.py`): Centralized creation logic
4. **CSS Styling** (`widgets/tool_messages.tcss`): Visual appearance
5. **Integration Points**: StreamHandler and SessionLoader

### Message Lifecycle

1. Tool is invoked by the AI agent
2. Factory creates appropriate message widget
3. Widget displays in "executing" state
4. Tool completes and output is updated
5. Widget transitions to "success" or "error" state

## Step-by-Step Guide

### Step 1: Define Your Tool Message Class

Create a new class in `src/vibecore/widgets/tool_messages.py`:

```python
class YourToolMessage(BaseToolMessage):
    """A widget to display your tool execution messages."""
    
    # Define reactive properties for tool-specific data
    your_param: reactive[str] = reactive("")
    another_param: reactive[int] = reactive(0)
    
    def __init__(
        self, 
        your_param: str, 
        another_param: int = 0,
        output: str = "", 
        status: MessageStatus = MessageStatus.EXECUTING, 
        **kwargs
    ) -> None:
        """
        Construct a YourToolMessage.
        
        Args:
            your_param: Description of your parameter
            another_param: Description of another parameter
            output: The output from the tool (optional, can be set later)
            status: The status of execution
            **kwargs: Additional keyword arguments for Widget
        """
        super().__init__(status=status, **kwargs)
        self.your_param = your_param
        self.another_param = another_param
        self.output = output
    
    def compose(self) -> ComposeResult:
        """Create child widgets for your tool message."""
        # Header line - shows tool name and key info
        header = f"YourTool({self.your_param})"
        yield MessageHeader("⏺", header, status=self.status)
        
        # Custom content section (optional)
        if self.another_param > 0:
            with Horizontal(classes="your-custom-section"):
                yield Static("└─", classes="your-prefix")
                with Vertical(classes="your-content"):
                    yield Static(f"Processing {self.another_param} items...")
        
        # Output section - use inherited method
        yield from self._render_output(self.output, truncated_lines=5)
```

### Step 2: Update the Factory

Add your tool to `src/vibecore/widgets/tool_message_factory.py`:

```python
# In create_tool_message function, add:
elif tool_name == "your_tool_name":
    your_param = args_dict.get("your_param", "") if args_dict else ""
    another_param = args_dict.get("another_param", 0) if args_dict else 0
    if output is not None:
        return YourToolMessage(
            your_param=your_param,
            another_param=another_param,
            output=output,
            status=status
        )
    else:
        return YourToolMessage(
            your_param=your_param,
            another_param=another_param,
            status=status
        )
```

Don't forget to import your new class at the top:

```python
from vibecore.widgets.tool_messages import (
    BaseToolMessage,
    PythonToolMessage,
    ReadToolMessage,
    TaskToolMessage,
    TodoWriteToolMessage,
    ToolMessage,
    YourToolMessage,  # Add this
)
```

### Step 3: Add CSS Styling

Create styles in `src/vibecore/widgets/tool_messages.tcss`:

```tcss
YourToolMessage {
    /* Custom sections */
    Horizontal.your-custom-section {
        height: auto;
        
        &> .your-prefix {
            height: 1;
            width: 5;
            padding-left: 2;
            padding-right: 1;
            color: $text-muted;
        }
        
        &> Vertical.your-content {
            height: auto;
            width: 1fr;
        }
    }
    
    /* Output section (inherits base styles) */
    Horizontal.tool-output {
        height: auto;
        
        &> .tool-output-prefix {
            height: 1;
            width: 5;
            padding-left: 2;
            padding-right: 1;
            color: $text-muted;
        }
        
        &> Vertical.tool-output-content {
            height: auto;
            width: 1fr;
        }
    }
}
```

### Step 4: Handle Special Cases

Some tools may need special handling:

#### Interactive Elements (like Copy button in PythonToolMessage)

```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    """Handle button press events."""
    if event.button.has_class("your-button"):
        # Handle the button action
        self.app.copy_to_clipboard(self.your_data)

def compose(self) -> ComposeResult:
    # Add button in compose
    yield Button("Action", classes="your-button", variant="primary")
```

#### Content Processing (like line number removal in ReadToolMessage)

```python
import re

class YourToolMessage(BaseToolMessage):
    _PATTERN = re.compile(r"your_pattern", re.MULTILINE)
    
    def compose(self) -> ComposeResult:
        # Process content before display
        clean_output = self._PATTERN.sub("", self.output)
        yield from self._render_output(clean_output)
```

#### Dynamic Content Updates

```python
def update(self, status: MessageStatus, output: str | None = None) -> None:
    """Override to handle special update logic."""
    super().update(status, output)
    # Additional update logic
    if status == MessageStatus.SUCCESS:
        self.process_results()
```

## Common Patterns

### 1. Expandable Content

Use `ExpandableContent` or `ExpandableMarkdown` for long content:

```python
from .expandable import ExpandableContent, ExpandableMarkdown

# In compose method:
yield ExpandableContent(
    long_content,
    truncated_lines=5,
    classes="your-expandable",
    collapsed_text="Custom collapsed text"
)

# For code with syntax highlighting:
yield ExpandableMarkdown(
    code_content,
    language="python",
    truncated_lines=8,
    classes="code-expandable"
)
```

### 2. Status-Based Rendering

Show different content based on execution status:

```python
def compose(self) -> ComposeResult:
    yield MessageHeader("⏺", self.header_text, status=self.status)
    
    # Show progress during execution
    if self.status == MessageStatus.EXECUTING:
        yield Static("Processing...")
    
    # Show results when complete
    elif self.status == MessageStatus.SUCCESS:
        yield from self._render_output(self.output)
    
    # Show error message
    elif self.status == MessageStatus.ERROR:
        yield Static(self.error_message, classes="error")
```

### 3. Multi-Section Layout

Use the tree-like prefix pattern for multiple sections:

```python
def compose(self) -> ComposeResult:
    yield MessageHeader("⏺", "YourTool", status=self.status)
    
    # First section
    with Horizontal(classes="section1"):
        yield Static("├─", classes="prefix")
        yield Static("Section 1 content")
    
    # Second section
    with Horizontal(classes="section2"):
        yield Static("├─", classes="prefix")
        yield Static("Section 2 content")
    
    # Final section with different prefix
    with Horizontal(classes="final-section"):
        yield Static("└─", classes="prefix")
        yield Static("Final content")
```

## Testing Your ToolMessage

### 1. Create a Test Tool

```python
# In src/vibecore/tools/your_tool/tools.py
from agents.tools import function_tool
from vibecore.context import VibecoreContext

@function_tool
async def your_tool_name(
    context: VibecoreContext,
    your_param: str,
    another_param: int = 0
) -> str:
    """Your tool description."""
    # Tool implementation
    return "Tool output"
```

### 2. tui-test-engineer Agent-based Testing

1. Launch vibecore
2. Ask the AI to use your tool
3. Verify the message displays correctly
4. Check all states (executing, success, error)
5. Test with various parameter combinations

## Best Practices

### 1. Consistent Visual Language

- Use "⏺" prefix for headers
- Use tree-like prefixes (├─, └─) for sections
- Follow existing color conventions ($text-muted for prefixes)

### 2. Performance

- Use `reactive` properties for data that changes
- Set `recompose=True` only when needed
- Avoid expensive operations in `compose()`

### 3. Content Handling

- Always escape user content with `Content` class:
  ```python
  from textual.content import Content
  yield Static(Content(user_provided_text))
  ```
- Use `ExpandableContent` for long outputs
- Set appropriate `truncated_lines` values

### 4. Error Handling

- Handle missing or malformed arguments gracefully
- Provide meaningful default values
- Show clear error messages to users

### 5. Accessibility

- Use descriptive class names for CSS targeting
- Ensure all interactive elements are keyboard accessible
- Provide clear visual feedback for states

## Common Pitfalls

1. **Forgetting Factory Registration**: Always add your tool to the factory
2. **Missing CSS**: Ensure styles are added for custom sections
3. **State Management**: Use reactive properties for dynamic content
4. **Import Errors**: Update all import statements when adding new classes
5. **Markup in Content**: Use `Content` class to prevent markup interpretation

## Examples from Existing ToolMessages

### Simple Tool (ToolMessage)
- Generic fallback for any tool
- Shows tool name and command
- Basic output display

### Rich Content Tool (PythonToolMessage)
- Syntax-highlighted code display
- Copy button functionality
- Expandable code sections

### File Operation Tool (ReadToolMessage)
- Line number stripping
- Custom collapsed text showing line count
- Large content handling

### Stateful Tool (TodoWriteToolMessage)
- Complex data structure (list of todos)
- Status-based styling (pending/completed)
- Custom rendering for each item

### Nested Content Tool (TaskToolMessage)
- Multiple content sections
- Conditional rendering based on status
- Prompt and output separation

## Conclusion

Creating a new ToolMessage involves:
1. Defining the message class with appropriate properties
2. Implementing the `compose()` method for UI structure
3. Adding factory support for creation
4. Styling with TCSS
5. Testing the implementation

Follow the patterns established by existing tool messages, and ensure your implementation integrates smoothly with the streaming and session loading systems.