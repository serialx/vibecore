"""Helper functions for Python execution tool."""

import tempfile
from io import BytesIO

from agents import RunContextWrapper

from vibecore.context import PythonToolContext

try:
    from PIL import Image  # type: ignore[import-not-found]
    from term_image.image import AutoImage  # type: ignore[import-not-found]

    TERM_IMAGE_AVAILABLE = True
except ImportError:
    TERM_IMAGE_AVAILABLE = False


async def execute_python_helper(ctx: RunContextWrapper[PythonToolContext], code: str) -> str:
    """Helper function to execute Python code.

    This is the actual implementation extracted from the tool decorator.
    """
    result = await ctx.context.python_manager.execute(code)

    # Format the response
    response_parts = []

    if result.output:
        response_parts.append(f"Output:\n```\n{result.output}```")

    if result.error:
        response_parts.append(f"Error:\n```\n{result.error}```")

    if result.value is not None and not result.output:
        # Only show the value if there was no print output
        response_parts.append(f"Result: `{result.value}`")

    # Display any captured matplotlib images
    if result.images:
        for i, image_data in enumerate(result.images):
            try:
                # Save image to temporary file
                with tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False) as tmp_file:
                    tmp_file.write(image_data)
                    temp_path = tmp_file.name

                # Add Markdown image reference to response
                response_parts.append(f"\n![Plot {i + 1}](file://{temp_path})")

                # Display in terminal if term-image is available
                if TERM_IMAGE_AVAILABLE:
                    # Load image from bytes for terminal display
                    buf = BytesIO(image_data)
                    pil_image = Image.open(buf)  # type: ignore

                    # Use AutoImage for automatic terminal detection
                    term_image = AutoImage(pil_image, width=80)  # type: ignore

                    # Display the image
                    term_image.draw(h_align="center", v_align="top", pad_width=1, pad_height=1)  # type: ignore

                    # Close the image
                    pil_image.close()
                    buf.close()

                    # Note that an image was displayed
                    if i == 0:
                        response_parts.append("[Image displayed in terminal]")
                else:
                    # Note that term-image is not available
                    if i == 0:
                        response_parts.append("[Matplotlib plots saved to temporary files]")
            except Exception as e:
                response_parts.append(f"\n[Error processing image {i + 1}: {e}]")

    if not response_parts:
        return "Code executed successfully (no output)."

    return "\n\n".join(response_parts)
