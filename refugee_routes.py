from fastapi import APIRouter, File, Query, UploadFile, HTTPException, Depends
from pydantic import HttpUrl
from auth_token import create_access_token, verify_oauth_token
from enterprise_routes import update_task_in_database
from mock_data import get_mock_refugee_tasks, get_mock_tasks
from database import get_latest_id_by_partition, check_field_exists, insert_entity, get_entity_by_field, update_entity_fields, get_all_entities
from schemas import CommonResponseBool, LoginResponse, RefugeeTask, RegisterRefugeeTask, RewardHistory, RewardHistoryResponse, TaskDifficulty, TaskFeedbackInfoGet, TaskListResponse, TaskStatus, TaskType, Task, WithdrawRequest, WithdrawStatusResponse, PARTITION_KEYS, TABLE_NAMES
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi.security import OAuth2PasswordBearer
import hashlib

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 账户管理

router = APIRouter()

@router.post("/api/refugee/register", response_model=RefugeeTask)
async def register_refugee(refugee: RegisterRefugeeTask):
    try:
        # 获取mock数据
        # mock_refugee_tasks = get_mock_refugee_tasks()
        
        
        # 验证用户名是否已存在
        usernameIsCheck = check_field_exists(TABLE_NAMES.REFUGEE, "username", refugee.username)
        if usernameIsCheck:
            raise HTTPException(status_code=400, detail="Username already exists")

        # 验证手机号是否已存在
        phoneIsCheck = check_field_exists(TABLE_NAMES.REFUGEE, "phone", refugee.phone)
        if phoneIsCheck:
            raise HTTPException(status_code=400, detail="Phone number already exists")

        # 验证邮箱是否已存在
        emailIsCheck = check_field_exists(TABLE_NAMES.REFUGEE, "email", refugee.username)
        if emailIsCheck:
            raise HTTPException(status_code=400, detail="Email already exists")

        # 密码加密
        hashed_password = hashlib.md5(refugee.password.encode()).hexdigest()

        # 创建新用户

        # 生成新的用户ID
        new_id = get_latest_id_by_partition(TABLE_NAMES.REFUGEE, PARTITION_KEYS.PARKEY)
        new_refugee = RefugeeTask(
            user_id=new_id,  # 生成唯一的用户ID
            username=refugee.username,
            phone=refugee.phone,
            email=refugee.email,
            password=hashed_password,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 将用户信息保存到数据库
        save_refugee_to_database(new_refugee)

        return new_refugee
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during registration: {str(e)}")

@router.post("/api/refugee/login", response_model=LoginResponse)
async def login_refugee(username: str, password: str, language: Optional[str] = "en"):
    try:
        # 查找匹配的用户
        user = get_entity_by_field(TABLE_NAMES.REFUGEE, "username", username)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # 验证密码
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        if user['password'] != hashed_password:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # 生成访问令牌
        access_token = create_access_token(data={"sub": str(user['PartitionKey'])})
        
        # 创建登录响应
        login_data = LoginResponse(
            userId=user['PartitionKey'],
            username=user['username'],
            access_token=access_token,
            token_type="bearer"
        )

        return login_data
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during login: {str(e)}")

@router.post("/api/refugee/forgot-password", response_model=CommonResponseBool)
async def forgot_password(contact: str = Query(..., min_length=1), password: str = Query(..., min_length=6), contact_type: str = Query(..., min_length=1)):
    try:
        # 验证联系方式是否存在
        if contact_type not in ["phone", "email"]:
            raise HTTPException(status_code=400, detail="Invalid contact type")

        # 根据联系方式查找用户
        user = None
        if contact_type == "phone":
            user = get_entity_by_field(TABLE_NAMES.REFUGEE, "phone", contact)
        elif contact_type == "email":
            user = get_entity_by_field(TABLE_NAMES.REFUGEE, "email", contact)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 更新用户密码
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        user['password'] = hashed_password
        user['updated_at'] = datetime.now()

        # 在实际应用中，这里应该有保存到数据库的逻辑
        # 但在这个mock环境中，我们只是更新了内存中的对象
        isUpdate = update_entity_fields(TABLE_NAMES.REFUGEE, user[PARTITION_KEYS.PARKEY], user[PARTITION_KEYS.ROWKEY], user)
        return CommonResponseBool(
            result=True
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/refugee/update-profile", response_model=CommonResponseBool)
async def update_refugee_profile(refugee: RegisterRefugeeTask, userId: str = Depends(verify_oauth_token)):
    try:
        # 获取当前用户信息
        user = get_entity_by_field(TABLE_NAMES.REFUGEE, PARTITION_KEYS.PARKEY, userId)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 准备更新字段
        fields_to_update = {}
        if refugee.username:
            if refugee.username != user['username'] and get_entity_by_field(TABLE_NAMES.REFUGEE, "username", refugee.username):
                raise HTTPException(status_code=400, detail="Username already exists")
            fields_to_update['username'] = refugee.username
        if refugee.phone:
            if refugee.phone != user['phone'] and get_entity_by_field(TABLE_NAMES.REFUGEE, "phone", refugee.phone):
                raise HTTPException(status_code=400, detail="Phone number already exists")
            fields_to_update['phone'] = refugee.phone
        if refugee.email:
            if refugee.email != user['email'] and get_entity_by_field(TABLE_NAMES.REFUGEE, "email", refugee.email):
                raise HTTPException(status_code=400, detail="Email already exists")
            fields_to_update['email'] = refugee.email

        fields_to_update['updated_at'] = datetime.now().isoformat()

        # 更新用户信息
        update_success = update_entity_fields(
            TABLE_NAMES.REFUGEE,
            user[PARTITION_KEYS.PARKEY], 
            user[PARTITION_KEYS.ROWKEY],
            fields_to_update
        )

        if not update_success:
            raise HTTPException(status_code=500, detail="Failed to update user profile")

        return CommonResponseBool(
            result = True
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while updating profile: {str(e)}")
    
# 辅助函数
def save_refugee_to_database(refugee: RefugeeTask) -> RefugeeTask:
    # 将难民数据插入到Refugee表中
    entity = {
        "PartitionKey": str(refugee.user_id),
        "RowKey": str(refugee.user_id),
        "user_id": refugee.user_id,
        "username": refugee.username,
        "phone": refugee.phone,
        "email": refugee.email,
        "password": refugee.password,
        "status": refugee.status.value,
        "created_at": refugee.created_at.isoformat(),
        "updated_at": refugee.updated_at.isoformat()
    }
    insert_entity(TABLE_NAMES.REFUGEE, entity)
    return refugee


# 任务浏览与申请

#获取可用任务列表，按类型、难度、报酬等进行筛选。
@router.get("/api/task/browse", response_model=TaskListResponse)
async def browse_tasks(
    userId: str = Depends(verify_oauth_token),
    task_type: Optional[TaskType] = Query(None, description="Filter tasks by type"),
    difficulty: Optional[TaskDifficulty] = Query(None, description="Filter tasks by difficulty"),
    min_reward: Optional[float] = Query(None, ge=0, description="Minimum reward per unit"),
    max_reward: Optional[float] = Query(None, ge=0, description="Maximum reward per unit"),
    status: Optional[TaskStatus] = Query(None, description="Filter tasks by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
):
    try:
        # 这里应该是实际的数据库查询逻辑
        search_params = {}
        # 筛选user_id为空或者0的任务
        search_params["user_id"] = 0
        # 根据查询参数筛选任务
        if task_type:
            search_params["type"] = task_type.value
        if difficulty:
            search_params["difficulty"] = difficulty.value
        if min_reward is not None:
            search_params["reward_per_unit__ge"] = min_reward
        if max_reward is not None:
            search_params["reward_per_unit__le"] = max_reward
        if status:
            search_params["status"] = status.value

        all_tasks, total_count = get_all_entities(TABLE_NAMES.TASK, page, page_size, **search_params)

        # Convert the raw entities to Task objects
        tasks = []
        for task in all_tasks:
            # 确保 resources 字段是一个列表
            if isinstance(task.get('resources'), str):
                task['resources'] = [task['resources']]
            elif task.get('resources') is None:
                task['resources'] = []
            tasks.append(Task(**task))

        return TaskListResponse(
            total_count=total_count,
            tasks=tasks
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 申请参与任务，将任务加入“我的任务”列表。
@router.post("/api/task/{task_id}/apply", response_model=CommonResponseBool)
async def apply_for_task(task_id: int, userId: str = Depends(verify_oauth_token)):
    try:
        # 1. 检查任务是否存在
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, PARTITION_KEYS.PARKEY, str(task_id))
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # 2. 检查任务是否可以申请（例如，状态是否为 PENDING）
        if TaskStatus(task_entity['status']) != TaskStatus.PENDING:
            raise HTTPException(status_code=400, detail="This task is not available for application")
        
        # 3. 检查任务是否已经被其他用户申请
        if task_entity.get('user_id'):
            raise HTTPException(status_code=400, detail="This task has already been assigned to another user")
        
        # 4. 检查用户是否已经申请过这个任务
        if task_entity.get('user_id') == userId:
            raise HTTPException(status_code=400, detail="You have already applied for this task")
        
        # 更新任务状态为进行中
        fields_to_update = {
            'user_id': userId,
            'status': TaskStatus.IN_PROGRESS.value,
            'updated_at': datetime.now().isoformat()
        }
        
        update_success = update_entity_fields(
            TABLE_NAMES.TASK,
            task_entity['PartitionKey'],
            task_entity['RowKey'],
            fields_to_update
        )
        
        if not update_success:
            raise HTTPException(status_code=500, detail="Failed to update task")
        
        return CommonResponseBool(result=True)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 任务执行
#获取用户已申请的任务列表及状态。
@router.get("/api/task/my-tasks", response_model=TaskListResponse)
async def get_my_tasks(
    userId: str = Depends(verify_oauth_token), 
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    try:
        search_params = {
            "user_id": userId
        }
        # 获取所有任务
        all_tasks, total_count = get_all_entities(TABLE_NAMES.TASK, page, page_size, **search_params)

        # 将任务列表转换为Task对象列表
        tasks = []
        for task in all_tasks:
            # 确保 resources 字段是一个列表
            if isinstance(task.get('resources'), str):
                task['resources'] = [task['resources']]
            elif task.get('resources') is None:
                task['resources'] = []
            tasks.append(Task(**task))

        # 按更新时间降序排序
        tasks.sort(key=lambda x: x.updated_at, reverse=True)

        # 构建响应
        return TaskListResponse(
            total_count=total_count,
            tasks=tasks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching tasks: {str(e)}")

# 提交已完成的任务。
@router.post("/api/task/{task_id}/submit", response_model=CommonResponseBool)
async def submit_task(task_id: int, userId: str = Depends(verify_oauth_token)):
    try:
        # 1. 检查任务是否存在
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, PARTITION_KEYS.PARKEY, task_id)
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # 2. 检查任务是否属于当前用户
        if str(task_entity.get('user_id')) != userId:
            raise HTTPException(status_code=403, detail="You don't have permission to submit this task")
        
        # 3. 检查任务状态是否为进行中
        if task_entity.get('status') != TaskStatus.IN_PROGRESS.value:
            raise HTTPException(status_code=400, detail="Task is not in progress")
        
        # 4. 更新任务状态为已完成
        fields_to_update = {
            'status': TaskStatus.COMPLETED.value,
            'updated_at': datetime.now().isoformat(),
            'completed_units': task_entity.get('total_units')
        }
        
        update_success = update_entity_fields(
            TABLE_NAMES.TASK,
            task_entity['PartitionKey'],
            task_entity['RowKey'],
            fields_to_update
        )
        
        if not update_success:
            raise HTTPException(status_code=500, detail="Failed to update task status")
        
        # 5. 计算并更新用户的奖励
        # reward_amount = task_entity.get('reward_per_unit', 0) * task_entity.get('total_units', 0)
        
        # 6. 创建奖励历史记录
        # reward_history = {
        #     'PartitionKey': userId,
        #     'RowKey': f"{int(time.time())}",
        #     'task_id': task_id,
        #     'task_title': task_entity.get('title'),
        #     'completion_date': datetime.now().isoformat(),
        #     'reward_amount': reward_amount
        # }
        
        # insert_success = insert_entity(TABLE_NAMES.REWARD_HISTORY, reward_history)
        # if not insert_success:
        #     raise HTTPException(status_code=500, detail="Failed to create reward history")
        
        return CommonResponseBool(result=True)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#查看任务是否通过审核和反馈信息。
@router.get("/api/task/{task_id}/feedback", response_model=TaskFeedbackInfoGet)
async def get_task_feedback(task_id: int, userId: str = Depends(verify_oauth_token)):
    try:
        # 1. 检查任务是否存在
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, PARTITION_KEYS.PARKEY, str(task_id))
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # 2. 检查任务是否属于当前用户
        if str(task_entity.get('user_id')) != userId:
            raise HTTPException(status_code=403, detail="You don't have permission to view this task's feedback")
        
        # 3. 获取任务反馈信息
        feedback = TaskFeedbackInfoGet(
            review_comment=task_entity.get('review_comment', ''),
            status=TaskStatus(task_entity.get('status'))
        )
        
        # 4. 构建并返回响应
        return feedback
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 报酬结算
@router.get("/api/reward/history", response_model=RewardHistoryResponse)
async def get_reward_history(userId: str = Depends(verify_oauth_token)):
    try:
        # 这里应该从数据库中获取用户的任务收入历史
        # 为了演示，我们使用模拟数据
        reward_history = [
            {
                "task_id": 1,
                "task_title": "数据输入：客户信息",
                "completion_date": datetime.now() - timedelta(days=5),
                "reward_amount": 175.0
            },
            {
                "task_id": 3,
                "task_title": "内容审核：社交媒体帖子",
                "completion_date": datetime.now() - timedelta(days=1),
                "reward_amount": 1000.0
            }
        ]
        
        total_reward = sum(item["reward_amount"] for item in reward_history)
        return_data = RewardHistoryResponse(
            reward_history=[RewardHistory(**item) for item in reward_history],
            total_reward=total_reward
        )
        return return_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/reward/withdraw", response_model=WithdrawRequest)
async def withdraw_reward(
    amount: float,
    payment_method: str,
    user_id: str = Depends(verify_oauth_token)
):
    try:
        # 验证提现金额
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero")

        # 验证支付方式
        valid_payment_methods = ["PayPal", "Mobile Money", "Bank Transfer"]
        if payment_method not in valid_payment_methods:
            raise ValueError(f"Invalid payment method. Supported methods are: {', '.join(valid_payment_methods)}")

        # 这里应该检查用户的可用余额，并在数据库中记录提现请求
        # 为了演示，我们假设操作总是成功的
        # Create a new WithdrawRequest model instance
        withdraw_request = WithdrawRequest(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            request_date=datetime.now(),
            status="Pending"
        )
        
        # Here you would typically save the withdraw_request to the database
        
        return withdraw_request.dict()
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/reward/withdraw-status", response_model=WithdrawStatusResponse)
async def get_withdraw_status(user_id: str = Depends(verify_oauth_token)):
    try:
        # 这里应该从数据库中获取用户的提现记录
        # 为了演示，我们使用模拟数据
        withdraw_history = [
            WithdrawRequest(
                id=1,
                user_id=user_id,
                amount=100.0,
                payment_method="PayPal",
                request_date=datetime.fromisoformat("2023-05-01T10:00:00"),
                status="Completed"
            ),
            WithdrawRequest(
                id=2,
                user_id=user_id,
                amount=50.0,
                payment_method="Mobile Money",
                request_date=datetime.fromisoformat("2023-05-10T14:30:00"),
                status="Pending"
            )
        ]
        result_data = WithdrawStatusResponse(
            withdraw_history=withdraw_history,
            pending_withdrawals=[w for w in withdraw_history if w.status == "Pending"]
        )
        return result_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))