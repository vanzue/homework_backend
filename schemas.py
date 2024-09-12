from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import Optional

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class TaskType(str, Enum):
    DATA_ENTRY = "data_entry"
    IMAGE_LABELING = "image_labeling"
    CONTENT_MODERATION = "content_moderation"
    TRANSLATION = "translation"

class Task(BaseModel):
    id: int
    title: str
    description: str
    type: TaskType
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    deadline: Optional[datetime]
    reward_per_unit: float
    total_units: int
    completed_units: int