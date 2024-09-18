import hashlib
from fastapi import APIRouter, File, UploadFile, Query, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from auth_token import create_access_token, verify_oauth_token
from schemas import CommonResponseBool, EnterpriseRegistration, EnterpriseResponse, EnterpriseResponse, LoginEnterpriseResponse, Task, TaskCreateResponse, TaskDifficulty, TaskFeedback, TaskFeedbackInfo, TaskFeedbackResponse, TaskProgress, TaskStatus, TaskType, TaskCreate
from mock_data import get_mock_enterprises, get_mock_tasks

router = APIRouter()

# 账户管理
@router.post("/api/enterprise/register", response_model=EnterpriseResponse)
async def register_enterprise(enterprise: EnterpriseRegistration):
    try:
        # 获取现有企业列表
        enterprises = get_mock_enterprises()
        
        # 生成新的企业ID
        new_id = max(e.id for e in enterprises) + 1
        
        # 创建新的企业对象
        new_enterprise = EnterpriseResponse(
            id=new_id,
            name=enterprise.name,
            email=enterprise.email,
            password=hashlib.md5(enterprise.email.encode()).hexdigest(),  # 使用邮箱作为初始密码并进行MD5哈希
            phone=enterprise.phone,
            address=enterprise.address,
            industry=enterprise.industry,
            registration_number=enterprise.registration_number,
            legal_representative=enterprise.legal_representative,
            business_scope=enterprise.business_scope,
            establishment_date=enterprise.establishment_date,
            registered_capital=enterprise.registered_capital,
            company_size=enterprise.company_size,
            website=enterprise.website,
            logo_url=enterprise.logo_url,
            description=enterprise.description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
        # 将新企业添加到列表中
        enterprises.append(new_enterprise)
        
        return new_enterprise
    except Exception as e:
        # 如果发生错误，抛出HTTP异常
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/enterprise/login", response_model=LoginEnterpriseResponse)
async def login_enterprise(
    email: Optional[str] = None,
    password: Optional[str] = None,
    oauth_token: Optional[str] = None
):
    try:
        access_token = None
        if oauth_token:
            # OAuth认证逻辑
            # 这里应该验证OAuth token并获取企业信息
            enterprise_id = verify_oauth_token(oauth_token)  # 假设这个函数用于验证OAuth token
            if enterprise_id is None:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            access_token = create_access_token(data={"sub": str(enterprise_id)})
        elif email and password:
            # 邮箱密码认证逻辑
            enterprise_id = verify_enterprise_credentials(email, password)  # 从数据库中获取认证id
            if not enterprise_id:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            access_token = create_access_token(data={"sub": str(enterprise_id)})
        else:
            raise HTTPException(status_code=400, detail="Invalid login credentials")
        
        # 返回登录响应
        return LoginEnterpriseResponse(
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        error_message = str(e) if str(e) else "An unexpected error occurred during login"
        raise HTTPException(status_code=401, detail=error_message)

#验证邮箱和密码
def verify_enterprise_credentials(email: str, password: str) -> bool:
    # 获取所有企业数据
    enterprises = get_mock_enterprises()
    # 查找匹配邮箱的企业
    enterprise = next((e for e in enterprises if e.email == email), None)
    
    if enterprise is None:
        return False
    
    # 在实际应用中，我们应该从数据库中获取存储的密码哈希
    # 这里为了演示，我们假设密码是邮箱地址的MD5哈希
    # 警告：这只是一个示例，实际应用中应使用更安全的哈希算法和加盐处理
    mock_password_hash = hashlib.md5(enterprise.password.encode()).hexdigest()
    
    # 对输入的密码进行MD5哈希处理
    input_password_hash = hashlib.md5(password.encode()).hexdigest()
    # 比较提供的密码哈希和模拟的密码哈希
    print(input_password_hash, mock_password_hash)
    if input_password_hash == mock_password_hash:
        return enterprise.id
    return None

@router.post("/api/enterprise/forgot-password")
async def forgot_password():
    return {"message": "Password reset email sent"}

@router.put("/api/enterprise/update-profile")
async def update_enterprise_profile():
    return {"message": "Enterprise profile updated successfully"}

# 任务管理
@router.post("/api/task/batch-upload")
async def batch_upload_tasks(files: List[UploadFile] = File(...)):
    return {"message": f"{len(files)} tasks uploaded successfully"}

@router.post("/api/task/create", response_model=Task)
async def create_task(task: TaskCreate):
    # 获取现有任务列表
    existing_tasks = get_mock_tasks()
    
    # 生成新的任务ID
    new_id = max(t.id for t in existing_tasks) + 1
    
    # 创建新任务
    new_task = Task(
        id=new_id,
        title=task.title,
        description=task.description,
        type=task.type,
        difficulty=task.difficulty,
        status=TaskStatus.PENDING,  # 新创建的任务默认为待处理状态
        deadline=task.deadline,
        reward_per_unit=task.reward_per_unit,
        total_units=task.total_units,
        completed_units=0,  # 新任务完成单位数为0
        resources=task.resources,  # 添加资源字段
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 在实际应用中，这里应该将新任务保存到数据库
    # 为了演示，我们只返回新创建的任务对象
    return new_task

@router.get("/api/task/list", response_model=List[Task])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    type: Optional[TaskType] = Query(None),
    difficulty: Optional[TaskDifficulty] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    try:
        tasks = get_mock_tasks()

        # 根据查询参数筛选任务
        if status:
            tasks = [task for task in tasks if task.status == status]
        if type:
            tasks = [task for task in tasks if task.type == type]
        if difficulty:
            tasks = [task for task in tasks if task.difficulty == difficulty]

        # 简单的分页逻辑
        start = (page - 1) * page_size
        end = start + page_size
        return tasks[start:end]
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

#查看任务实时进度
@router.get("/api/task/{task_id}/progress", response_model=TaskProgress)
async def get_task_progress(task_id: int):
    try:
        # 从数据库获取任务信息
        task = await get_task_from_database(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # 计算进度百分比
        progress_percentage = (task.completed_units / task.total_units) * 100 if task.total_units > 0 else 0
        
        # 估算完成时间（如果有足够的数据）
        estimated_completion_time = None
        if task.created_at and task.completed_units > 0:
            time_elapsed = datetime.now() - task.created_at
            units_per_second = task.completed_units / time_elapsed.total_seconds()
            remaining_units = task.total_units - task.completed_units
            if units_per_second > 0:
                estimated_seconds = remaining_units / units_per_second
                estimated_completion_time = datetime.now() + timedelta(seconds=estimated_seconds)
        
        task_progress = TaskProgress(
            task_id=task_id,
            completed_units=task.completed_units,
            total_units=task.total_units,
            progress_percentage=progress_percentage,
            estimated_completion_time=estimated_completion_time
        )
        return task_progress
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

async def get_task_from_database(task_id: int) -> Task:
    # 这里应该是从数据库获取任务的实际逻辑
    # 为了演示，我们使用模拟数据
    tasks = get_mock_tasks()
    task = next((t for t in tasks if t.id == task_id), None)
    if task:
        return task
    return None

#暂停任务
@router.put("/api/task/{task_id}/pause", response_model=CommonResponseBool)
async def pause_task(task_id: int):
    try:
        # 从数据库获取任务
        task = await get_task_from_database(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 检查任务是否可以暂停
        if task.status not in [TaskStatus.IN_PROGRESS, TaskStatus.PENDING]:
            raise HTTPException(status_code=400, detail="Task cannot be paused in its current state")

        # 更新任务状态为暂停
        task.status = TaskStatus.PAUSED
        task.updated_at = datetime.now()

        # 将更新后的任务保存到数据库
        is_paused = await update_task_in_database(task)

        if not is_paused:
            raise HTTPException(status_code=500, detail="Failed to pause the task")

        return CommonResponseBool(
            result=is_paused,
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

async def update_task_in_database(task: Task) -> bool:
    # 这里应该是更新数据库中任务的实际逻辑
    # 为了演示，我们假设更新总是成功的
    return True

#取消任务
@router.delete("/api/task/{task_id}/cancel", response_model=CommonResponseBool)
async def cancel_task(task_id: int):
    try:
        # 从数据库获取任务
        task = await get_task_from_database(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 检查任务是否可以取消
        if task.status == TaskStatus.COMPLETED or task.status == TaskStatus.CANCELLED:
            raise HTTPException(status_code=400, detail="Task cannot be cancelled in its current state")

        # 更新任务状态为取消
        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.now()

        # 将更新后的任务保存到数据库
        is_cancelled = await update_task_in_database(task)

        if not is_cancelled:
            raise HTTPException(status_code=500, detail="Failed to cancel the task")

        return CommonResponseBool(
            result=is_cancelled,
        )
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))
    
#审核已完成的任务结果，决定是否验收
@router.post("/api/task/{task_id}/review", response_model=CommonResponseBool)
async def review_task(task_id: int, is_accepted: bool):
    try:
        # 从数据库获取任务
        task = await get_task_from_database(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 检查任务是否可以被审核
        if task.status != TaskStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Task is not in progress and cannot be reviewed")

        if is_accepted:
            task.status = TaskStatus.COMPLETED
        else:
            task.status = TaskStatus.IN_PROGRESS

        # 更新任务的审核信息
        task.updated_at = datetime.now()

        # 将更新后的任务保存到数据库
        is_updated = await update_task_in_database(task)

        if not is_updated:
            raise HTTPException(status_code=500, detail="Failed to update the task after review")

        result_data = CommonResponseBool(
            result=True
        )
        return result_data
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#提供任务结果反馈和评分
@router.post("/api/task/{task_id}/feedback", response_model=CommonResponseBool)
async def provide_task_feedback(task_id: int, feedback: TaskFeedbackInfo):
    try:
        # 检查任务是否存在
        task = await get_task_from_database(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 检查任务状态是否为已完成
        if task.status != TaskStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Task is not completed yet")

        # 更新任务的审核信息
        task.review_comment = feedback.review_comment
        task.rating = feedback.rating
        task.updated_at = datetime.now()
        
        is_updated = await update_task_in_database(task)
        if not is_updated:
            raise HTTPException(status_code=500, detail="Failed to update task with feedback")

        result_data = CommonResponseBool(
            result=True
        )
        return result_data
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 报酬管理
@router.post("/api/reward/set")
async def set_reward():
    return {"message": "Reward set successfully"}

@router.post("/api/reward/pay")
async def pay_reward():
    return {"message": "Payment initiated"}

# API接口
@router.post("/api/task/integrate")
async def integrate_task():
    return {"message": "Task integration successful"}

@router.get("/api/task/status-callback")
async def task_status_callback():
    return {"message": "Task status updated"}

@router.get("/api/task/{task_id}/details", response_model=Task)
async def get_task_details(task_id: int):
    tasks = get_mock_tasks()
    task = next((task for task in tasks if task.id == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
