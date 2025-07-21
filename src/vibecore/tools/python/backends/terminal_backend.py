"""Terminal backend for matplotlib that captures images for later display."""

from io import BytesIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.backend_bases import FigureManagerBase  # type: ignore[import-not-found]
    from matplotlib.backends.backend_agg import FigureCanvasAgg  # type: ignore[import-not-found]
else:
    try:
        from matplotlib.backend_bases import FigureManagerBase
        from matplotlib.backends.backend_agg import FigureCanvasAgg
    except ImportError:
        # Create dummy classes if matplotlib is not installed
        FigureManagerBase = object  # type: ignore[misc,assignment]
        FigureCanvasAgg = object  # type: ignore[misc,assignment]

__all__ = ["FigureCanvas", "FigureManager", "clear_captured_images", "get_captured_images"]

# Global list to store captured images
_captured_images: list[bytes] = []


class TerminalImageFigureManager(FigureManagerBase):
    """Figure manager that captures plots for later display."""

    def show(self):
        global _captured_images

        # Save figure to BytesIO buffer
        buf = BytesIO()
        self.canvas.figure.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)

        # Store the image buffer in the global list
        _captured_images.append(buf.getvalue())


class TerminalImageFigureCanvas(FigureCanvasAgg):
    """Figure canvas for terminal image backend."""

    manager_class = TerminalImageFigureManager  # type: ignore[assignment]


# Provide the standard names that matplotlib is expecting
FigureCanvas = TerminalImageFigureCanvas
FigureManager = TerminalImageFigureManager


def get_captured_images() -> list[bytes]:
    """Get the list of captured images."""
    return _captured_images.copy()


def clear_captured_images() -> None:
    """Clear the list of captured images."""
    global _captured_images
    _captured_images.clear()
