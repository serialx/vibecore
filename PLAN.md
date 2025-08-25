# Flow Mode Sub-Agent Feature Plan

## Use Case: Deep Research Workflow

A multi-agent research system that demonstrates parallel sub-agent execution in flow mode.

### Workflow Overview

```
User Input (Research Topic)
    ↓
ResearchKeywordAgent (generates keywords)
    ↓
Parallel SearchAgents (one per keyword)
    ↓
ReportAgent (synthesizes final report)
    ↓
Final Report Output
```

### Pseudo Code Example

```python
import asyncio
from typing import List
from dataclasses import dataclass
from agents import Agent, Runner
from vibecore.context import VibecoreContext
from vibecore.flow import UserInputFunc, flow
from vibecore.main import SystemMessage, VibecoreApp

# Data models for structured output
@dataclass
class ResearchKeywords:
    """Keywords generated for research."""
    keywords: List[str]
    rationale: str

@dataclass
class SearchSummary:
    """Summary from a single search."""
    keyword: str
    summary: str
    sources: List[str]

@dataclass
class ResearchReport:
    """Final synthesized research report."""
    title: str
    executive_summary: str
    detailed_findings: str
    conclusion: str
    references: List[str]

# Agent definitions
research_keyword_agent = Agent[VibecoreContext](
    name="Research Keyword Generator",
    instructions="""You are an expert at breaking down research topics into comprehensive search keywords.
    Given a research topic, generate 3-5 specific search keywords that would help gather diverse perspectives
    and comprehensive information about the topic.""",
    output_type=ResearchKeywords,
    model="gpt-4o",
)

search_agent = Agent[VibecoreContext](
    name="Search Agent",
    instructions="""You are a search and summarization expert. Given a search keyword,
    you search for relevant information and provide a concise, informative summary
    of the findings along with source citations.""",
    output_type=SearchSummary,
    model="gpt-4o-mini",  # Using smaller model for parallel searches
    tools=[web_search_tool],  # Hypothetical web search tool
)

report_agent = Agent[VibecoreContext](
    name="Report Synthesizer",
    instructions="""You are an expert research report writer. Given multiple search summaries,
    synthesize them into a comprehensive, well-structured research report with proper citations.""",
    output_type=ResearchReport,
    model="gpt-4o",
)

async def research_logic(app: VibecoreApp, ctx: VibecoreContext, user_input: UserInputFunc):
    # Step 1: Get research topic from user
    research_topic = await user_input("Enter your research topic:")
    await app.add_message(SystemMessage(f"Starting deep research on: {research_topic}"))
    
    # Step 2: Generate research keywords
    await app.add_message(SystemMessage("🔍 Generating research keywords..."))
    
    keyword_result = await Runner.run_async(
        research_keyword_agent,
        input=f"Generate research keywords for: {research_topic}",
        context=ctx,
    )
    
    keywords = keyword_result.output.keywords
    await app.add_message(SystemMessage(f"Generated {len(keywords)} keywords: {', '.join(keywords)}"))
    
    # Step 3: Parallel search execution
    await app.add_message(SystemMessage("🔎 Executing parallel searches..."))
    
    # Create search tasks for parallel execution
    search_tasks = []
    for keyword in keywords:
        # Each search runs as a separate sub-agent task
        task = asyncio.create_task(
            run_search_agent(app, ctx, keyword)
        )
        search_tasks.append(task)
    
    # Wait for all searches to complete
    search_summaries = await asyncio.gather(*search_tasks)
    
    await app.add_message(SystemMessage(f"✅ Completed {len(search_summaries)} searches"))
    
    # Step 4: Generate final report
    await app.add_message(SystemMessage("📝 Synthesizing final report..."))
    
    # Prepare summaries for report agent
    summaries_text = "\n\n".join([
        f"Keyword: {s.keyword}\nSummary: {s.summary}\nSources: {', '.join(s.sources)}"
        for s in search_summaries
    ])
    
    report_result = await Runner.run_async(
        report_agent,
        input=f"Create a research report from these summaries:\n\n{summaries_text}",
        context=ctx,
    )
    
    # Step 5: Display final report
    report = report_result.output
    await app.add_message(SystemMessage(f"""
# Research Report: {report.title}

## Executive Summary
{report.executive_summary}

## Detailed Findings
{report.detailed_findings}

## Conclusion
{report.conclusion}

## References
{chr(10).join(f"- {ref}" for ref in report.references)}
    """))
    
    await app.add_message(SystemMessage("✨ Research complete!"))

async def run_search_agent(app: VibecoreApp, ctx: VibecoreContext, keyword: str) -> SearchSummary:
    """Helper function to run a single search agent with streaming."""
    # Run the search agent with streaming
    result = Runner.run_streamed(
        search_agent,
        input=f"Search and summarize information about: {keyword}",
        context=ctx,
        session=app.create_sub_session(),  # Create isolated session for sub-agent
    )
    
    # Handle streaming response with dedicated SubAgentMessage widget
    worker = app.handle_sub_agent_streamed_response(
        result,
        agent_name=f"Search Agent ({keyword})",
        metadata={"keyword": keyword}
    )
    
    # Wait for sub-agent to complete
    await worker.wait()
    
    return result.final_output

async def main():
    await flow(
        agent=None,  # No main agent needed, we orchestrate sub-agents
        logic=research_logic,
        shutdown=False,  # Keep app running after completion
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Implementation Requirements

### 1. Flow Mode Enhancements

Currently missing capabilities that need to be added:

#### a. Sub-Agent Streaming Handler
Reuse and extend the existing `AgentStreamHandler` infrastructure:

```python
# In stream_handler.py - extend for sub-agents
class SubAgentStreamHandler(AgentStreamHandler):
    """Specialized handler for sub-agent streaming responses."""
    
    def __init__(
        self,
        message_handler: MessageHandler,
        agent_name: str,
        parent_context: dict = None
    ):
        super().__init__(message_handler)
        self.agent_name = agent_name
        self.parent_context = parent_context or {}
        self.sub_agent_message: SubAgentMessage | None = None
    
    async def handle_text_delta(self, delta: str) -> None:
        """Override to use SubAgentMessage instead of AgentMessage."""
        self.message_content += delta
        if not self.sub_agent_message:
            self.sub_agent_message = SubAgentMessage(
                agent_name=self.agent_name,
                content=self.message_content,
                status=MessageStatus.EXECUTING,
                metadata=self.parent_context
            )
            await self.message_handler.handle_agent_message(self.sub_agent_message)
        else:
            self.sub_agent_message.update_content(self.message_content)
    
    async def handle_message_complete(self) -> None:
        """Finalize sub-agent message when complete."""
        if self.sub_agent_message:
            self.sub_agent_message.update_status(MessageStatus.SUCCESS)
            self.sub_agent_message = None
            self.message_content = ""

# In VibecoreApp
class VibecoreApp:
    def handle_sub_agent_streamed_response(
        self,
        result: RunResultStreaming,
        agent_name: str,
        metadata: dict = None
    ) -> Worker:
        """Handle streaming response from a sub-agent.
        
        Reuses the existing streaming infrastructure with SubAgentStreamHandler.
        """
        # Create a custom message handler for the sub-agent
        class SubAgentMessageHandler:
            def __init__(self, app: VibecoreApp):
                self.app = app
                
            async def handle_agent_message(self, message: BaseMessage) -> None:
                # Mount message in a sub-agent container
                container = self.app.query_one("#sub-agents-container", default=None)
                if not container:
                    # Create container if it doesn't exist
                    container = SubAgentsContainer(id="sub-agents-container")
                    self.app.query_one(MainScroll).mount(container)
                container.mount(message)
                
            async def handle_agent_update(self, new_agent: Agent) -> None:
                # Sub-agents don't typically handoff, but handle if needed
                pass
                
            async def handle_agent_error(self, error: Exception) -> None:
                # Update the sub-agent message with error status
                pass
                
            async def handle_agent_finished(self) -> None:
                # Mark sub-agent as complete
                pass
        
        # Create handler with sub-agent specific behavior
        handler = SubAgentStreamHandler(
            SubAgentMessageHandler(self),
            agent_name=agent_name,
            parent_context=metadata
        )
        
        # Use @work decorator for non-blocking execution
        @work(exclusive=False, thread=False)
        async def process_sub_agent_stream():
            await handler.process_stream(result)
            return result.final_output
        
        return process_sub_agent_stream()
    
    def create_sub_session(self) -> Session:
        """Create an isolated session for sub-agent execution."""
        # Returns a new session that doesn't interfere with main conversation
        return Session(parent=self.session)
```

### 2. UI/UX Considerations

#### a. SubAgentMessage Widget
New widget similar to TaskToolMessage that displays sub-agent activity. Can inherit from BaseToolMessage for consistency:

```python
from vibecore.widgets.tool_messages import BaseToolMessage

class SubAgentMessage(BaseToolMessage):
    """Widget for displaying sub-agent execution and streaming output.
    
    Similar to TaskToolMessage but for sub-agent execution.
    """
    
    def __init__(
        self,
        agent_name: str,
        content: str = "",
        metadata: dict = None,
        status: MessageStatus = MessageStatus.EXECUTING,
    ):
        # Initialize as a special tool message
        super().__init__(
            tool_name=f"sub_agent:{agent_name}",
            arguments={},  # Will be populated with metadata
            status=status
        )
        self.agent_name = agent_name
        self.content = content
        self.metadata = metadata or {}
        self.agent_message: AgentMessage | None = None
        self.tool_messages: list[BaseToolMessage] = []
        
    def compose(self):
        # Header with agent name and status indicator
        yield SubAgentHeader(
            self.agent_name,
            self.status,
            self.metadata
        )
        
        # Collapsible container for sub-agent's messages
        with ExpandableContainer(
            title=f"Agent: {self.agent_name}",
            expanded=self.status == MessageStatus.EXECUTING
        ):
            # Show the agent's current message if streaming
            if self.agent_message:
                yield self.agent_message
            
            # Show any tool calls made by the sub-agent
            for tool_msg in self.tool_messages:
                yield tool_msg
    
    def update_content(self, content: str) -> None:
        """Update the agent's message content during streaming."""
        if not self.agent_message:
            self.agent_message = AgentMessage(content, status=MessageStatus.EXECUTING)
            self.mount(self.agent_message)
        else:
            self.agent_message.update(content)
    
    def add_tool_message(self, tool_message: BaseToolMessage) -> None:
        """Add a tool call made by the sub-agent."""
        self.tool_messages.append(tool_message)
        self.mount(tool_message)
    
    def update_status(self, status: MessageStatus) -> None:
        """Update the overall status of the sub-agent execution."""
        self.status = status
        if self.agent_message:
            self.agent_message.status = MessageStatus.IDLE if status == MessageStatus.SUCCESS else status
        # Update header to reflect new status
        self.query_one(SubAgentHeader).status = status
```

Features:
- **Live Streaming**: Shows agent's responses as they stream in
- **Status Indicators**: Executing (spinning), Success (✓), Error (✗)
- **Nested Tool Calls**: Display tools used by the sub-agent
- **Collapsible Sections**: Keep UI clean while maintaining full visibility
- **Parallel Execution Indicators**: Show multiple SubAgentMessages running simultaneously

#### b. Progress Visualization
- Show which agents are currently running
- Progress indicators for parallel operations
- Clear hierarchy of agent outputs

#### c. Message Organization
- Group messages by agent/sub-task
- Collapsible sections for sub-agent outputs
- Clear visual separation between workflow stages


## Implementation Strategy

### Phase 1: Core Infrastructure
1. **Extend AgentStreamHandler**
   - Create `SubAgentStreamHandler` class in `stream_handler.py`
   - Override methods to handle sub-agent specific behavior
   - Support nested tool calls and agent messages

2. **Create SubAgentMessage Widget**
   - Inherit from `BaseToolMessage` for consistency
   - Implement collapsible container for agent output
   - Support nested tool messages from sub-agent

3. **Modify VibecoreApp**
   - Add `handle_sub_agent_streamed_response()` method
   - Implement sub-session creation for isolation
   - Add container widget for organizing sub-agent messages

### Phase 2: Flow Mode Integration
1. **Session Management**
   - Implement sub-session isolation
   - Prevent conversation history pollution
   - Maintain parent-child session relationships

### Phase 3: Example Implementation
1. **Simple Test Case**
   - Parallel math calculations with multiple agents
   - Test UI update synchronization
   - Verify result aggregation

2. **Research Workflow**
   - Implement the full research example
   - Test with real web search tools
   - Optimize parallel execution performance

### Phase 4: Polish and Testing
1. **UI/UX Improvements**
   - Progress indicators for parallel operations
   - Better visual hierarchy for nested agents
   - Keyboard shortcuts for expanding/collapsing

2. **Error Handling**
   - Graceful failure of individual sub-agents
   - Timeout mechanisms for long-running agents
   - Cancellation support for user interruption

3. **Testing**
   - Unit tests for SubAgentStreamHandler
   - Snapshot tests for SubAgentMessage widget
   - Integration tests for parallel execution

## Questions to Address

1. **Error Handling**: How to handle failures in parallel agents?
2. **Cancellation**: How to cancel running sub-agents if user interrupts?
3. **Resource Management**: Limits on parallel agent execution?
4. **Streaming**: How to handle streaming from multiple parallel agents?

## Visual Example of UI During Execution

```
┌─────────────────────────────────────────────────────────────┐
│ Vibecore - Deep Research Workflow                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ User: Research quantum computing applications              │
│                                                             │
│ System: Starting deep research on: quantum computing       │
│         applications                                       │
│                                                             │
│ System: 🔍 Generating research keywords...                 │
│                                                             │
│ System: Generated 4 keywords: quantum algorithms,          │
│         quantum cryptography, quantum simulation,          │
│         quantum machine learning                           │
│                                                             │
│ System: 🔎 Executing parallel searches...                  │
│                                                             │
│ ┌─[Search Agent (quantum algorithms)]──────[⚡ Executing]─┐ │
│ │ Input: Search and summarize information about:         │ │
│ │        quantum algorithms                               │ │
│ │ Output: Searching for recent developments in quantum... │ │
│ │ [Tool: web_search] Searching "quantum algorithms 2024" │ │
│ └──────────────────────────────────────────────────────── ┘ │
│                                                             │
│ ┌─[Search Agent (quantum cryptography)]────[⚡ Executing]─┐ │
│ │ Input: [collapsed]                                     │ │
│ │ Output: Quantum cryptography leverages the principles..│ │
│ │ [Tool: web_search] Complete                            │ │
│ └──────────────────────────────────────────────────────── ┘ │
│                                                             │
│ ┌─[Search Agent (quantum simulation)]──────[✓ Complete]──┐ │
│ │ Input: [collapsed]                                     │ │
│ │ Output: [View full summary - 450 words]                │ │
│ └──────────────────────────────────────────────────────── ┘ │
│                                                             │
│ ┌─[Search Agent (quantum machine learning)]─[⚡ Executing]┐ │
│ │ Input: [collapsed]                                     │ │
│ │ Output: Recent advances in quantum machine learning... │ │
│ └──────────────────────────────────────────────────────── ┘ │
│                                                             │
│ System: ✅ Completed 4 searches                            │
│                                                             │
│ System: 📝 Synthesizing final report...                    │
│                                                             │
│ [Final Report displayed here]                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Benefits of This Approach

1. **Composability**: Small, focused agents that do one thing well
2. **Parallelism**: Significant speed improvements for independent tasks
3. **Modularity**: Easy to swap out or upgrade individual agents
4. **Scalability**: Can add more search agents or other processing stages
5. **Clarity**: Clear separation of concerns between agents
6. **Visibility**: Full transparency into what each sub-agent is doing
7. **Streaming**: Real-time updates from all agents running concurrently