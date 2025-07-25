"""Vibecore CLI interface using typer."""

import logging
from pathlib import Path

import agents
import typer
from textual.logging import TextualHandler

from vibecore.agents.default import default_agent
from vibecore.context import VibecoreContext
from vibecore.main import VibecoreApp

app = typer.Typer()


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
):
    """Run the Vibecore TUI application."""
    # Set up logging
    logging.basicConfig(
        level="WARNING",
        handlers=[TextualHandler()],
    )

    logger = logging.getLogger("openai.agents")
    logger.addHandler(TextualHandler())

    agents.set_default_openai_api("chat_completions")

    # Create context
    ctx = VibecoreContext()

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

    # Create and run app
    app = VibecoreApp(ctx, default_agent, session_id=session_to_load)
    app.run()


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
