"""Unit tests for JSONLSession."""

import json
from pathlib import Path

import pytest
import pytest_asyncio

from vibecore.session import JSONLSession


@pytest_asyncio.fixture
async def session(tmp_path):
    """Create a test session with a temporary directory."""
    session = JSONLSession(
        session_id="test-session",
        project_path="/test/project",
        base_dir=tmp_path,
    )
    return session


@pytest.mark.asyncio
async def test_init(tmp_path):
    """Test JSONLSession initialization."""
    session = JSONLSession(
        session_id="test-session",
        project_path="/test/project",
        base_dir=tmp_path,
    )

    assert session.session_id == "test-session"
    assert session.project_path == Path("/test/project")
    assert session.base_dir == tmp_path
    assert session.file_path.name == "test-session.jsonl"
    # The canonicalized path will be "test-project" not "-test-project"
    assert "test-project" in str(session.file_path)


@pytest.mark.asyncio
async def test_get_items_empty(session):
    """Test get_items on empty/non-existent session."""
    items = await session.get_items()
    assert items == []


@pytest.mark.asyncio
async def test_add_and_get_items(session):
    """Test adding and retrieving items."""
    test_items = [
        {"type": "user", "content": "Hello"},
        {"type": "assistant", "content": "Hi there!"},
    ]

    # Add items
    await session.add_items(test_items)

    # Get all items
    items = await session.get_items()
    assert items == test_items

    # Get limited items
    items = await session.get_items(limit=1)
    assert items == [test_items[1]]  # Should return last item


@pytest.mark.asyncio
async def test_pop_item(session):
    """Test popping items from session."""
    test_items = [
        {"type": "user", "content": "First"},
        {"type": "user", "content": "Second"},
        {"type": "user", "content": "Third"},
    ]

    # Add items
    await session.add_items(test_items)

    # Pop last item
    popped = await session.pop_item()
    assert popped == {"type": "user", "content": "Third"}

    # Check remaining items
    items = await session.get_items()
    assert items == test_items[:2]

    # Pop until empty
    await session.pop_item()
    await session.pop_item()
    popped = await session.pop_item()
    assert popped is None


@pytest.mark.asyncio
async def test_clear_session(session):
    """Test clearing session."""
    test_items = [
        {"type": "user", "content": "Test 1"},
        {"type": "user", "content": "Test 2"},
    ]

    # Add items
    await session.add_items(test_items)

    # Verify items exist
    items = await session.get_items()
    assert len(items) == 2

    # Clear session
    await session.clear_session()

    # Verify session is empty
    items = await session.get_items()
    assert items == []

    # Verify file doesn't exist
    assert not session.file_path.exists()


@pytest.mark.asyncio
async def test_jsonl_format(session):
    """Test that the file is stored in proper JSONL format."""
    test_items = [
        {"type": "user", "content": "Line 1"},
        {"type": "assistant", "content": "Line 2"},
    ]

    await session.add_items(test_items)

    # Read file directly
    with open(session.file_path) as f:
        lines = f.readlines()

    assert len(lines) == 2
    assert json.loads(lines[0].strip()) == test_items[0]
    assert json.loads(lines[1].strip()) == test_items[1]


@pytest.mark.asyncio
async def test_concurrent_operations(session):
    """Test basic concurrent operations."""
    import asyncio

    async def add_items(start_idx):
        items = [{"type": "user", "content": f"Message {start_idx + i}"} for i in range(5)]
        await session.add_items(items)

    # Run concurrent adds
    await asyncio.gather(
        add_items(0),
        add_items(10),
        add_items(20),
    )

    # Check all items were added
    items = await session.get_items()
    assert len(items) == 15

    # All items should be present
    contents = {item["content"] for item in items}
    expected = {f"Message {i}" for i in list(range(5)) + list(range(10, 15)) + list(range(20, 25))}
    assert contents == expected


@pytest.mark.asyncio
async def test_path_canonicalization():
    """Test path canonicalization works correctly."""
    from vibecore.session.path_utils import canonicalize_path

    # Test normal path
    path = Path("/Users/test/project")
    canonical = canonicalize_path(path)
    assert canonical == "Users-test-project"  # Leading slash becomes empty, so no leading hyphen

    # Test path with various separators
    path = Path("/test/with/many/separators")
    canonical = canonicalize_path(path)
    assert canonical == "test-with-many-separators"
    assert "/" not in canonical

    # Test root path
    path = Path("/")
    canonical = canonicalize_path(path)
    # Root path "/" becomes empty after stripping, so default to "root"
    assert canonical == "root"
