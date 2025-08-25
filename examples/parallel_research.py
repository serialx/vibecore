"""Parallel research example demonstrating sub-agent execution in flow mode.

This example shows how to use multiple sub-agents running in parallel to gather
information and then synthesize it into a final report.
"""

import asyncio
from dataclasses import dataclass

from agents import Agent, Runner, function_tool

from vibecore.context import VibecoreContext
from vibecore.flow import UserInputFunc, flow
from vibecore.main import SystemMessage, VibecoreApp


# Data models for structured output
@dataclass
class ResearchKeywords:
    """Keywords generated for research."""

    keywords: list[str]
    rationale: str


@dataclass
class SearchSummary:
    """Summary from a single search."""

    keyword: str
    summary: str
    sources: list[str]


@dataclass
class ResearchReport:
    """Final synthesized research report."""

    title: str
    executive_summary: str
    detailed_findings: str
    conclusion: str
    references: list[str]


# Mock web search tool for demo purposes
@function_tool
async def web_search_mock(query: str) -> str:
    """Mock web search tool that simulates searching for information.

    Args:
        query: The search query

    Returns:
        Mock search results
    """
    # Simulate some delay
    await asyncio.sleep(1)

    # Return mock results based on the query
    results = {
        "quantum algorithms": """
        Recent developments in quantum algorithms show significant progress in:
        - Variational Quantum Eigensolver (VQE) improvements
        - Quantum Approximate Optimization Algorithm (QAOA) enhancements
        - New error correction techniques
        Sources: arxiv.org/quantum-algorithms-2024, nature.com/quantum-computing
        """,
        "quantum cryptography": """
        Quantum cryptography advances include:
        - Quantum Key Distribution (QKD) reaching longer distances
        - Device-independent protocols gaining traction
        - Integration with classical networks improving
        Sources: ieee.org/quantum-crypto-2024, science.org/qkd-advances
        """,
        "quantum simulation": """
        Quantum simulation breakthroughs:
        - Larger system sizes now achievable
        - Better noise mitigation strategies
        - Applications in drug discovery expanding
        Sources: physics.aps.org/quantum-sim, pnas.org/quantum-materials
        """,
        "quantum machine learning": """
        Quantum machine learning progress:
        - Quantum neural networks showing promise
        - Hybrid classical-quantum algorithms improving
        - Speed advantages demonstrated for specific problems
        Sources: ml-quantum.org/recent-papers, arxiv.org/qml-2024
        """,
    }

    return results.get(query, f"Mock search results for: {query}\nNo specific data available.")


# Agent definitions
research_keyword_agent = Agent[VibecoreContext](
    name="Research Keyword Generator",
    instructions="""You are an expert at breaking down research topics into comprehensive search keywords.
    Given a research topic, generate 3-5 specific search keywords that would help gather diverse perspectives
    and comprehensive information about the topic. Return as a ResearchKeywords object.""",
    output_type=ResearchKeywords,
    model="gpt-4o-mini",
)

search_agent = Agent[VibecoreContext](
    name="Search Agent",
    instructions="""You are a search and summarization expert. Given a search keyword,
    you search for relevant information and provide a concise, informative summary
    of the findings along with source citations. Return as a SearchSummary object.""",
    output_type=SearchSummary,
    model="gpt-4o-mini",
    tools=[web_search_mock],
)

report_agent = Agent[VibecoreContext](
    name="Report Synthesizer",
    instructions="""You are an expert research report writer. Given multiple search summaries,
    synthesize them into a comprehensive, well-structured research report with proper citations.
    Return as a ResearchReport object.""",
    output_type=ResearchReport,
    model="gpt-4o-mini",
)

# Main coordinator agent for the flow
main_coordinator = Agent[VibecoreContext](
    name="Research Coordinator",
    instructions="""You coordinate research workflows by orchestrating multiple sub-agents.
    You don't perform searches yourself but manage the overall research process.""",
    model="gpt-4o-mini",
)


async def run_search_agent(app: VibecoreApp, ctx: VibecoreContext, keyword: str) -> SearchSummary:
    """Helper function to run a single search agent with streaming.

    Args:
        app: The VibecoreApp instance
        ctx: The VibecoreContext instance
        keyword: The keyword to search for

    Returns:
        The search summary from the agent
    """
    # Run the search agent with streaming
    result = Runner.run_streamed(
        search_agent,
        input=f"Search and summarize information about: {keyword}",
        context=ctx,
    )

    # Handle streaming response with dedicated SubAgentMessage widget
    worker = app.handle_sub_agent_streamed_response(
        result, agent_name=f"Search Agent ({keyword})", metadata={"keyword": keyword}
    )

    # Wait for sub-agent to complete and get result
    final_output = await worker.wait()
    return final_output


async def research_logic(app: VibecoreApp, ctx: VibecoreContext, user_input: UserInputFunc):
    """Main research workflow logic.

    Args:
        app: The VibecoreApp instance
        ctx: The VibecoreContext instance
        user_input: Function to get user input
    """
    # Step 1: Get research topic from user
    research_topic = await user_input("Enter your research topic:")
    await app.add_message(SystemMessage(f"Starting deep research on: {research_topic}"))

    # Step 2: Generate research keywords
    await app.add_message(SystemMessage("🔍 Generating research keywords..."))

    keyword_result = await Runner.run(
        research_keyword_agent,
        input=f"Generate research keywords for: {research_topic}",
        context=ctx,
    )

    keyword_output = keyword_result.final_output_as(ResearchKeywords)
    keywords = keyword_output.keywords
    await app.add_message(SystemMessage(f"Generated {len(keywords)} keywords: {', '.join(keywords)}"))

    # Step 3: Parallel search execution
    await app.add_message(SystemMessage("🔎 Executing parallel searches..."))

    # Create search tasks for parallel execution
    search_tasks = []
    for keyword in keywords:
        # Each search runs as a separate sub-agent task
        task = asyncio.create_task(run_search_agent(app, ctx, keyword))
        search_tasks.append(task)

    # Wait for all searches to complete
    await app.add_message(SystemMessage("🔎 Waiting for parallel searches to finish..."))
    search_summaries = await asyncio.gather(*search_tasks)

    await app.add_message(SystemMessage(f"✅ Completed {len(search_summaries)} searches"))

    # Step 4: Generate final report
    await app.add_message(SystemMessage("📝 Synthesizing final report..."))

    # Prepare summaries for report agent
    summaries_text = "\n\n".join(
        [f"Keyword: {s.keyword}\nSummary: {s.summary}\nSources: {', '.join(s.sources)}" for s in search_summaries]
    )

    report_result = await Runner.run(
        report_agent,
        input=f"Create a research report from these summaries:\n\n{summaries_text}",
        context=ctx,
    )

    # Step 5: Display final report
    report = report_result.final_output_as(ResearchReport)
    await app.add_message(
        SystemMessage(f"""
# Research Report: {report.title}

## Executive Summary
{report.executive_summary}

## Detailed Findings
{report.detailed_findings}

## Conclusion
{report.conclusion}

## References
{chr(10).join(f"- {ref}" for ref in report.references)}
    """)
    )

    await app.add_message(SystemMessage("✨ Research complete!"))


async def main():
    """Main entry point for the parallel research example."""
    await flow(
        agent=main_coordinator,  # Use coordinator agent for orchestration
        logic=research_logic,
        shutdown=False,  # Keep app running after completion
    )


if __name__ == "__main__":
    asyncio.run(main())
