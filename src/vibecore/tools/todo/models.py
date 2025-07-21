"""Todo data models."""

import uuid
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TodoPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TodoItem:
    content: str
    status: TodoStatus
    priority: TodoPriority
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class TodoItemModel(BaseModel):
    """Pydantic model for todo items."""

    id: str
    content: str
    status: str
    priority: str
