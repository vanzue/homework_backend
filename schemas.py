from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from datetime import datetime
from typing import Optional, Union
from typing import Optional, List

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

class TaskDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class TaskBase(BaseModel):
    title: str
    description: str
    type: TaskType
    difficulty: TaskDifficulty
    deadline: Optional[datetime]
    reward_per_unit: float
    total_units: int
    resources: List[HttpUrl]  # Added resources field

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
    # code: int
    data: Optional[Union[Task, List[Task],dict, bool]]

class CommonResponseBool(BaseModel):
    result: bool
class TaskProgress(BaseModel):
    task_id: int
    completed_units: int
    total_units: int
    progress_percentage: float
    estimated_completion_time: Optional[datetime]

class RefugeeTask(BaseModel):
    user_id: int
    username: str
    phone: str
    email: str
    password: Optional[str] = None
    status: Optional[TaskStatus] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RegisterRefugeeTask(BaseModel):
    username: str
    password: str
    phone: str
    email: str

class LoginResponse(BaseModel):
    userId: int
    username: str
    access_token: str
    token_type: str

class TaskFeedbackInfo(BaseModel):
    status: str
    comments: str
    review_date: Optional[datetime] = None

class TaskFeedback(BaseModel):
    task_id: int
    feedback: TaskFeedbackInfo

class TaskProgress(BaseModel):
    task_id: int
    completed_units: int
    total_units: int
    progress_percentage: float
    estimated_completion_time: Optional[datetime] = None

class TaskFeedbackResponse(BaseModel):
    task_id: int
    feedback: TaskFeedbackInfo
    message: str

class TaskReviewResponse(BaseModel):
    task_id: int
    is_accepted: bool
    status: TaskStatus
    review_comment: Optional[str] = None

class RewardHistory(BaseModel):
    task_id: int
    task_title: str
    completion_date: datetime
    reward_amount: float

class RewardHistoryResponse(BaseModel):
    reward_history: List[RewardHistory]
    total_reward: float

class WithdrawRequest(BaseModel):
    user_id: str
    amount: float
    payment_method: str
    request_date: datetime
    status: str

class WithdrawStatusResponse(BaseModel):
    withdraw_history: List[WithdrawRequest]
    pending_withdrawals: List[WithdrawRequest]


