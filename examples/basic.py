import asyncio

from agents import Agent, Session

from vibecore.context import VibecoreContext
from vibecore.flow import Vibecore
from vibecore.settings import settings
from vibecore.tools.file.tools import read
from vibecore.tools.shell.tools import glob, grep, ls
from vibecore.tools.todo.tools import todo_read, todo_write

agent = Agent[VibecoreContext](
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


vibecore: Vibecore[str] = Vibecore(agent)


@vibecore.workflow()
async def logic(session: Session) -> str:
    user_message = await vibecore.user_input("Input your message:")
    await vibecore.print(f"Starting generation of '{user_message}'...")
    result = await vibecore.run_agent(
        agent,
        input=user_message,  # Pass string directly when using session
        context=vibecore.context,
        max_turns=settings.max_turns,
        session=session,
    )

    await vibecore.print("Done!")
    return result.final_output


async def main():
    result = await vibecore.run_textual(shutdown=False)
    print(f"Final output: {result}")


if __name__ == "__main__":
    asyncio.run(main())
