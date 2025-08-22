"""
Simple sub-agent demonstration example.

This example shows how sub-agents could work in vibecore, following the pattern
proposed in SUB_AGENT_SUPPORT_PLAN.md. It demonstrates:
1. Sequential sub-agent execution
2. Parallel sub-agent execution using asyncio.gather()
3. Mixed execution patterns

Note: This is a demonstration of the proposed API. The actual implementation
will be done according to the plan.
"""

import asyncio

from agents import Agent, Runner

from vibecore.context import VibecoreContext
from vibecore.flow import UserInputFunc, flow
from vibecore.main import VibecoreApp
from vibecore.settings import settings
from vibecore.tools.file.tools import read, write
from vibecore.tools.shell.tools import grep, ls

# Create specialized sub-agents for different tasks
research_agent = Agent[VibecoreContext](
    name="Research Agent",
    instructions="""You are a research specialist. Your job is to search and gather
    information about the requested topic. Be thorough but concise.""",
    tools=[read, grep, ls],
    model=settings.model,
    model_settings=settings.default_model_settings,
)

writer_agent = Agent[VibecoreContext](
    name="Writer Agent",
    instructions="""You are a technical writer. Take the provided information and
    create clear, well-structured documentation or reports.""",
    tools=[write],
    model=settings.model,
    model_settings=settings.default_model_settings,
)

analyzer_agent = Agent[VibecoreContext](
    name="Analyzer Agent",
    instructions="""You analyze code structure and patterns. Provide insights about
    code organization, dependencies, and potential improvements.""",
    tools=[read, grep],
    model=settings.model,
    model_settings=settings.default_model_settings,
)


async def sequential_flow(app: VibecoreApp, ctx: VibecoreContext, user_input: UserInputFunc):
    """Demonstrate sequential sub-agent execution."""

    # Get user input
    topic = await user_input("What would you like to research and document?")

    print("\n🔄 Starting sequential sub-agent workflow...")

    # Phase 1: Research with the research agent
    print("📚 Phase 1: Researching topic...")

    # Mock the proposed API - in reality, this would use app.run_sub_agent()
    # For now, we'll use the standard Runner pattern to demonstrate
    research_result = Runner.run_streamed(
        research_agent,
        input=f"Research the following topic in this codebase: {topic}",
        context=ctx,
        max_turns=3,
        session=app.session,
    )

    # Handle the streamed response
    research_worker = app.handle_streamed_response(research_result)
    await research_worker.wait()

    # Phase 2: Write documentation based on research
    print("✍️ Phase 2: Creating documentation...")

    writer_result = Runner.run_streamed(
        writer_agent,
        input=f"Based on this research, create a brief summary:\n{research_result.final_output}",
        context=ctx,
        max_turns=2,
        session=app.session,
    )

    writer_worker = app.handle_streamed_response(writer_result)
    await writer_worker.wait()

    print("✅ Sequential workflow complete!\n")


async def parallel_flow(app: VibecoreApp, ctx: VibecoreContext, user_input: UserInputFunc):
    """Demonstrate parallel sub-agent execution."""

    # Get user input
    component = await user_input("Which component would you like to analyze? (e.g., 'widgets', 'tools', 'handlers')")

    print("\n🔄 Starting parallel sub-agent analysis...")
    print("⚡ Running 3 agents in parallel...")

    # Create tasks for parallel execution
    # In the actual implementation, these would use app.run_sub_agent()
    async def run_agent_task(agent: Agent, prompt: str, task_name: str):
        """Helper to run an agent and return its output."""
        print(f"  🔄 Starting: {task_name}")

        result = Runner.run_streamed(
            agent,
            input=prompt,
            context=ctx,
            max_turns=2,
            session=app.session,
        )

        # Process stream in background
        worker = app.handle_streamed_response(result)
        await worker.wait()

        print(f"  ✓ Completed: {task_name}")
        return result.final_output

    # Run three analysis tasks in parallel
    results = await asyncio.gather(
        run_agent_task(
            research_agent,
            f"List all files in the {component} directory and identify the main modules",
            "File Structure Analysis",
        ),
        run_agent_task(
            analyzer_agent, f"Analyze the code patterns and architecture used in {component}", "Architecture Analysis"
        ),
        run_agent_task(research_agent, f"Find all imports and dependencies used by {component}", "Dependency Analysis"),
    )

    # Combine results
    print("📝 Synthesizing results...")

    combined_analysis = "\n\n".join(
        [f"File Structure:\n{results[0]}", f"Architecture:\n{results[1]}", f"Dependencies:\n{results[2]}"]
    )

    # Final synthesis step
    synthesis_result = Runner.run_streamed(
        writer_agent,
        input=f"Create a concise summary of this component analysis:\n{combined_analysis}",
        context=ctx,
        max_turns=1,
        session=app.session,
    )

    synthesis_worker = app.handle_streamed_response(synthesis_result)
    await synthesis_worker.wait()

    print("✅ Parallel analysis complete!\n")


async def mixed_flow(app: VibecoreApp, ctx: VibecoreContext, user_input: UserInputFunc):
    """Demonstrate mixed sequential and parallel patterns."""

    feature = await user_input("What new feature would you like to explore? (e.g., 'streaming', 'tools', 'widgets')")

    print("\n🔄 Starting mixed-pattern workflow...")

    # Phase 1: Initial research (sequential)
    print("🔍 Phase 1: Initial research...")

    initial_result = Runner.run_streamed(
        research_agent,
        input=f"Find the main implementation files for {feature} in the codebase",
        context=ctx,
        max_turns=2,
        session=app.session,
    )

    initial_worker = app.handle_streamed_response(initial_result)
    await initial_worker.wait()

    # Phase 2: Parallel deep-dive (parallel)
    print("🔬 Phase 2: Parallel deep analysis...")

    async def analyze_aspect(prompt: str, label: str):
        print(f"  → {label}")
        result = Runner.run_streamed(
            analyzer_agent,
            input=prompt,
            context=ctx,
            max_turns=2,
            session=app.session,
        )
        worker = app.handle_streamed_response(result)
        await worker.wait()
        return result.final_output

    analyses = await asyncio.gather(
        analyze_aspect(
            f"Based on these files: {initial_result.final_output}\nAnalyze the design patterns used", "Design Patterns"
        ),
        analyze_aspect(
            f"Based on these files: {initial_result.final_output}\nIdentify potential improvements", "Improvements"
        ),
    )

    # Phase 3: Final report (sequential)
    print("📄 Phase 3: Creating final report...")

    final_result = Runner.run_streamed(
        writer_agent,
        input=f"""Create a brief technical report about {feature}:

Files Found: {initial_result.final_output}

Design Patterns: {analyses[0]}

Potential Improvements: {analyses[1]}
""",
        context=ctx,
        max_turns=1,
        session=app.session,
    )

    final_worker = app.handle_streamed_response(final_result)
    await final_worker.wait()

    print("✅ Mixed workflow complete!\n")


async def demo_flow(app: VibecoreApp, ctx: VibecoreContext, user_input: UserInputFunc):
    """Main demo flow that lets users choose which pattern to try."""

    print("""
🤖 Sub-Agent Demo
=================
This demonstrates the proposed sub-agent architecture from SUB_AGENT_SUPPORT_PLAN.md

Choose a workflow pattern:
1. Sequential - Agents run one after another, passing results
2. Parallel - Multiple agents run simultaneously
3. Mixed - Combination of sequential and parallel patterns
""")

    choice = await user_input("Enter your choice (1, 2, or 3):")

    if choice == "1":
        await sequential_flow(app, ctx, user_input)
    elif choice == "2":
        await parallel_flow(app, ctx, user_input)
    elif choice == "3":
        await mixed_flow(app, ctx, user_input)
    else:
        print("Invalid choice. Please run again and select 1, 2, or 3.")


async def main():
    # Create a coordinator agent that manages the sub-agents
    coordinator = Agent[VibecoreContext](
        name="Coordinator",
        instructions="You coordinate between different specialized agents.",
        tools=[],  # Coordinator doesn't need tools, it uses sub-agents
        model=settings.model,
        model_settings=settings.default_model_settings,
        handoffs=[research_agent, writer_agent, analyzer_agent],  # Can hand off to these agents
    )

    # Use headless=True to avoid TUI rendering, shutdown=True to exit after completion
    await flow(coordinator, demo_flow, headless=True, shutdown=True)


if __name__ == "__main__":
    asyncio.run(main())
