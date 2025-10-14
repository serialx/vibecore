# Migrating to Runner-as-Argument Workflows

This release refactors Flow Mode workflows so that the `runner` is passed as the
first argument to your workflow function. The change eliminates the shared
`Vibecore.runner` instance state and makes concurrent `Vibecore.run()` calls
safe by design.

## Why the Change?

- **Concurrency safety** – each workflow invocation receives its own runner
  instance, preventing race conditions across tasks.
- **Explicit dependencies** – the workflow signature clearly communicates that
  user interaction helpers come from the runner.
- **Simpler reasoning** – no more hidden state on the `Vibecore` object and no
  need for `ContextVar` indirection.

## Updated Workflow Signature

```python
@vibecore.workflow()
async def logic(
    runner: VibecoreRunnerBase[MyContext, MyResult],
) -> MyResult:
    ...
```

### What Moved to the Runner?

| Old API                       | New API                  | Notes                                   |
| ----------------------------- | ------------------------ | --------------------------------------- |
| `await vibecore.user_input()` | `await runner.user_input()` | Reads from CLI/Textual/static inputs      |
| `await vibecore.print()`      | `await runner.print()`      | Emits status messages                    |
| `await vibecore.run_agent()`  | `await runner.run_agent()`  | Runs agents with streaming + sessions    |

The `Vibecore.run_agent()` helper now raises a `RuntimeError` to surface the
breaking change early.

## Migration Steps

1. **Add `runner` as the first parameter** to every function decorated with
   `@vibecore.workflow()`.
2. **Update imports** to include `VibecoreRunnerBase` when you need explicit
   typing for the runner argument.
3. **Replace `vibecore.user_input/print/run_agent` calls** with the runner
   equivalents.
4. **Access context and session from the runner** via `runner.context` and
   `runner.session` when you need them.
5. **Re-run your tests** (including `uv run pyright`) to verify typing and
   runtime behavior.

## Before & After

**Before**

```python
@vibecore.workflow()
async def logic(context: MyContext | None, session: Session) -> str:
    message = await vibecore.user_input("Enter message:")
    await vibecore.print(f"Processing: {message}")
    result = await vibecore.run_agent(agent, message, context=context, session=session)
    return result.final_output
```

**After**

```python
@vibecore.workflow()
async def logic(
    runner: VibecoreRunnerBase[MyContext, RunResultBase],
) -> str:
    message = await runner.user_input("Enter message:")
    await runner.print(f"Processing: {message}")
    result = await runner.run_agent(
        agent,
        message,
        context=runner.context,
        session=runner.session,
    )
    return result.final_output
```

## Testing Checklist

- [ ] `uv run pytest`
- [ ] `uv run ruff check .`
- [ ] `uv run pyright`

All Flow Mode examples and docs in the repository have been updated to follow
the new runner-first convention. Use them as references while updating your
own applications.
