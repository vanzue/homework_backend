from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, Union

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

class TaskBase(BaseModel):
    title: str
    description: str
    type: TaskType
    deadline: Optional[datetime]
    reward_per_unit: float
    total_units: int

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_units: int = 0

class TaskCreateResponse(BaseModel):
    task: Task
    message: str

class CommonResponse(BaseModel):
    code: int
    data: Optional[Union[dict, bool]]
    message: str