import asyncio
from typing import cast

import pytest
from agents import Agent

from vibecore.flow import Vibecore, VibecoreRunnerBase


@pytest.mark.asyncio
async def test_concurrent_runs_isolated_inputs():
    vibecore = Vibecore[None, str]()

    @vibecore.workflow()
    async def logic(
        runner: VibecoreRunnerBase[None, str],
    ) -> str:
        message = await runner.user_input()
        return f"Response: {message}"

    results = await asyncio.gather(
        vibecore.run("input1"),
        vibecore.run("input2"),
        vibecore.run("input3"),
    )

    assert results == [
        "Response: input1",
        "Response: input2",
        "Response: input3",
    ]


@pytest.mark.asyncio
async def test_run_agent_method_removed():
    vibecore = Vibecore[None, None]()

    with pytest.raises(RuntimeError):
        await vibecore.run_agent(cast(Agent[None], object()), input="message")
