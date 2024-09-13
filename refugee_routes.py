from fastapi import APIRouter, File, Query, UploadFile, HTTPException, Depends
from auth_token import create_access_token, get_current_user
from mock_data import get_mock_tasks
from schemas import RegisterRefugeeTask, CommonResponse, TaskDifficulty, TaskStatus, TaskType
from datetime import datetime, timedelta
from typing import Optional
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 账户管理
@router.post("/api/refugee/register", response_model=CommonResponse)
async def register_refugee(refugee: RegisterRefugeeTask):
    try:
        # 这里应该有验证用户名是否已存在的逻辑
        # 这里应该有验证手机号是否已存在的逻辑
        # 这里应该有发送手机验证码的逻辑
        # 这里应该有验证邮箱是否已存在的逻辑
        # 这里应该有密码加密的逻辑
        # 这里应该有将用户信息保存到数据库的逻辑

        # 模拟创建用户
        new_refugee = {
            "userId": 1,
            "username": refugee.username,
            "phone": refugee.phone,
            "email": refugee.email,
            "register_time": datetime.now(),
        }

        return CommonResponse(
            code=1,
            data=new_refugee,
            message="Refugee registered successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/refugee/login", response_model=CommonResponse)
async def login_refugee(username: str, password: str, language: Optional[str] = "en"):
    try:
        # 这里应该有验证用户名和密码的逻辑
        userId = 1 #假设获取到用户id
        # 生成访问令牌
        access_token = create_access_token(data={"sub": userId})
        # 模拟登录成功
        login_data = {
            "userId": userId,
            "username": username,
            "access_token": access_token,
            "token_type": "bearer"
        }

        # 多语言支持
        messages = {
            "en": "Refugee logged in successfully",
            "zh": "难民登录成功",
            "fr": "Réfugié connecté avec succès",
            # 可以添加更多语言
        }

        return CommonResponse(
            code=1,
            data=login_data,
            message=messages.get(language, messages["en"])
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@router.post("/api/refugee/forgot-password", response_model=CommonResponse)
async def forgot_password(contact: str = Query(..., min_length=1), password: str = Query(..., min_length=1), contact_type: str = Query(..., min_length=1)):
    try:
        # 验证联系方式是否存在
        if contact_type not in ["phone", "email"]:
            raise HTTPException(status_code=400, detail="Invalid contact type")

        # 模拟检查用户是否存在
        user_exists = True  # 这里应该是实际的数据库查询逻辑

        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")

        #这里进行更新数据库用户密码

        return CommonResponse(
            code=1,
            data=True,
            message="Password reset link sent successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/refugee/update-profile", response_model=CommonResponse)
async def update_refugee_profile(
    userId: str = Depends(get_current_user),
    username: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
):
    try:
        # 这里应该是实际的数据库更新逻辑
        # 模拟更新用户信息
        updated_user = {
            "userId": userId,
            "username": username,
            "phone": phone,
            "email": email
        }

        return CommonResponse(
            code=1,
            data=updated_user,
            message="Refugee profile updated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 任务浏览与申请
@router.get("/api/task/browse", response_model=CommonResponse)
async def browse_tasks(
    userId: str = Depends(get_current_user),
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
        # 为了演示，我们使用模拟数据
        tasks = get_mock_tasks()

        # 根据查询参数筛选任务
        if task_type:
            tasks = [task for task in tasks if task.type == task_type]
        if difficulty:
            tasks = [task for task in tasks if task.difficulty == difficulty]
        if min_reward is not None:
            tasks = [task for task in tasks if task.reward_per_unit >= min_reward]
        if max_reward is not None:
            tasks = [task for task in tasks if task.reward_per_unit <= max_reward]
        if status:
            tasks = [task for task in tasks if task.status == status]

        # 简单的分页逻辑
        start = (page - 1) * page_size
        end = start + page_size
        paginated_tasks = tasks[start:end]

        return CommonResponse(
            code=1,
            data=paginated_tasks,
            message='Task list retrieved successfully'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/task/{task_id}/apply", response_model=CommonResponse)
async def apply_for_task(task_id: int, userId: str = Depends(get_current_user)):
    try:
        # 这里应该是实际的数据库操作逻辑
        # 1. 检查任务是否存在
        task = next((task for task in get_mock_tasks() if task.id == task_id), None)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # 2. 检查任务是否可以申请（例如，状态是否为 PENDING）
        if task.status != TaskStatus.PENDING:
            raise HTTPException(status_code=400, detail="This task is not available for application")
        
        # 3. 检查用户是否已经申请过这个任务
        # 这里应该查询数据库，检查用户的任务列表中是否已经包含这个任务
        # 为了演示，我们假设用户没有申请过这个任务
        
        # 4. 将任务添加到用户的"我的任务列表"中
        # 这里应该更新数据库中用户的任务列表
        # 为了演示，我们假设添加成功
        
        return CommonResponse(
            code=1,
            data={"task_id": task_id},
            message=f"Successfully applied for task {task_id}"
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 任务执行
@router.get("/api/task/my-tasks", response_model=CommonResponse)
async def get_my_tasks(userId: str = Depends(get_current_user)):
    try:
        # 这里应该是实际的数据库操作逻辑
        # 为了演示，我们使用模拟数据
        mock_tasks = get_mock_tasks()
        
        # 假设用户已申请的任务ID为1和2
        user_task_ids = [1, 2]
        
        user_tasks = [task for task in mock_tasks if task.id in user_task_ids]
        
        return CommonResponse(
            code=1,
            data=user_tasks,
            message='User tasks retrieved successfully'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/task/{task_id}/submit", response_model=CommonResponse)
async def submit_task(task_id: int, userId: str = Depends(get_current_user)):
    try:
        # 1. 检查任务是否存在
        task = next((task for task in get_mock_tasks() if task.id == task_id), None)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # 2. 检查任务是否属于当前用户
        # 这里应该查询数据库，确认任务是否在用户的任务列表中
        # 为了演示，我们假设任务属于当前用户
        
        # 3. 检查任务状态是否为进行中
        if task.status != TaskStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Task is not in progress")
        
        # 4. 更新任务状态为已完成
        # 这里应该更新数据库中的任务状态
        task.status = TaskStatus.COMPLETED
        task.updated_at = datetime.now()
        
        return CommonResponse(
            code=1,
            data={"task_id": task_id},
            message=f"Task {task_id} submitted successfully."
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/task/{task_id}/feedback", response_model=CommonResponse)
async def get_task_feedback(task_id: int, userId: str = Depends(get_current_user)):
    try:
        # 1. 检查任务是否存在
        task = next((task for task in get_mock_tasks() if task.id == task_id), None)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # 2. 检查任务是否属于当前用户
        # 这里应该查询数据库，确认任务是否在用户的任务列表中
        # 为了演示，我们假设任务属于当前用户
        
        # 3. 获取任务反馈信息
        # 这里应该从数据库中获取实际的反馈信息
        # 为了演示，我们使用模拟数据
        feedback = {
            "status": "approved" if task.status == TaskStatus.COMPLETED else "pending",
            "comments": "Great job!" if task.status == TaskStatus.COMPLETED else "Still under review.",
            "review_date": datetime.now().isoformat() if task.status == TaskStatus.COMPLETED else None
        }
        
        return CommonResponse(
            code=1,
            data={
                "task_id": task_id,
                "feedback": feedback
            },
            message="Task feedback retrieved successfully"
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 报酬结算
@router.get("/api/reward/history", response_model=CommonResponse)
async def get_reward_history(userId: str = Depends(get_current_user)):
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
        
        return CommonResponse(
            code=1,
            data={
                "reward_history": reward_history,
                "total_reward": total_reward
            },
            message="Reward history retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/reward/withdraw", response_model=CommonResponse)
async def withdraw_reward(
    amount: float,
    payment_method: str,
    user_id: str = Depends(get_current_user)
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

        return CommonResponse(
            code=1,
            data={
                "user_id": user_id,
                "amount": amount,
                "payment_method": payment_method,
                "request_date": datetime.now().isoformat(),
                "status": "Pending"
            },
            message="Withdrawal request submitted successfully"
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/reward/withdraw-status", response_model=CommonResponse)
async def get_withdraw_status(user_id: str = Depends(get_current_user)):
    try:
        # 这里应该从数据库中获取用户的提现记录
        # 为了演示，我们使用模拟数据
        withdraw_history = [
            {
                "id": 1,
                "amount": 100.0,
                "payment_method": "PayPal",
                "request_date": "2023-05-01T10:00:00",
                "status": "Completed"
            },
            {
                "id": 2,
                "amount": 50.0,
                "payment_method": "Mobile Money",
                "request_date": "2023-05-10T14:30:00",
                "status": "Pending"
            }
        ]
        
        return CommonResponse(
            code=1,
            data={
                "withdraw_history": withdraw_history,
                "pending_withdrawals": [w for w in withdraw_history if w["status"] == "Pending"]
            },
            message="Withdrawal status and history retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))