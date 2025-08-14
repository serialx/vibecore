"""Vibecore CLI interface using typer."""

import logging
from importlib.metadata import version
from pathlib import Path

import typer
from textual.logging import TextualHandler

from vibecore.agents.default import create_default_agent
from vibecore.context import VibecoreContext
from vibecore.main import VibecoreApp
from vibecore.mcp import MCPManager
from vibecore.settings import settings

app = typer.Typer()


def version_callback(value: bool):
    """Handle --version flag."""
    if value:
        try:
            pkg_version = version("vibecore")
        except Exception:
            pkg_version = "unknown"
        typer.echo(f"vibecore {pkg_version}")
        raise typer.Exit()


def find_latest_session(project_path: Path | None = None, base_dir: Path | None = None) -> str | None:
    """Find the most recent session file for the current project."""
    from vibecore.session.path_utils import canonicalize_path
    from vibecore.settings import settings

    # Use provided paths or defaults
    if project_path is None:
        project_path = Path.cwd()
    if base_dir is None:
        base_dir = settings.session.base_dir

    # Get the session directory for this project
    canonical_project = canonicalize_path(project_path)
    session_dir = base_dir / "projects" / canonical_project

    if not session_dir.exists():
        return None

    # Find all session files
    session_files = list(session_dir.glob("chat-*.jsonl"))
    if not session_files:
        return None

    # Sort by modification time (most recent first)
    session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Return the session ID (filename without extension)
    return session_files[0].stem


@app.command()
def run(
    prompt: str | None = typer.Argument(None, help="Prompt text (requires -p flag)"),
    continue_session: bool = typer.Option(
        False,
        "--continue",
        "-c",
        help="Continue the most recent session for this project",
    ),
    session_id: str | None = typer.Option(
        None,
        "--session",
        "-s",
        help="Continue a specific session by ID",
    ),
    print_mode: bool = typer.Option(
        False,
        "--print",
        "-p",
        help="Print response and exit (useful for pipes)",
    ),
    version: bool | None = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Run the Vibecore TUI application."""
    # Set up logging
    logging.basicConfig(
        level="WARNING",
        handlers=[TextualHandler()],
    )

    logger = logging.getLogger("openai.agents")
    logger.addHandler(TextualHandler())

    # Create context
    ctx = VibecoreContext()

    # Initialize MCP manager if configured
    mcp_servers = []
    if settings.mcp_servers:
        # Create MCP manager
        mcp_manager = MCPManager(settings.mcp_servers)
        ctx.mcp_manager = mcp_manager

        # Get the MCP servers from the manager
        mcp_servers = mcp_manager.servers

    # Create agent with MCP servers
    agent = create_default_agent(mcp_servers=mcp_servers)

    # Determine session to use
    session_to_load = None
    if continue_session:
        session_to_load = find_latest_session()
        if not session_to_load:
            typer.echo("No existing sessions found for this project.")
            raise typer.Exit(1)
        typer.echo(f"Continuing session: {session_to_load}")
    elif session_id:
        session_to_load = session_id
        typer.echo(f"Loading session: {session_to_load}")

    # Create app
    app_instance = VibecoreApp(ctx, agent, session_id=session_to_load, print_mode=print_mode)

    if print_mode:
        # Run in print mode
        import asyncio

        # Use provided prompt or None to read from stdin
        result = asyncio.run(app_instance.run_print(prompt))
        # Print raw output to stdout
        if result:
            print(result)
    else:
        # Run normal TUI mode
        app_instance.run()


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
