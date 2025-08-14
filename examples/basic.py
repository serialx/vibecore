import asyncio

from agents import Agent, Runner

from vibecore.context import VibecoreContext
from vibecore.flow import flow
from vibecore.main import SystemMessage
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


async def main():
    async with flow(agent) as (app, ctx, user_input):
        await app.add_message(SystemMessage("Input your message:"))
        user_message = await user_input()
        await app.add_message(SystemMessage(f"Starting generation of '{user_message}'..."))
        result = Runner.run_streamed(
            agent,
            input=user_message,  # Pass string directly when using session
            context=ctx,
            max_turns=settings.max_turns,
            session=app.session,
        )

        app.current_worker = app.handle_streamed_response(result)
        await app.current_worker.wait()
        await app.add_message(SystemMessage("Done!"))
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
