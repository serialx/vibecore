"""Text extraction utilities for vibecore."""

from openai.types.responses.response_output_message import Content
from openai.types.responses.response_output_refusal import ResponseOutputRefusal
from openai.types.responses.response_output_text import ResponseOutputText


class TextExtractor:
    """Utility class for extracting text from various content formats."""

    @staticmethod
    def extract_from_content(content: list[Content]) -> str:
        """Extract text from various content formats.

        Args:
            content: List of content items from OpenAI response

        Returns:
            Concatenated text from all text content items
        """
        text_parts = []
        for item in content:
            match item:
                case ResponseOutputText(text=text):
                    text_parts.append(text)
                case ResponseOutputRefusal(refusal=text):
                    text_parts.append(text)
        return "".join(text_parts)
