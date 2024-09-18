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
    user_id: Optional[int] = None  # 新增用户id字段，设置默认值为None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_units: int = 0
    review_comment: str
    rating: Optional[float] = Field(None, ge=0, le=5, description="Task rating from 0 to 5")

class TaskCreateResponse(BaseModel):
    task: Task
    message: str

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class LoginResponse(BaseModel):
    userId: int
    username: str
    access_token: str
    token_type: str

class TaskFeedbackInfo(BaseModel):
    review_comment: str
    rating: float

class TaskFeedbackInfoGet(BaseModel):
    review_comment: str
    status: TaskStatus

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

class EnterpriseRegistration(BaseModel):
    name: str  # 企业名称
    email: str  # 企业邮箱
    phone: str  # 企业联系电话
    address: str  # 企业地址
    industry: str  # 所属行业
    registration_number: str  # 企业注册号
    legal_representative: str  # 法定代表人
    business_scope: str  # 经营范围
    establishment_date: datetime  # 成立日期
    registered_capital: float  # 注册资本（单位：元）
    company_size: str  # 公司规模（如：小型、中型、大型）
    website: Optional[str] = None  # 企业官网（可选）
    logo_url: Optional[str] = None  # 企业logo URL（可选）
    description: Optional[str] = None  # 企业简介（可选）

class EnterpriseResponse(BaseModel):
    id: int  # 企业ID，由系统自动生成
    name: str  # 企业名称
    email: str  # 企业邮箱
    password: str # 企业密码
    phone: str  # 企业联系电话
    address: str  # 企业地址
    industry: str  # 所属行业
    registration_number: str  # 企业注册号
    legal_representative: str  # 法定代表人
    business_scope: str  # 经营范围
    establishment_date: datetime  # 成立日期
    registered_capital: float  # 注册资本（单位：元）
    company_size: str  # 公司规模（如：小型、中型、大型）
    website: Optional[str] = None  # 企业官网（可选）
    logo_url: Optional[str] = None  # 企业logo URL（可选）
    description: Optional[str] = None  # 企业简介（可选）
    created_at: datetime  # 记录创建时间
    updated_at: datetime  # 记录最后更新时间

class LoginEnterpriseResponse(BaseModel):
    access_token: str
    token_type: str



