from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from datetime import datetime
from typing import Optional, Union
from typing import Optional, List


class TABLE_NAMES:
    REFUGEE = "Refugee"
    ENTERPRISE = "Enterprise"
    TASK = "Task"
    REWARD_HISTORY = "RewardHistory"
    WITHDRAW_REQUEST = "WithdrawRequest"


class PARTITION_KEYS:
    PARKEY = "PartitionKey"
    ROWKEY = "RowKey"


class TaskStatus(str, Enum):
    PENDING = "pending"  # 待处理
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    PAUSED = "paused"  # 已暂停
    CANCELLED = "cancelled"  # 已取消


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"  # 未支付
    PROCESSING = "processing"  # 处理中
    PAID = "paid"  # 已支付
    FAILED = "failed"  # 支付失败


class TaskType(str, Enum):
    DATA_ENTRY = "data_entry"  # 数据录入
    IMAGE_LABELING = "image_labeling"  # 图像标注
    CONTENT_MODERATION = "content_moderation"  # 内容审核
    TRANSLATION = "translation"  # 翻译


class TaskDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TaskBase(BaseModel):
    title: str
    description: str
    type: TaskType
    difficulty: TaskDifficulty  # 难度
    deadline: Optional[datetime]  # 最后期限
    reward_per_unit: float  # 奖励
    total_units: int  # 总的任务数
    resources: List[HttpUrl]  # Added resources field


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: int
    user_id: Optional[int] = 0  # 新增用户id字段，设置默认值为0
    enterprise_id: Optional[int] = 0  # 新增企业用户id字段，设置默认值为0
    status: TaskStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    completed_units: int = 0  # 已完成的任务数
    review_comment: str  # 任务反馈
    task_comments: List[str] = []  # 任务commits
    rating: Optional[float] = Field(
        None, ge=0, le=5, description="Task rating from 0 to 5"
    )  # 评分


class TaskListResponse(BaseModel):
    total_count: float
    tasks: List[Task]


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
    balance: Optional[float] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RegisterRefugeeTask(BaseModel):
    username: str
    password: str
    phone: str
    email: str
    balance: Optional[float] = 0
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
    status: TaskStatus


class TaskFeedbackResponse(BaseModel):
    task_id: int
    feedback: TaskFeedbackInfo
    message: str


class WithdrawStatus(str, Enum):
    PENDING = "pending"  # 待处理
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    PAUSED = "paused"  # 已暂停
    CANCELLED = "cancelled"  # 已取消


class WithdrawRequest(BaseModel):
    user_id: int
    amount: float
    payment_method: str
    request_date: datetime
    status: WithdrawStatus
    created_at: datetime  # 记录创建时间
    updated_at: datetime  # 记录最后更新时间


class WithdrawStatusResponse(BaseModel):
    withdraw_history: List[WithdrawRequest]
    total_count: float


class RewardRequest(BaseModel):
    user_id: int
    task_id: int
    amount: float
    created_at: datetime
    updated_at: datetime


class RewardRequestListResponse(BaseModel):
    reward_requests: List[RewardRequest]
    total_count: int


class RewardHistoryResponse(BaseModel):
    reward_history: List[RewardRequest]
    total_reward: float
    total_count: float


class EnterpriseRegistration(BaseModel):
    name: str  # 企业名称
    email: str  # 企业邮箱
    phone: str  # 企业联系电话
    password: str  # 企业密码
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
