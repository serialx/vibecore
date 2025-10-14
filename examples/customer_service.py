from __future__ import annotations as _annotations

import asyncio
import random
import uuid

from agents import (
    Agent,
    HandoffOutputItem,
    RunContextWrapper,
    function_tool,
    handoff,
    trace,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel

from vibecore.flow import Vibecore, VibecoreRunnerBase

### CONTEXT


class AirlineAgentContext(BaseModel):
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None


### TOOLS


@function_tool(name_override="faq_lookup_tool", description_override="Lookup frequently asked questions.")
async def faq_lookup_tool(question: str) -> str:
    question_lower = question.lower()
    if any(
        keyword in question_lower for keyword in ["bag", "baggage", "luggage", "carry-on", "hand luggage", "hand carry"]
    ):
        return (
            "You are allowed to bring one bag on the plane. "
            "It must be under 50 pounds and 22 inches x 14 inches x 9 inches."
        )
    elif any(keyword in question_lower for keyword in ["seat", "seats", "seating", "plane"]):
        return (
            "There are 120 seats on the plane. "
            "There are 22 business class seats and 98 economy seats. "
            "Exit rows are rows 4 and 16. "
            "Rows 5-8 are Economy Plus, with extra legroom. "
        )
    elif any(
        keyword in question_lower for keyword in ["wifi", "internet", "wireless", "connectivity", "network", "online"]
    ):
        return "We have free wifi on the plane, join Airline-Wifi"
    return "I'm sorry, I don't know the answer to that question."


@function_tool
async def update_seat(context: RunContextWrapper[AirlineAgentContext], confirmation_number: str, new_seat: str) -> str:
    """
    Update the seat for a given confirmation number.

    Args:
        confirmation_number: The confirmation number for the flight.
        new_seat: The new seat to update to.
    """
    # Update the context based on the customer's input
    context.context.confirmation_number = confirmation_number
    context.context.seat_number = new_seat
    # Ensure that the flight number has been set by the incoming handoff
    assert context.context.flight_number is not None, "Flight number is required"
    return f"Updated seat to {new_seat} for confirmation number {confirmation_number}"


### HOOKS


async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentContext]) -> None:
    flight_number = f"FLT-{random.randint(100, 999)}"
    context.context.flight_number = flight_number


### AGENTS

faq_agent = Agent[AirlineAgentContext](
    name="FAQ Agent",
    handoff_description="A helpful agent that can answer questions about the airline.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are an FAQ agent. If you are speaking to a customer, you probably were transferred to from the triage agent.
    Use the following routine to support the customer.
    # Routine
    1. Identify the last question asked by the customer.
    2. Use the faq lookup tool to answer the question. Do not rely on your own knowledge.
    3. If you cannot answer the question, transfer back to the triage agent.""",
    tools=[faq_lookup_tool],
)

seat_booking_agent = Agent[AirlineAgentContext](
    name="Seat Booking Agent",
    handoff_description="A helpful agent that can update a seat on a flight.",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a seat booking agent. If you are speaking to a customer, you were transferred to from the triage agent.
    Use the following routine to support the customer.
    # Routine
    1. Ask for their confirmation number.
    2. Ask the customer what their desired seat number is.
    3. Use the update seat tool to update the seat on the flight.
    If the customer asks a question that is not related to the routine, transfer back to the triage agent. """,
    tools=[update_seat],
)

triage_agent = Agent[AirlineAgentContext](
    name="Triage Agent",
    handoff_description="A triage agent that can delegate a customer's request to the appropriate agent.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX} "
        "You are a helpful triaging agent. You can use your tools to delegate questions to other appropriate agents."
    ),
    handoffs=[
        faq_agent,
        handoff(agent=seat_booking_agent, on_handoff=on_seat_booking_handoff),
    ],
)

faq_agent.handoffs.append(triage_agent)
seat_booking_agent.handoffs.append(triage_agent)


### RUN

vibecore = Vibecore[AirlineAgentContext, None]()


@vibecore.workflow()
async def logic(
    runner: VibecoreRunnerBase[AirlineAgentContext, None],
) -> None:
    current_agent: Agent[AirlineAgentContext] = triage_agent
    context = AirlineAgentContext()

    # Normally, each input from the user would be an API request to your app, and you can wrap the request in a trace()
    # Here, we'll just use a random UUID for the conversation ID
    conversation_id = uuid.uuid4().hex[:16]

    while True:
        user_input_ = await runner.user_input()
        with trace("Customer service", group_id=conversation_id):
            result = await runner.run_agent(
                current_agent,
                input=user_input_,
                context=context,
                session=runner.session,
            )

            for new_item in result.new_items:
                if isinstance(new_item, HandoffOutputItem):
                    message = f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}"
                    await runner.print(message)
            current_agent = result.last_agent


async def main():
    await vibecore.run_textual(shutdown=False)


if __name__ == "__main__":
    asyncio.run(main())
