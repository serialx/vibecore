"""Test loading the specific JSONL format provided by the user."""

# ruff: noqa: E501

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from agents.result import RunResultBase

from vibecore.context import AppAwareContext
from vibecore.flow import Vibecore, VibecoreTextualRunner
from vibecore.main import VibecoreApp
from vibecore.widgets.messages import AgentMessage, MessageStatus, UserMessage
from vibecore.widgets.tool_messages import PythonToolMessage, ToolMessage


@pytest.mark.asyncio
async def test_load_jsonl_format():
    """Test loading history with the exact JSONL format provided."""
    # Exact session data from the user's JSONL
    session_items = [
        {"content": "hi", "role": "user"},
        {
            "id": "__fake_id__",
            "content": [
                {
                    "annotations": [],
                    "text": (
                        "Hi! I'm here to help you with data engineering and analysis tasks. "
                        "I can assist with SQL queries, Python data analysis, file processing, "
                        "and more. What would you like to work on?"
                    ),
                    "type": "output_text",
                }
            ],
            "role": "assistant",
            "status": "completed",
            "type": "message",
        },
        {"content": "good", "role": "user"},
        {
            "id": "__fake_id__",
            "content": [
                {
                    "annotations": [],
                    "text": (
                        "Great! Let me know what data task you'd like to tackle - whether it's "
                        "analyzing a dataset, running SQL queries, processing files, or "
                        "anything else data-related."
                    ),
                    "type": "output_text",
                }
            ],
            "role": "assistant",
            "status": "completed",
            "type": "message",
        },
        {"content": "great!", "role": "user"},
        {
            "id": "__fake_id__",
            "content": [
                {
                    "annotations": [],
                    "text": "Ready when you are! What data engineering or analysis task can I help you with today?",
                    "type": "output_text",
                }
            ],
            "role": "assistant",
            "status": "completed",
            "type": "message",
        },
        {"content": "Show me python demo", "role": "user"},
        {
            "id": "__fake_id__",
            "content": [{"annotations": [], "text": "", "type": "output_text"}],
            "role": "assistant",
            "status": "completed",
            "type": "message",
        },
        {
            "arguments": (
                '{"code": "# Python demo - data analysis basics\\nimport pandas as pd\\n'
                "import numpy as np\\nimport matplotlib.pyplot as plt\\n\\n# Create sample data\\n"
                "data = {\\n    'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],\\n"
                "    'age': [25, 30, 35, 28, 32],\\n    'salary': [50000, 65000, 80000, 55000, 70000],\\n"
                "    'department': ['Engineering', 'Marketing', 'Engineering', 'HR', 'Marketing']\\n}\\n\\n"
                'df = pd.DataFrame(data)\\nprint(\\"Sample DataFrame:\\")\\nprint(df)\\n'
                'print(\\"\\\\nBasic statistics:\\")\\nprint(df.describe())"}'
            ),
            "call_id": "toolu_019BiZPmLf8xhzzbFXK467Vq",
            "name": "execute_python",
            "type": "function_call",
            "id": "__fake_id__",
        },
        {
            "call_id": "toolu_019BiZPmLf8xhzzbFXK467Vq",
            "output": "Error:\n```\nModuleNotFoundError: No module named 'pandas'```",
            "type": "function_call_output",
        },
        {
            "id": "__fake_id__",
            "content": [{"annotations": [], "text": "", "type": "output_text"}],
            "role": "assistant",
            "status": "completed",
            "type": "message",
        },
        {
            "arguments": r'{"code": "# Python demo with built-in libraries\nimport json\nimport random\n\n# Create sample data\nemployees = [\n    {\'name\': \'Alice\', \'age\': 25, \'salary\': 50000, \'department\': \'Engineering\'},\n    {\'name\': \'Bob\', \'age\': 30, \'salary\': 65000, \'department\': \'Marketing\'},\n    {\'name\': \'Charlie\', \'age\': 35, \'salary\': 80000, \'department\': \'Engineering\'},\n    {\'name\': \'Diana\', \'age\': 28, \'salary\': 55000, \'department\': \'HR\'},\n    {\'name\': \'Eve\', \'age\': 32, \'salary\': 70000, \'department\': \'Marketing\'}\n]\n\nprint(\"Employee Data:\")\nfor emp in employees:\n    print(f\"{emp[\'name\']}: {emp[\'age\']} years, ${emp[\'salary\']:,}, {emp[\'department\']}\")\n\n# Calculate average salary by department\ndepartments = {}\nfor emp in employees:\n    dept = emp[\'department\']\n    if dept not in departments:\n        departments[dept] = []\n    departments[dept].append(emp[\'salary\'])\n\nprint(\"\\nAverage salary by department:\")\nfor dept, salaries in departments.items():\n    avg_salary = sum(salaries) / len(salaries)\n    print(f\"{dept}: ${avg_salary:,.0f}\")\n\n# Generate random numbers\nprint(f\"\\nRandom sample: {[random.randint(1, 100) for _ in range(5)]}\")"}',
            "call_id": "toolu_01S4Nnj8gvML8t2BMeKy7JHX",
            "name": "execute_python",
            "type": "function_call",
            "id": "__fake_id__",
        },
        {
            "call_id": "toolu_01S4Nnj8gvML8t2BMeKy7JHX",
            "output": "Output:\n```\nEmployee Data:\nAlice: 25 years, $50,000, Engineering\nBob: 30 years, $65,000, Marketing\nCharlie: 35 years, $80,000, Engineering\nDiana: 28 years, $55,000, HR\nEve: 32 years, $70,000, Marketing\n\nAverage salary by department:\nEngineering: $65,000\nMarketing: $67,500\nHR: $55,000\n\nRandom sample: [3, 24, 89, 11, 87]\n```",
            "type": "function_call_output",
        },
        {
            "id": "__fake_id__",
            "content": [
                {
                    "annotations": [],
                    "text": "Python demo complete! Shows data manipulation, calculations, and basic analysis using built-in libraries.",
                    "type": "output_text",
                }
            ],
            "role": "assistant",
            "status": "completed",
            "type": "message",
        },
    ]

    mock_session = AsyncMock()
    mock_session.get_items.return_value = session_items

    # Create app instance
    vibecore = Vibecore()
    runner = VibecoreTextualRunner(
        cast("Vibecore[AppAwareContext, RunResultBase]", vibecore),
        context=None,
        session=None,
    )

    app = VibecoreApp(runner)

    # Mock the query methods
    app.query_one = MagicMock()
    mock_messages = MagicMock()
    mock_messages.query.return_value = []  # No Welcome widget
    app.query_one.return_value = mock_messages

    # Track added messages
    added_messages = []
    app.add_message = AsyncMock(side_effect=lambda msg: added_messages.append(msg))

    # Load history
    await app.load_session_history(mock_session)

    # Verify correct number of messages
    # Expected: 4 user, 3 non-empty assistant, 2 tool messages, 1 final assistant = 10 total
    assert len(added_messages) == 10

    # Check message order and types
    assert isinstance(added_messages[0], UserMessage)
    assert added_messages[0].text == "hi"

    assert isinstance(added_messages[1], AgentMessage)
    assert "I'm here to help you with data engineering" in added_messages[1].text

    assert isinstance(added_messages[2], UserMessage)
    assert added_messages[2].text == "good"

    assert isinstance(added_messages[3], AgentMessage)
    assert "Great! Let me know what data task" in added_messages[3].text

    assert isinstance(added_messages[4], UserMessage)
    assert added_messages[4].text == "great!"

    assert isinstance(added_messages[5], AgentMessage)
    assert "Ready when you are!" in added_messages[5].text

    assert isinstance(added_messages[6], UserMessage)
    assert added_messages[6].text == "Show me python demo"

    # Check tool messages
    assert isinstance(added_messages[7], PythonToolMessage)
    assert "ModuleNotFoundError" in added_messages[7].output
    assert added_messages[7].status == MessageStatus.SUCCESS

    # This might be ToolMessage if JSON parsing fails, or PythonToolMessage if it succeeds
    assert isinstance(added_messages[8], ToolMessage | PythonToolMessage)
    assert "Employee Data:" in added_messages[8].output
    assert added_messages[8].status == MessageStatus.SUCCESS

    # The last assistant message
    assert isinstance(added_messages[9], AgentMessage)
    assert "Python demo complete!" in added_messages[9].text


@pytest.mark.asyncio
async def test_load_session_with_function_calls():
    """Test loading session format focusing on function calls and outputs."""
    # Session data focusing on function calls
    session_items = [
        {
            "id": "__fake_id__",
            "content": [{"annotations": [], "text": "", "type": "output_text"}],
            "role": "assistant",
            "status": "completed",
            "type": "message",
        },
        {
            "arguments": '{"code": "# Python demo\\nimport pandas as pd\\nprint(\\"test\\")"}',
            "call_id": "toolu_019BiZPmLf8xhzzbFXK467Vq",
            "name": "execute_python",
            "type": "function_call",
            "id": "__fake_id__",
        },
        {
            "call_id": "toolu_019BiZPmLf8xhzzbFXK467Vq",
            "output": "Error:\n```\nModuleNotFoundError: No module named 'pandas'```",
            "type": "function_call_output",
        },
        {"role": "user", "content": "Try again with built-in libraries"},
        {
            "arguments": '{"code": "# Python demo with built-in libraries\\nimport json\\nprint(\\"Success!\\")"}',
            "call_id": "toolu_01S4Nnj8gvML8t2BMeKy7JHX",
            "name": "execute_python",
            "type": "function_call",
            "id": "__fake_id__",
        },
        {
            "call_id": "toolu_01S4Nnj8gvML8t2BMeKy7JHX",
            "output": "Output:\n```\nSuccess!\n```",
            "type": "function_call_output",
        },
    ]

    mock_session = AsyncMock()
    mock_session.get_items.return_value = session_items

    # Create app instance
    vibecore = Vibecore()
    runner = VibecoreTextualRunner(
        cast("Vibecore[AppAwareContext, RunResultBase]", vibecore),
        context=None,
        session=None,
    )

    app = VibecoreApp(runner)

    # Mock the query methods
    app.query_one = MagicMock()
    mock_messages = MagicMock()
    mock_messages.query.return_value = []  # No Welcome widget
    app.query_one.return_value = mock_messages

    # Track added messages
    added_messages = []
    app.add_message = AsyncMock(side_effect=lambda msg: added_messages.append(msg))

    # Load history
    await app.load_session_history(mock_session)

    # Verify correct messages were added (should skip empty assistant messages)
    assert len(added_messages) == 3  # 1 user + 2 tool messages

    # Check first tool message (with error)
    assert isinstance(added_messages[0], PythonToolMessage)
    assert "ModuleNotFoundError" in added_messages[0].output
    assert added_messages[0].status == MessageStatus.SUCCESS

    # Check user message
    assert isinstance(added_messages[1], UserMessage)
    assert added_messages[1].text == "Try again with built-in libraries"

    # Check second tool message (successful)
    assert isinstance(added_messages[2], PythonToolMessage)
    assert "Success!" in added_messages[2].output
    assert added_messages[2].status == MessageStatus.SUCCESS
