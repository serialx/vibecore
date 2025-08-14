import asyncio
import threading
from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any

from agents import Agent
from textual.pilot import Pilot

from vibecore.context import VibecoreContext
from vibecore.main import VibecoreApp
from vibecore.widgets.core import MyTextArea


@asynccontextmanager
async def flow(
    agent: Agent, headless: bool = False, shutdown: bool = False
) -> AsyncGenerator[tuple[VibecoreApp, VibecoreContext, Callable[[], Coroutine[Any, Any, str]]], None]:
    ctx = VibecoreContext()
    app = VibecoreApp(ctx, agent)

    app_ready_event = asyncio.Event()

    def on_app_ready() -> None:
        """Called when app is ready to process events."""
        app_ready_event.set()

    async def run_app(app: VibecoreApp) -> None:
        """Run the apps message loop.

        Args:
            app: App to run.
        """

        with app._context():
            try:
                app._loop = asyncio.get_running_loop()
                app._thread_id = threading.get_ident()
                await app._process_messages(
                    ready_callback=on_app_ready,
                    headless=headless,
                )
            finally:
                app_ready_event.set()

    async def user_input() -> str:
        app.query_one(MyTextArea).disabled = False
        app.query_one(MyTextArea).focus()
        user_input = await app.wait_for_user_input()
        app.query_one(MyTextArea).disabled = True
        return user_input

    app_task = asyncio.create_task(run_app(app), name=f"with_app({app})")
    await app_ready_event.wait()
    pilot = Pilot(app)
    try:
        await pilot._wait_for_screen()
        app.query_one(MyTextArea).disabled = True
        yield (app, ctx, user_input)
    finally:
        if shutdown:
            if not headless:
                await pilot._wait_for_screen()
                await asyncio.sleep(1.0)
                await app.action_quit()
                await asyncio.sleep(1.0)
            await app._shutdown()

        # Enable text input so users can interact freely
        app.query_one(MyTextArea).disabled = True
        await app_task
