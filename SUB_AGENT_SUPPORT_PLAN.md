# Sub-Agent Support Implementation Plan

## Overview
Enable Vibecore to run sub-agents with full streaming support, providing a foundation for both sequential and parallel agent execution patterns. This generalizes the pattern currently used by TaskTool, allowing any flow to spawn sub-agents that stream their output to nested UI widgets. Parallel execution becomes a natural consequence of using Python's `asyncio.gather()` with multiple sub-agent calls.

## Rationale for This Approach

### Why Not Dedicated Parallel Agent Support?
The initial plan proposed creating specific `ParallelAgentMessage` and `ParallelRunner` classes. However, this approach would:
- Duplicate patterns already present in TaskTool
- Create separate systems for parallel vs sequential execution
- Limit flexibility in execution patterns
- Add unnecessary complexity to the codebase

### Why General Sub-Agent Support is Better
1. **Architectural Simplicity**: One unified system for all agent hierarchies
2. **Flexibility**: Supports sequential, parallel, and mixed execution patterns
3. **Code Reuse**: Leverages existing streaming infrastructure
4. **Natural Python Patterns**: Uses standard `asyncio` for parallelism
5. **Alignment with OpenAI SDK**: Extends existing handoff patterns

## Current State Analysis

### How TaskTool Works Today
1. **Task Execution** (`src/vibecore/tools/task/executor.py`):
   - Creates a sub-agent with `create_task_agent()`
   - Runs with `Runner.run_streamed()` 
   - Streams events to app via `context.app.handle_task_tool_event()`

2. **Event Routing**:
   - App's `handle_task_tool_event()` routes to `AgentStreamHandler.handle_task_tool_event()`
   - StreamHandler finds the TaskToolMessage widget by tool_call_id
   - Widget has its own AgentStreamHandler that processes events

3. **Widget Display** (`src/vibecore/widgets/tool_messages.py:TaskToolMessage`):
   - Contains a MainScroll area for nested agent messages
   - Has its own AgentStreamHandler instance
   - Displays sub-agent's messages, tool calls, and outputs

## Implementation Plan

### Phase 1: Create General SubAgentMessage Widget

**New file**: `src/vibecore/widgets/sub_agent.py`

```python
from textual.reactive import reactive
from vibecore.widgets.core import BaseMessage, MainScroll, MessageHeader
from vibecore.widgets.messages import MessageStatus
from vibecore.handlers.stream_handler import AgentStreamHandler
from agents import StreamEvent

class SubAgentMessage(BaseMessage):
    """General widget for displaying any sub-agent execution with streaming."""
    
    agent_name: reactive[str]
    agent_id: str
    description: reactive[str]
    parent_context: str  # e.g., "task", "handoff", "parallel_search"
    
    def __init__(
        self, 
        agent_name: str, 
        agent_id: str, 
        description: str = "",
        parent_context: str = "sub-agent",
        status: MessageStatus = MessageStatus.EXECUTING
    ):
        super().__init__(status=status)
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.description = description
        self.parent_context = parent_context
        self._agent_stream_handler = None
        self.main_scroll = MainScroll()
        
    def compose(self):
        # Icon based on context
        icon = {
            "task": "🔧",
            "handoff": "🤝",
            "parallel": "⚡",
            "search": "🔍",
            "sub-agent": "🤖"
        }.get(self.parent_context, "🤖")
        
        # Header with agent name and status
        yield MessageHeader(icon, f"{self.agent_name}", status=self.status)
        
        # Description if provided
        if self.description:
            yield Static(f"└─ {self.description}", classes="sub-agent-description")
            
        # Nested messages area
        with Horizontal(classes="sub-agent-content"):
            yield Static("  ", classes="sub-agent-indent")
            yield self.main_scroll
            
    async def handle_agent_event(self, event: StreamEvent):
        """Process streaming events from the sub-agent."""
        if self._agent_stream_handler is None:
            from vibecore.handlers.stream_handler import AgentStreamHandler
            self._agent_stream_handler = AgentStreamHandler(self)
        await self._agent_stream_handler.handle_event(event)
        
    async def add_message(self, message: BaseMessage):
        """Add a message to the nested scroll area."""
        await self.main_scroll.mount(message)
        
    def mark_complete(self, success: bool = True):
        """Mark the sub-agent execution as complete."""
        self.status = MessageStatus.SUCCESS if success else MessageStatus.ERROR
```

### Phase 2: Add Sub-Agent Support to VibecoreApp

**Update**: `src/vibecore/main.py`

Add methods for running sub-agents:

```python
import uuid
from typing import Optional, Dict
from vibecore.widgets.sub_agent import SubAgentMessage
from agents import Agent, Runner, RunResultStreaming

class VibecoreApp(App):
    # ... existing code ...
    
    def __init__(self, ...):
        # ... existing init ...
        self.active_sub_agents: Dict[str, SubAgentMessage] = {}
        
    async def run_sub_agent(
        self,
        agent: Agent,
        input_text: str,
        description: str = "",
        parent_context: str = "sub-agent",
        max_turns: int = 10,
        display_inline: bool = True
    ) -> RunResultStreaming:
        """
        Run a sub-agent with streaming to UI.
        
        Args:
            agent: The agent to run
            input_text: Input to the agent
            description: Optional description for the UI
            parent_context: Context type (task, handoff, parallel, etc.)
            max_turns: Maximum conversation turns
            display_inline: If True, add widget to main message area
            
        Returns:
            RunResultStreaming with the final output
        """
        agent_id = str(uuid.uuid4())[:8]
        
        # Create widget for this sub-agent
        widget = SubAgentMessage(
            agent_name=agent.name,
            agent_id=agent_id,
            description=description,
            parent_context=parent_context
        )
        
        # Track active sub-agent
        self.active_sub_agents[agent_id] = widget
        
        # Add to UI if requested
        if display_inline:
            await self.add_message(widget)
        
        try:
            # Run the agent with streaming
            result = Runner.run_streamed(
                agent, 
                input_text, 
                context=self.context,
                max_turns=max_turns
            )
            
            # Stream events to the widget
            async for event in result.stream_events():
                await widget.handle_agent_event(event)
                
            # Mark as complete
            widget.mark_complete(success=True)
            
        except Exception as e:
            # Mark as failed
            widget.mark_complete(success=False)
            raise
            
        finally:
            # Clean up tracking
            del self.active_sub_agents[agent_id]
            
        return result
        
    async def handle_sub_agent_event(self, agent_id: str, event: StreamEvent):
        """Route events to the appropriate sub-agent widget."""
        if widget := self.active_sub_agents.get(agent_id):
            await widget.handle_agent_event(event)
```

### Phase 3: Update Flow Support

**Update**: `src/vibecore/flow.py`

Export sub-agent functionality:

```python
# Add to module exports
__all__ = ['flow', 'UserInputFunc', 'SubAgentMessage']

# Document sub-agent support in docstring
"""
The flow module provides programmatic conversation control with sub-agent support.

Example - Sequential sub-agents:
    result1 = await app.run_sub_agent(research_agent, query)
    result2 = await app.run_sub_agent(writer_agent, result1.final_output)

Example - Parallel sub-agents:
    results = await asyncio.gather(
        app.run_sub_agent(agent1, input1, "Searching academic papers"),
        app.run_sub_agent(agent2, input2, "Searching news articles"),
        app.run_sub_agent(agent3, input3, "Searching documentation")
    )
"""
```

### Phase 4: Refactor TaskTool (Optional)

Update TaskTool to use the new general sub-agent infrastructure:

```python
# In src/vibecore/tools/task/executor.py
async def execute_task(context: VibecoreContext, description: str, ...)
    # Instead of custom handling, use the new sub-agent support
    task_agent = create_task_agent(...)
    
    result = await context.app.run_sub_agent(
        agent=task_agent,
        input_text=description,
        description=f"Task: {description[:50]}...",
        parent_context="task",
        max_turns=max_turns
    )
    
    return result.final_output
```

## Usage Examples

### Sequential Execution
```python
async def sequential_flow(app, ctx, user_input):
    query = await user_input("What would you like to research?")
    
    # Research phase
    research_result = await app.run_sub_agent(
        research_agent,
        query,
        description="Researching topic",
        parent_context="search"
    )
    
    # Writing phase (uses research output)
    report_result = await app.run_sub_agent(
        writer_agent,
        f"Write a report based on: {research_result.final_output}",
        description="Writing report",
        parent_context="task"
    )
```

### Parallel Execution
```python
async def parallel_search_flow(app, ctx, user_input):
    query = await user_input("What would you like to search for?")
    
    # Run multiple searches in parallel
    search_results = await asyncio.gather(
        app.run_sub_agent(
            web_search_agent,
            f"Search web for: {query}",
            description="Web search",
            parent_context="parallel"
        ),
        app.run_sub_agent(
            academic_agent,
            f"Search academic papers for: {query}",
            description="Academic search",
            parent_context="parallel"
        ),
        app.run_sub_agent(
            news_agent,
            f"Search recent news about: {query}",
            description="News search",
            parent_context="parallel"
        )
    )
    
    # Combine results
    combined = "\n\n".join([r.final_output for r in search_results])
    
    # Synthesize findings
    synthesis = await app.run_sub_agent(
        synthesis_agent,
        f"Synthesize these findings:\n{combined}",
        description="Synthesizing results"
    )
```

### Mixed Patterns
```python
async def complex_flow(app, ctx, user_input):
    # Get initial input
    task = await user_input("Describe your task")
    
    # Phase 1: Parallel analysis
    analyses = await asyncio.gather(
        app.run_sub_agent(feasibility_agent, task, "Checking feasibility"),
        app.run_sub_agent(requirements_agent, task, "Gathering requirements")
    )
    
    # Phase 2: Sequential planning based on analyses
    plan = await app.run_sub_agent(
        planner_agent,
        f"Task: {task}\nAnalyses: {[a.final_output for a in analyses]}",
        description="Creating plan"
    )
    
    # Phase 3: Parallel implementation of plan steps
    if plan_data := plan.final_output_as(PlanData):
        implementations = await asyncio.gather(*[
            app.run_sub_agent(
                implement_agent,
                step.description,
                description=f"Step {i+1}: {step.name}"
            )
            for i, step in enumerate(plan_data.steps)
        ])
```

## Benefits

1. **Unified System**: Single approach for all sub-agent scenarios
2. **Natural Parallelism**: Use standard Python `asyncio.gather()` for parallel execution
3. **Full Streaming**: All sub-agents stream their output in real-time
4. **Flexibility**: Supports any execution pattern (sequential, parallel, mixed)
5. **Code Reuse**: Leverages existing streaming infrastructure
6. **Maintainability**: Less code duplication, cleaner architecture
7. **Extensibility**: Easy to add new contexts and behaviors

## Validation from Demo

Three demonstration files validate the proposed architecture:

### 1. `examples/sub_agent_demo.py`
Full integration with vibecore's flow system, showing:
- Sequential workflows using standard `Runner.run_streamed()`
- Parallel execution with `asyncio.gather()`
- Mixed execution patterns
- UI properly displays agent messages and tool outputs
- Flow mode successfully orchestrates multi-agent interactions

### 2. `examples/sub_agent_simple.py`
Standalone demonstration without TUI, showing:
- Direct agent execution with print output
- Error handling for max turns exceeded
- Simplified API for testing

### 3. `examples/sub_agent_mock.py`
Mock implementation demonstrating all patterns:
- **Sequential**: Agents run one after another (1.5s + 2.0s = 3.5s total)
- **Parallel**: Multiple agents run simultaneously (2.0s total vs 4.5s sequential)
- **Mixed**: Combination of sequential and parallel patterns
- **Nested**: Agents spawning their own sub-agents

**Key Findings**:
1. Current infrastructure already supports most sub-agent patterns
2. Parallel execution provides significant performance benefits
3. The main missing piece is a dedicated `SubAgentMessage` widget for better visual nesting
4. The `app.run_sub_agent()` method would simplify the API but isn't strictly necessary
5. Event routing works correctly with the existing stream handler

## Testing Plan

1. **Unit Tests**:
   - Test SubAgentMessage widget rendering
   - Test event routing to sub-agents
   - Test status updates (executing → success/error)

2. **Integration Tests**:
   - Sequential sub-agent execution (validated in demo)
   - Parallel sub-agent execution with 3+ agents (validated in demo)
   - Mixed execution patterns (validated in demo)
   - Error handling when sub-agent fails
   - Cancellation during execution

3. **Performance Tests**:
   - Verify no blocking with 10+ parallel sub-agents
   - Memory usage with nested sub-agents
   - Event streaming performance

4. **UI Tests**:
   - Snapshot tests for SubAgentMessage rendering
   - Verify nested message display
   - Test collapse/expand functionality

## Future Enhancements

- **Progress Tracking**: Add progress percentage for long-running sub-agents
- **Dependencies**: Support for agent dependencies (agent B waits for agent A)
- **Resource Limits**: Configurable limits on concurrent sub-agents
- **Result Aggregation**: Built-in helpers for combining sub-agent outputs
- **Retry Logic**: Automatic retry for failed sub-agents
- **Handoff Integration**: Seamless integration with OpenAI SDK handoff patterns
- **Observability**: Tracing and metrics for sub-agent execution patterns