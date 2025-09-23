# Repository Guidelines

## Project Structure & Module Organization
- `src/vibecore` holds the app (`main.py`), Flow Mode orchestration (`flow.py`), and subpackages for agents, tools, widgets, session, models, and mcp.
- Entry points are `cli.py` and `main.py`; defaults and prompts live in `settings.py` and `prompts/`.
- Flow and multi-agent samples are under `examples/`; reference docs stay in `docs/`.
- Tests mirror runtime modules in `tests/`, with fixtures in `tests/fixtures` and harness helpers in `tests/_harness`.

## Build, Test, and Development Commands
- `uv sync` — provision the dev environment against `uv.lock`.
- `uv run vibecore` — launch the TUI locally; (NEVER RUN THIS)
- `uv run vibecore --print -p 'prompt'` — launch vibecore in pipe mode. non-TUI. (USE THIS INSTEAD OF TUI)
- `uv run pytest …` — run the suite or scoped folders like `tests/ui`.
- `uv run ruff check .` / `uv run ruff format .` — lint and auto-format.
- `uv run pyright` — type-check before requesting review.

## Coding Style & Naming Conventions
- Python 3.11, 4-space indentation, 120-character lines, double quotes via Ruff.
- Use snake_case for modules, functions, variables; PascalCase for classes and TypedDicts.
- Keep public APIs typed—`py.typed` means downstream users rely on annotations.
- Place new tools, widgets, or agents beside existing peers to keep modules focused.

## Testing Guidelines
- pytest runs in strict asyncio mode; decorate async tests with `pytest.mark.asyncio`.
- Name files `test_*.py`, reuse fixtures, and mirror new runtime code with matching tests.
- UI changes touching message widgets must refresh `tests/ui/test_message_snapshots.py`.
- Run full `uv run pytest` plus targeted suites before opening a PR.

## Textual & UI Development Tips
- Consult Textual source in `.venv/lib/python3.11/site-packages/textual/` when extending widgets—docs lag the implementation.
- Textual ignores CSS `@keyframes`; use widget `animate()` helpers for motion.
- Streaming handlers in `handlers/` expect incremental updates—ensure new widgets cooperate with that flow.

## Commit & Pull Request Guidelines
- Follow conventional commits (`feat:`, `fix:`, `chore:`, `release:`) as seen in the log.
- Keep commits scoped and explain non-obvious intent; PRs should summarize behavior changes, link issues, and include UI screenshots when relevant.
- Verify `pytest`, `ruff check`, `ruff format`, and `pyright` locally before asking for review.

## Configuration & Secrets
- Provide `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` via env vars or `config.yaml`.
- Never commit secrets—prefer `.env` files or shell exports ignored by git.
- Document new integrations in `docs/` and extend `settings.py` with safe defaults for configuration.
