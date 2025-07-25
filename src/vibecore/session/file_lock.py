"""File locking utilities for thread-safe session operations."""

import asyncio
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path


class FileLockManager:
    """Manages thread-based file locks for session files.

    This is a basic implementation using threading locks.
    In Phase 2, this will be enhanced with OS-level file locking
    using fcntl (Unix) and msvcrt (Windows).
    """

    def __init__(self):
        """Initialize the file lock manager."""
        # Dictionary mapping file paths to their locks
        self._locks: dict[str, threading.Lock] = {}
        # Lock to protect the _locks dictionary itself
        self._locks_lock = threading.Lock()

    def _get_lock(self, file_path: Path) -> threading.Lock:
        """Get or create a lock for the specified file path.

        Args:
            file_path: Path to the file to lock

        Returns:
            Threading lock for the file
        """
        path_str = str(file_path.resolve())

        with self._locks_lock:
            if path_str not in self._locks:
                self._locks[path_str] = threading.Lock()
            return self._locks[path_str]

    @asynccontextmanager
    async def acquire_lock(
        self,
        file_path: Path,
        timeout: float = 30.0,
        exclusive: bool = True,
    ) -> AsyncIterator[None]:
        """Acquire a lock for the specified file.

        Args:
            file_path: Path to the file to lock
            timeout: Maximum time to wait for the lock (in seconds)
            exclusive: Whether to acquire an exclusive lock (unused in thread-based impl)

        Yields:
            None when the lock is acquired

        Raises:
            TimeoutError: If the lock cannot be acquired within the timeout
        """
        lock = self._get_lock(file_path)

        # Try to acquire the lock with timeout
        acquired = await asyncio.to_thread(lock.acquire, timeout=timeout)

        if not acquired:
            raise TimeoutError(f"Could not acquire lock for {file_path} within {timeout} seconds")

        try:
            yield
        finally:
            # Always release the lock
            lock.release()

    def cleanup_lock(self, file_path: Path) -> None:
        """Remove the lock for a file that no longer exists.

        This should be called after deleting a file to avoid memory leaks.

        Args:
            file_path: Path to the file whose lock should be removed
        """
        path_str = str(file_path.resolve())

        with self._locks_lock:
            if path_str in self._locks:
                del self._locks[path_str]


# Global lock manager instance
_lock_manager = FileLockManager()


@asynccontextmanager
async def acquire_file_lock(
    file_path: Path,
    timeout: float = 30.0,
    exclusive: bool = True,
) -> AsyncIterator[None]:
    """Acquire a lock for the specified file.

    This is a convenience function that uses the global lock manager.

    Args:
        file_path: Path to the file to lock
        timeout: Maximum time to wait for the lock (in seconds)
        exclusive: Whether to acquire an exclusive lock

    Yields:
        None when the lock is acquired

    Raises:
        TimeoutError: If the lock cannot be acquired within the timeout
    """
    async with _lock_manager.acquire_lock(file_path, timeout, exclusive):
        yield


def cleanup_file_lock(file_path: Path) -> None:
    """Remove the lock for a file that no longer exists.

    This is a convenience function that uses the global lock manager.

    Args:
        file_path: Path to the file whose lock should be removed
    """
    _lock_manager.cleanup_lock(file_path)
