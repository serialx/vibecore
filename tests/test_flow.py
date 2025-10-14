import asyncio

import pytest

from vibecore.flow import Vibecore, VibecoreRunner


@pytest.mark.asyncio
async def test_concurrent_runs_isolated_inputs():
    vibecore = Vibecore[None, str]()

    @vibecore.workflow()
    async def logic(
        runner: VibecoreRunner[None, str],
        user_message: str,
    ) -> str:
        return f"Response: {user_message}"

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
