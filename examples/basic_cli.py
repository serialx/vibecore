import asyncio

from agents import Agent

from vibecore.context import FullVibecoreContext
from vibecore.flow import Vibecore, VibecoreRunnerBase
from vibecore.settings import settings
from vibecore.tools.file.tools import read
from vibecore.tools.shell.tools import glob, grep, ls
from vibecore.tools.todo.tools import todo_read, todo_write

agent = Agent[FullVibecoreContext](
    name="Poetic Agent",
    instructions="You are a poetic calculator",
    tools=[
        todo_read,
        todo_write,
        read,
        glob,
        grep,
        ls,
    ],
    model=settings.model,
    model_settings=settings.default_model_settings,
    handoffs=[],
)


vibecore = Vibecore[FullVibecoreContext, str]()


@vibecore.workflow()
async def logic(
    runner: VibecoreRunnerBase[FullVibecoreContext, str],
) -> str:
    user_message = await runner.user_input("Input your message:")
    await runner.print(f"Starting generation of '{user_message}'...")
    result = await runner.run_agent(
        agent,
        input=user_message,  # Pass string directly when using session
        context=runner.context,
        max_turns=settings.max_turns,
        session=runner.session,
    )

    await runner.print("Done!")
    return result.final_output


async def main():
    print("Running static flow with predefined inputs...")
    result = await vibecore.run("hi")
    print(f"Final output: {result}")
    print("*" * 40)
    print("Running interactive CLI flow...")
    result = await vibecore.run_cli()
    print(f"Final output: {result}")


if __name__ == "__main__":
    asyncio.run(main())
