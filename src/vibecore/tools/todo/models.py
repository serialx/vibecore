"""Todo data models."""

import uuid
from enum import Enum

from pydantic import BaseModel, Field


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TodoPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TodoItem(BaseModel):
    """Pydantic model for todo items."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    status: TodoStatus
    priority: TodoPriority
