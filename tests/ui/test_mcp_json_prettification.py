"""Tests for MCP tool message JSON prettification."""

import json

from vibecore.widgets.tool_messages import MCPToolMessage


class TestMCPJsonPrettification:
    """Test JSON prettification in MCP tool messages."""

    def test_prettify_valid_json_object(self):
        """Test that valid JSON objects are prettified correctly."""
        msg = MCPToolMessage(
            server_name="api",
            tool_name="get_data",
            arguments="{}",
            output='{"name": "test", "value": 123}',
        )

        is_json, formatted = msg._prettify_json_output(msg.output)

        assert is_json is True
        expected = json.dumps({"name": "test", "value": 123}, indent=2, ensure_ascii=False)
        assert formatted == expected
        assert "\n" in formatted  # Should have newlines for formatting

    def test_prettify_valid_json_array(self):
        """Test that valid JSON arrays are prettified correctly."""
        msg = MCPToolMessage(
            server_name="api",
            tool_name="list_items",
            arguments="{}",
            output='["item1", "item2", "item3"]',
        )

        is_json, formatted = msg._prettify_json_output(msg.output)

        assert is_json is True
        expected = json.dumps(["item1", "item2", "item3"], indent=2, ensure_ascii=False)
        assert formatted == expected

    def test_prettify_nested_json(self):
        """Test that nested JSON structures are prettified correctly."""
        nested_data = {
            "user": {"id": 1, "name": "Alice"},
            "items": [{"id": 101, "name": "Item 1"}, {"id": 102, "name": "Item 2"}],
            "metadata": {"created": "2024-01-01", "version": "1.0"},
        }
        msg = MCPToolMessage(
            server_name="api",
            tool_name="get_complex",
            arguments="{}",
            output=json.dumps(nested_data),  # Compact JSON
        )

        is_json, formatted = msg._prettify_json_output(msg.output)

        assert is_json is True
        expected = json.dumps(nested_data, indent=2, ensure_ascii=False)
        assert formatted == expected
        assert formatted.count("\n") > 5  # Should have multiple newlines

    def test_prettify_invalid_json(self):
        """Test that invalid JSON is returned as-is."""
        msg = MCPToolMessage(
            server_name="api",
            tool_name="get_text",
            arguments="{}",
            output="This is not JSON: {invalid}",
        )

        is_json, formatted = msg._prettify_json_output(msg.output)

        assert is_json is False
        assert formatted == msg.output  # Should return unchanged

    def test_prettify_empty_output(self):
        """Test that empty output is handled correctly."""
        msg = MCPToolMessage(
            server_name="api",
            tool_name="no_output",
            arguments="{}",
            output="",
        )

        is_json, formatted = msg._prettify_json_output(msg.output)

        assert is_json is False
        assert formatted == ""

    def test_prettify_whitespace_only(self):
        """Test that whitespace-only output is handled correctly."""
        msg = MCPToolMessage(
            server_name="api",
            tool_name="whitespace",
            arguments="{}",
            output="   \n\t  ",
        )

        is_json, formatted = msg._prettify_json_output(msg.output)

        assert is_json is False
        assert formatted == "   \n\t  "

    def test_prettify_json_with_unicode(self):
        """Test that JSON with Unicode characters is handled correctly."""
        unicode_data = {"name": "José", "city": "São Paulo", "emoji": "🚀"}
        msg = MCPToolMessage(
            server_name="api",
            tool_name="unicode_test",
            arguments="{}",
            output=json.dumps(unicode_data, ensure_ascii=True),  # Escaped unicode
        )

        is_json, formatted = msg._prettify_json_output(msg.output)

        assert is_json is True
        # Should preserve unicode characters
        assert "José" in formatted
        assert "São Paulo" in formatted
        assert "🚀" in formatted

    def test_prettify_arguments_json(self):
        """Test that JSON arguments are also prettified."""
        args = {"key1": "value1", "key2": {"nested": "value"}}
        msg = MCPToolMessage(
            server_name="api",
            tool_name="test",
            arguments=json.dumps(args),
            output="result",
        )

        is_json, formatted = msg._prettify_json_output(msg.arguments)

        assert is_json is True
        expected = json.dumps(args, indent=2, ensure_ascii=False)
        assert formatted == expected

    def test_prettify_malformed_json(self):
        """Test various forms of malformed JSON."""
        test_cases = [
            '{"unclosed": ',
            '{"key": undefined}',
            "{'single': 'quotes'}",  # JSON requires double quotes
            "{key: value}",  # Keys must be quoted
            '{"trailing": "comma",}',
        ]

        for malformed in test_cases:
            msg = MCPToolMessage(
                server_name="api",
                tool_name="test",
                arguments="{}",
                output=malformed,
            )

            is_json, formatted = msg._prettify_json_output(msg.output)

            assert is_json is False, f"Should not parse as JSON: {malformed}"
            assert formatted == malformed, f"Should return unchanged: {malformed}"

    def test_prettify_json_primitives(self):
        """Test that JSON primitives are handled correctly."""
        primitives = [
            ("123", 123),
            ("true", True),
            ("false", False),
            ("null", None),
            ('"string"', "string"),
        ]

        for json_str, expected_value in primitives:
            msg = MCPToolMessage(
                server_name="api",
                tool_name="test",
                arguments="{}",
                output=json_str,
            )

            is_json, formatted = msg._prettify_json_output(msg.output)

            assert is_json is True, f"Should parse as JSON: {json_str}"
            # Primitives should be formatted consistently
            assert formatted == json.dumps(expected_value, indent=2, ensure_ascii=False)
