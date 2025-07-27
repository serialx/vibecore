"""Task execution logic for spawning sub-agents."""

from agents import (
    MessageOutputItem,
    RawResponsesStreamEvent,
    RunItemStreamEvent,
    Runner,
    ToolCallOutputItem,
)
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputItemDoneEvent,
    ResponseTextDeltaEvent,
)
from textual import log

from vibecore.agents.task_agent import create_task_agent
from vibecore.context import VibecoreContext
from vibecore.settings import settings


async def execute_task(
    context: VibecoreContext,
    description: str,
    prompt: str,
) -> str:
    """Execute a task using a sub-agent with streaming support.

    Args:
        context: The vibecore context to pass to the task agent
        description: Short task description (for logging/display)
        prompt: Full task instructions

    Returns:
        Task execution results as a string with formatted sub-agent activity
    """
    try:
        # Create the task agent
        task_agent = create_task_agent(prompt)

        # Run the task agent with streaming
        result = Runner.run_streamed(task_agent, prompt, context=context, max_turns=settings.max_turns)

        # Collect all streaming events with detailed formatting
        output_lines = []
        current_message = ""
        tool_calls = []
        message_count = 0

        async for event in result.stream_events():
            match event:
                case RawResponsesStreamEvent(data=data):
                    match data:
                        case ResponseTextDeltaEvent(delta=delta) if delta:
                            # Accumulate text content
                            current_message += delta

                        case ResponseOutputItemDoneEvent(
                            item=ResponseFunctionToolCall(name=tool_name, arguments=arguments, call_id=call_id)
                        ):
                            # Show tool call immediately
                            args_preview = arguments if len(arguments) < 100 else arguments[:100] + "..."
                            output_lines.append(f"🔧 Calling tool: {tool_name}")
                            output_lines.append(f"   Arguments: {args_preview}")
                            tool_calls.append(
                                {
                                    "name": tool_name,
                                    "args": args_preview,
                                    "call_id": call_id,
                                    "output": None,
                                    "line_index": len(output_lines) - 1,
                                }
                            )

                case RunItemStreamEvent(item=item):
                    match item:
                        case ToolCallOutputItem(output=output, raw_item=raw_item):
                            # Match tool output with its call
                            if isinstance(raw_item, dict) and "call_id" in raw_item:
                                call_id = raw_item["call_id"]
                                for tool_call in tool_calls:
                                    if tool_call["call_id"] == call_id:
                                        # Truncate very long outputs
                                        tool_output = str(output)
                                        if len(tool_output) > 300:
                                            tool_output = tool_output[:300] + "..."
                                        tool_call["output"] = tool_output
                                        # Add output right after the tool call
                                        output_lines.append(f"   → Result: {tool_output}")
                                        output_lines.append("")  # Empty line for readability
                                        break

                        case MessageOutputItem():
                            # Message complete - save current message if any
                            if current_message:
                                message_count += 1
                                output_lines.insert(0, f"🤖 Sub-agent message {message_count}:")
                                output_lines.insert(1, current_message)
                                output_lines.insert(2, "")  # Empty line
                                current_message = ""

        # Add any final message content
        if current_message:
            message_count += 1
            output_lines.insert(0, f"🤖 Sub-agent message {message_count}:")
            output_lines.insert(1, current_message)
            output_lines.insert(2, "")

        # Add summary at the end
        if output_lines:
            output_lines.append("———————————————")
            output_lines.append(f"✅ Task completed: {message_count} message(s), {len(tool_calls)} tool call(s)")
            return "\n".join(output_lines)
        else:
            return f"✅ Task '{description}' completed with no output."

    except Exception as e:
        log(f"Task execution error: {type(e).__name__}: {e!s}")
        return f"Task '{description}' failed with error: {e!s}"
