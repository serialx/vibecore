"""Python code execution manager."""

import ast
import sys
import warnings
from dataclasses import dataclass
from io import StringIO
from typing import Any


@dataclass
class ExecutionResult:
    """Result of Python code execution."""

    success: bool
    output: str
    error: str
    value: Any = None
    images: list[bytes] | None = None  # Store captured matplotlib images


class TerminalImageCapture(StringIO):
    """Custom StringIO that captures term-image output."""

    def __init__(self):
        super().__init__()
        self.has_term_image_output = False

    def write(self, s: str) -> int:
        # Check if this is term-image output (usually contains escape sequences)
        if "\033[" in s or "\x1b[" in s:
            self.has_term_image_output = True
        return super().write(s)


class PythonExecutionManager:
    """Manages Python code execution with persistent context."""

    def __init__(self) -> None:
        """Initialize the execution manager with empty context."""
        self.globals: dict[str, Any] = {"__builtins__": __builtins__}
        self.locals: dict[str, Any] = {}
        self._setup_matplotlib_backend()

    def _setup_matplotlib_backend(self) -> None:
        """Set up the terminal matplotlib backend."""
        # Pre-configure matplotlib to use our custom backend
        # This will take effect when matplotlib is imported
        # import os

        # # Set the backend environment variable
        # os.environ["MPLBACKEND"] = "module://vibecore.tools.python.backends.terminal_backend"

        # # Also set it in the execution globals
        # self.globals["__matplotlib_backend__"] = "module://vibecore.tools.python.backends.terminal_backend"

        # Add a helper function to set matplotlib backend programmatically
        backend_setup_code = """
def _setup_matplotlib_terminal():
    '''Helper to ensure matplotlib uses terminal backend.'''
    try:
        import matplotlib
        matplotlib.use('module://vibecore.tools.python.backends.terminal_backend')
    except ImportError:
        pass
_setup_matplotlib_terminal()
"""
        exec(backend_setup_code, self.globals, self.globals)

    async def execute(self, code: str) -> ExecutionResult:
        """Execute Python code and return the result.

        Args:
            code: Python code to execute.

        Returns:
            ExecutionResult with success status, output, errors, and return value.
        """
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = TerminalImageCapture()
        stderr_capture = StringIO()

        # Capture warnings
        old_showwarning = warnings.showwarning

        def custom_showwarning(message, category, filename, lineno, file=None, line=None):
            stderr_capture.write(warnings.formatwarning(message, category, filename, lineno, line))

        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            warnings.showwarning = custom_showwarning

            # Parse the code to handle async functions
            tree = ast.parse(code, mode="exec")

            # Check if we need to run in async context
            has_await = self._has_await_at_module_level(tree)

            if has_await:
                # Create an event loop if needed and run async code
                result_value = await self._execute_async(code)
            else:
                # Normal execution
                result_value = None

                # Check if last statement is an expression we should evaluate
                last_is_expr = tree.body and isinstance(tree.body[-1], ast.Expr)

                if last_is_expr:
                    # Execute all but the last statement
                    if len(tree.body) > 1:
                        exec(
                            compile(ast.Module(body=tree.body[:-1], type_ignores=[]), "<string>", "exec"),
                            self.globals,
                            self.globals,
                        )
                    # Evaluate the last expression
                    last_expr = tree.body[-1]
                    assert isinstance(last_expr, ast.Expr)  # We already checked this
                    result_value = eval(
                        compile(ast.Expression(body=last_expr.value), "<string>", "eval"),
                        self.globals,
                        self.globals,
                    )
                else:
                    # Execute everything normally
                    exec(code, self.globals, self.globals)

            # Check for captured matplotlib images
            images = None
            try:
                # Import the backend module to access captured images
                from vibecore.tools.python.backends import terminal_backend

                captured_images = terminal_backend.get_captured_images()
                if captured_images:
                    images = captured_images
                    terminal_backend.clear_captured_images()
            except Exception:
                # If we can't get images, just continue without them
                pass

            return ExecutionResult(
                success=True,
                output=stdout_capture.getvalue(),
                error=stderr_capture.getvalue(),
                value=result_value,
                images=images,
            )

        except SyntaxError as e:
            return ExecutionResult(
                success=False,
                output="",
                error=f"SyntaxError: {e}",
                value=None,
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=f"{type(e).__name__}: {e}",
                value=None,
            )
        finally:
            # Restore stdout, stderr, and warnings
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            warnings.showwarning = old_showwarning

    def _has_await_at_module_level(self, tree: ast.Module) -> bool:
        """Check if there are await expressions at module level."""
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await):
                return True
            # Check for await in direct assignments
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Await):
                return True
        return False

    async def _execute_async(self, code: str) -> Any:
        """Execute code containing await expressions."""
        # Wrap the entire code in an async function
        lines = code.splitlines()
        indented_code = "\n".join(f"    {line}" if line.strip() else "" for line in lines)
        wrapped_code = f"async def __async_exec():\n{indented_code}\n    return None"

        # Define the async function
        exec(wrapped_code, self.globals, self.globals)

        # Run it
        result = await self.globals["__async_exec"]()

        # Clean up
        del self.globals["__async_exec"]

        return result

    def reset_context(self) -> None:
        """Reset the execution context."""
        matplotlib_backend = self.globals.get("__matplotlib_backend__")
        self.globals = {"__builtins__": __builtins__}
        if matplotlib_backend is not None:
            self.globals["__matplotlib_backend__"] = matplotlib_backend
        self.locals = {}
