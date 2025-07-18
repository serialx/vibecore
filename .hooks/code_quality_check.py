#!/usr/bin/env python3
"""
Code quality check hook for PostToolUse and Stop events.

Supports two modes:
1. PostToolUse: Checks specific modified files
2. Stop: Checks all project files

Runs: ruff format → ruff check → pyright
Exits with code 2 on lint errors.

Command-line flags:
  --format        Run ruff format (default: True)
  --check         Run ruff check (default: True)
  --pyright       Run pyright (default: True)
  --skip-format   Skip ruff format
  --skip-check    Skip ruff check
  --skip-pyright  Skip pyright

Usage examples:
  # Run all checks (default)
  uv run hooks/code_quality_check.py

  # Skip pyright only
  uv run hooks/code_quality_check.py --skip-pyright

  # Run only pyright
  uv run hooks/code_quality_check.py --skip-format --skip-check

Setup in `.claude/settings.json`:

PostToolUse hook (check modified files):
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "uv run hooks/code_quality_check.py"
      }]
    }]
  }
}
```

Stop hook (check all files when session ends):
```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run hooks/code_quality_check.py"
      }]
    }]
  }
}
```

Combined setup with different configurations:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "uv run hooks/code_quality_check.py --skip-format --skip-check"
      }]
    }],
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uv run hooks/code_quality_check.py"
      }]
    }]
  }
}
```

Input formats (JSON via stdin):

PostToolUse event:
```json
{
  "tool_name": "Write|Edit|MultiEdit",
  "tool_input": {
    "file_path": "/path/to/file.py",
    "content": "...",     // Write
    "old_string": "...",  // Edit
    "new_string": "...",  // Edit
    "edits": [...]        // MultiEdit
  },
  "tool_output": "...",
  "error": null
}
```

Stop event:
```json
{
  "session_id": "abc123",
  "transcript_path": "path/to/transcript.jsonl",
  "stop_hook_active": true
}
```

Docs: https://docs.anthropic.com/en/docs/claude-code/hooks
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Code quality check hook with selective tool execution")

    # Positive flags (enable tools, all default to True)
    parser.add_argument(
        "--format",
        action="store_true",
        default=True,
        help="Run ruff format (default: True)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=True,
        help="Run ruff check (default: True)",
    )
    parser.add_argument(
        "--pyright",
        action="store_true",
        default=True,
        help="Run pyright (default: True)",
    )

    # Negative flags (disable tools)
    parser.add_argument(
        "--skip-format",
        action="store_false",
        dest="format",
        help="Skip ruff format",
    )
    parser.add_argument(
        "--skip-check",
        action="store_false",
        dest="check",
        help="Skip ruff check",
    )
    parser.add_argument(
        "--skip-pyright",
        action="store_false",
        dest="pyright",
        help="Skip pyright",
    )

    return parser.parse_args()


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run command, return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def run_checks(target: str, args, is_all_files: bool = False):
    """Run quality checks on specified target.

    Args:
        target: File path or "." for all files
        args: Command-line arguments
        is_all_files: Whether checking all files (affects messaging)
    """
    # Track errors
    ruff_has_errors = False
    pyright_has_errors = False

    # Determine scope message suffix
    scope = " on all files" if is_all_files else ""

    # Run ruff format
    if args.format:
        print(f"\n🔧 Running ruff format{scope}...", file=sys.stderr)
        exit_code, stdout, stderr = run_command(["uv", "run", "ruff", "format", target])
        if stdout:
            print(stdout, file=sys.stderr)
        if stderr:
            print(stderr, file=sys.stderr)

    # Run ruff check
    if args.check:
        print(f"\n🔍 Running ruff check{scope}...", file=sys.stderr)
        exit_code, stdout, stderr = run_command(["uv", "run", "ruff", "check", "--fix", target])
        ruff_has_errors = exit_code != 0
        if stdout:
            print(stdout, file=sys.stderr)
        if stderr:
            print(stderr, file=sys.stderr)

    # Run pyright
    if args.pyright:
        print(f"\n📊 Running pyright{scope}...", file=sys.stderr)
        exit_code, stdout, stderr = run_command(["uv", "run", "pyright", target])
        pyright_has_errors = exit_code != 0
        if stdout:
            print(stdout, file=sys.stderr)
        if stderr:
            print(stderr, file=sys.stderr)

    # Exit with code 2 to block on errors
    if ruff_has_errors or pyright_has_errors:
        print("\n❌ Lint errors detected!", file=sys.stderr)
        sys.exit(2)
    else:
        print("\n✅ All checks passed!", file=sys.stderr)
        sys.exit(0)


def check_all_files(args):
    """Check all Python files in the project (Stop event)."""
    run_checks(".", args, is_all_files=True)


def check_single_file(file_path: Path, args):
    """Check a single Python file."""
    print(f"Running code quality checks on: {file_path}", file=sys.stderr)
    run_checks(str(file_path), args, is_all_files=False)


def main():
    """Process tool use and run quality checks on Python files."""
    # Parse command-line arguments
    args = parse_args()

    # Read JSON input from stdin
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine if this is a Stop event or PostToolUse event
    is_stop_event = "stop_hook_active" in input_data

    if is_stop_event:
        # Stop event: check all files in the project
        print("Running code quality checks on all project files...", file=sys.stderr)
        check_all_files(args)
    else:
        # PostToolUse event: check specific file
        # Only process file-related tools
        tool_name = input_data.get("tool_name", "")
        if tool_name not in ["Write", "Edit", "MultiEdit"]:
            # Skip non-file tools
            sys.exit(0)

        # Extract file path from tool_input
        tool_input = input_data.get("tool_input", {})
        if not isinstance(tool_input, dict):
            # Skip invalid input
            sys.exit(0)

        # Handle both file_path and notebook_path
        file_path = tool_input.get("file_path") or tool_input.get("notebook_path")

        if not file_path:
            # Skip if no path
            sys.exit(0)

        file_path = Path(file_path)

        # Only check Python files
        if file_path.suffix not in [".py", ".pyi"]:
            sys.exit(0)

        # Check if file exists
        if not file_path.exists():
            print(f"File not found: {file_path}", file=sys.stderr)
            sys.exit(0)

        check_single_file(file_path, args)


if __name__ == "__main__":
    main()
