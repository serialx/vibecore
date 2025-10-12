"""JSONL-based session storage implementation for openai-agents SDK."""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from agents import Session

if TYPE_CHECKING:
    from openai.types.responses import ResponseInputItemParam as TResponseInputItem

from .file_lock import acquire_file_lock, cleanup_file_lock
from .path_utils import get_session_file_path

logger = logging.getLogger(__name__)


class JSONLSession(Session):
    """JSONL-based implementation of the agents.Session protocol.

    Stores conversation history in JSON Lines format, with one JSON object
    per line. This provides human-readable storage and efficient append operations.

    The session files are stored at:
    {base_dir}/projects/{canonicalized_project_path}/{session_id}.jsonl
    """

    def __init__(
        self,
        session_id: str,
        project_path: str | Path | None = None,
        base_dir: str | Path | None = None,
    ):
        """Initialize the JSONL session.

        Args:
            session_id: Unique identifier for the session
            project_path: Project path to canonicalize (defaults to cwd)
            base_dir: Base directory for sessions (defaults to ~/.vibecore)
        """
        self.session_id = session_id

        # Set default project path to current working directory
        if project_path is None:
            self.project_path = Path.cwd()
        else:
            self.project_path = Path(project_path)

        # Set default base directory
        if base_dir is None:
            self.base_dir = Path.home() / ".vibecore"
        else:
            self.base_dir = Path(base_dir)

        # Get the full path to the session file
        self.file_path = get_session_file_path(
            self.session_id,
            self.project_path,
            self.base_dir,
        )

        # Ensure the parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Initialized JSONLSession for {self.session_id} at {self.file_path}")

    async def get_items(self, limit: int | None = None) -> list["TResponseInputItem"]:
        """Retrieve the conversation history for this session.

        Args:
            limit: Maximum number of items to retrieve. If None, retrieves all items.
                   When specified, returns the latest N items in chronological order.

        Returns:
            List of input items representing the conversation history
        """
        # If file doesn't exist, return empty list
        if not self.file_path.exists():
            return []

        items: list[TResponseInputItem] = []

        async with acquire_file_lock(self.file_path, exclusive=False):
            try:
                if limit is None:
                    # Read entire file sequentially
                    with open(self.file_path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                item = json.loads(line)
                                items.append(item)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Skipping invalid JSON line in {self.file_path}: {e}")
                else:
                    # Read file backwards to get last N items efficiently
                    # For now, read all and slice (optimize in Phase 2)
                    all_items = []
                    with open(self.file_path, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                item = json.loads(line)
                                all_items.append(item)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Skipping invalid JSON line in {self.file_path}: {e}")

                    # Return the last N items
                    items = all_items[-limit:] if len(all_items) > limit else all_items

            except FileNotFoundError:
                # File was deleted between existence check and read
                return []
            except Exception as e:
                logger.error(f"Error reading session file {self.file_path}: {e}")
                raise

        return items

    async def add_items(self, items: list["TResponseInputItem"]) -> None:
        """Add new items to the conversation history.

        Args:
            items: List of input items to add to the history
        """
        if not items:
            return

        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        async with acquire_file_lock(self.file_path, exclusive=True):
            try:
                # Open file in append mode
                with open(self.file_path, "a", encoding="utf-8") as f:
                    for item in items:
                        # Write each item as a JSON line
                        json_line = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
                        f.write(json_line + "\n")

                    # Ensure data is written to disk
                    f.flush()

                logger.debug(f"Added {len(items)} items to session {self.session_id}")

            except Exception as e:
                logger.error(f"Error adding items to session file {self.file_path}: {e}")
                raise

    async def pop_item(self) -> "TResponseInputItem | None":
        """Remove and return the most recent item from the session.

        Returns:
            The most recent item if it exists, None if the session is empty
        """
        if not self.file_path.exists():
            return None

        async with acquire_file_lock(self.file_path, exclusive=True):
            try:
                # Read all lines
                with open(self.file_path, encoding="utf-8") as f:
                    lines = f.readlines()

                if not lines:
                    return None

                # Find the last non-empty line
                last_item = None
                last_item_index = -1

                for i in range(len(lines) - 1, -1, -1):
                    line = lines[i].strip()
                    if line:
                        try:
                            last_item = json.loads(line)
                            last_item_index = i
                            break
                        except json.JSONDecodeError as e:
                            logger.warning(f"Skipping invalid JSON line in {self.file_path}: {e}")

                if last_item is None:
                    return None

                # Remove the last item and write back the rest
                remaining_lines = lines[:last_item_index]

                # Write atomically by writing to a temp file and renaming
                temp_file = self.file_path.with_suffix(".tmp")
                try:
                    with open(temp_file, "w", encoding="utf-8") as f:
                        f.writelines(remaining_lines)

                    # Atomically replace the original file
                    temp_file.replace(self.file_path)

                except Exception:
                    # Clean up temp file if something went wrong
                    if temp_file.exists():
                        temp_file.unlink()
                    raise

                logger.debug(f"Popped item from session {self.session_id}")
                return last_item

            except FileNotFoundError:
                # File was deleted between existence check and read
                return None
            except Exception as e:
                logger.error(f"Error popping item from session file {self.file_path}: {e}")
                raise

    async def clear_session(self) -> None:
        """Clear all items for this session."""
        if not self.file_path.exists():
            return

        async with acquire_file_lock(self.file_path, exclusive=True):
            try:
                # Delete the file
                self.file_path.unlink()

                # Clean up the lock for this file
                cleanup_file_lock(self.file_path)

                logger.debug(f"Cleared session {self.session_id}")

            except FileNotFoundError:
                # File was already deleted
                pass
            except Exception as e:
                logger.error(f"Error clearing session file {self.file_path}: {e}")
                raise
