"""Common prompts and instructions for agents."""

from pathlib import Path


def load_common_prompt() -> str:
    """Load the common system prompt from file."""
    prompt_file = Path(__file__).parent.parent / "prompts" / "common_system_prompt.txt"
    return prompt_file.read_text()


COMMON_PROMPT = load_common_prompt()
