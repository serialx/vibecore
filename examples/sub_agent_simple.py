"""
Simple sub-agent demonstration without TUI.

This example shows how sub-agents could work in vibecore, demonstrating:
1. Sequential sub-agent execution
2. Parallel sub-agent execution using asyncio.gather()

This version runs in print mode without TUI rendering.
"""

import asyncio
import sys

from agents import Agent, Runner

from vibecore.context import VibecoreContext
from vibecore.settings import settings
from vibecore.tools.file.tools import read
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

analyzer_agent = Agent[VibecoreContext](
    name="Analyzer Agent",
    instructions="""You analyze code structure and patterns. Provide insights about
    code organization, dependencies, and potential improvements.""",
    tools=[read, grep],
    model=settings.model,
    model_settings=settings.default_model_settings,
)


async def run_agent_with_output(agent: Agent, input_text: str, context: VibecoreContext, max_turns: int = 1) -> str:
    """Run an agent and return its final output, printing progress."""
    print(f"\n🤖 Running {agent.name}...")
    print(f"   Input: {input_text[:100]}...")

    try:
        result = Runner.run_streamed(agent, input=input_text, context=context, max_turns=max_turns)

        # Consume the stream (in real implementation this would update UI)
        async for _event in result.stream_events():
            # We could process events here if needed
            pass

        output = result.final_output or "No output generated"
        print(f"   ✅ {agent.name} completed")
        return output
    except Exception as e:
        error_msg = f"Error: {e!s}"
        print(f"   ❌ {agent.name} failed: {error_msg}")
        return error_msg


async def sequential_demo():
    """Demonstrate sequential sub-agent execution."""
    print("\n" + "=" * 60)
    print("SEQUENTIAL SUB-AGENT DEMO")
    print("=" * 60)

    ctx = VibecoreContext()

    # Phase 1: Research
    print("\n📚 Phase 1: Researching vibecore widgets...")
    research_output = await run_agent_with_output(
        research_agent, "List the main widget files in src/vibecore/widgets", ctx
    )

    # Phase 2: Analysis (uses research output)
    print("\n🔍 Phase 2: Analyzing the widget architecture...")
    analysis_output = await run_agent_with_output(
        analyzer_agent, f"Based on these widget files:\n{research_output}\n\nAnalyze the widget architecture", ctx
    )

    print("\n📊 Final Sequential Results:")
    print("-" * 40)
    print("Research found:", research_output[:200] + "..." if len(research_output) > 200 else research_output)
    print("\nAnalysis concluded:", analysis_output[:200] + "..." if len(analysis_output) > 200 else analysis_output)


async def parallel_demo():
    """Demonstrate parallel sub-agent execution."""
    print("\n" + "=" * 60)
    print("PARALLEL SUB-AGENT DEMO")
    print("=" * 60)

    ctx = VibecoreContext()

    print("\n⚡ Running 3 agents in parallel...")

    # Run three agents simultaneously
    results = await asyncio.gather(
        run_agent_with_output(research_agent, "Find all tool modules in src/vibecore/tools", ctx, max_turns=1),
        run_agent_with_output(analyzer_agent, "Analyze the main.py file structure", ctx, max_turns=1),
        run_agent_with_output(research_agent, "List all test files in the tests directory", ctx, max_turns=1),
    )

    print("\n📊 Parallel Execution Results:")
    print("-" * 40)
    print(f"1. Tool modules: {results[0][:100]}...")
    print(f"2. Main.py analysis: {results[1][:100]}...")
    print(f"3. Test files: {results[2][:100]}...")


async def main():
    """Main entry point."""
    print("\n🚀 Sub-Agent Architecture Demo")
    print("This demonstrates the proposed sub-agent support from SUB_AGENT_SUPPORT_PLAN.md\n")

    if len(sys.argv) > 1 and sys.argv[1] == "parallel":
        await parallel_demo()
    elif len(sys.argv) > 1 and sys.argv[1] == "sequential":
        await sequential_demo()
    else:
        # Run both demos
        await sequential_demo()
        await parallel_demo()

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
