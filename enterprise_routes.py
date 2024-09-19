import hashlib
import json
from fastapi import APIRouter, Body, Depends, File, UploadFile, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from auth_token import create_access_token, verify_oauth_token
from common import process_task_resources
from schemas import (
    CommonResponseBool,
    EnterpriseRegistration,
    EnterpriseResponse,
    EnterpriseResponse,
    LoginEnterpriseResponse,
    Task,
    TaskDifficulty,
    TaskFeedbackInfo,
    TaskListResponse,
    TaskProgress,
    TaskStatus,
    TaskType,
    TaskCreate,
    PARTITION_KEYS,
    TABLE_NAMES,
)
from database import (
    get_latest_id_by_partition,
    insert_entity,
    get_entity_by_field,
    update_entity_fields,
    get_all_entities,
)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter()


# 账户管理
# 企业用户注册，填写公司信息。
@router.post("/api/enterprise/register", response_model=EnterpriseResponse)
async def register_enterprise(enterprise: EnterpriseRegistration):
    try:
        # 检查邮箱是否已被注册
        existing_enterprise = get_entity_by_field(
            TABLE_NAMES.ENTERPRISE, "email", enterprise.email
        )
        if existing_enterprise:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 生成新的企业ID
        new_id = get_latest_id_by_partition(TABLE_NAMES.ENTERPRISE, "id")

        # 创建新的企业对象
        hashed_password = hashlib.md5(
            enterprise.password.encode()
        ).hexdigest()  # 使用SHA256进行密码哈希
        new_enterprise = {
            "PartitionKey": TABLE_NAMES.ENTERPRISE,
            "RowKey": str(new_id),  # Convert new_id to string
            "id": str(new_id),  # Convert new_id to string
            "name": enterprise.name,
            "email": enterprise.email,
            "password": hashed_password,
            "phone": enterprise.phone,
            "address": enterprise.address,
            "industry": enterprise.industry,
            "registration_number": enterprise.registration_number,
            "legal_representative": enterprise.legal_representative,
            "business_scope": enterprise.business_scope,
            "establishment_date": enterprise.establishment_date.isoformat(),
            "registered_capital": str(
                enterprise.registered_capital
            ),  # Convert to string
            "company_size": enterprise.company_size,
            "website": enterprise.website,
            "logo_url": enterprise.logo_url,
            "description": enterprise.description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        try:
            # 将新企业添加到Azure表存储
            insert_entity(TABLE_NAMES.ENTERPRISE, new_enterprise)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Bad Request: {str(e)}")

        # 获取新添加的企业数据
        new_enterprise_data = get_entity_by_field(TABLE_NAMES.ENTERPRISE, "id", new_id)
        if not new_enterprise_data:
            raise HTTPException(
                status_code=404, detail="Newly created enterprise not found"
            )

        # 将datetime对象转换为ISO格式字符串
        new_enterprise_data["establishment_date"] = datetime.fromisoformat(
            new_enterprise_data["establishment_date"]
        ).isoformat()
        new_enterprise_data["created_at"] = datetime.fromisoformat(
            new_enterprise_data["created_at"]
        ).isoformat()
        new_enterprise_data["updated_at"] = datetime.fromisoformat(
            new_enterprise_data["updated_at"]
        ).isoformat()

        # 转换为EnterpriseResponse对象并返回
        return EnterpriseResponse(**new_enterprise_data)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        # 如果发生错误，抛出HTTP异常
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/api/enterprise/login", response_model=LoginEnterpriseResponse)
async def login_enterprise(
    email: Optional[str] = None,
    password: Optional[str] = None,
    oauth_token: Optional[str] = None,
):
    try:
        access_token = None
        if oauth_token:
            # OAuth认证逻辑
            # 这里应该验证OAuth token并获取企业信息
            enterprise_id = verify_oauth_token(
                oauth_token
            )  # 假设这个函数用于验证OAuth token
            if enterprise_id is None:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            access_token = create_access_token(data={"sub": str(enterprise_id)})
        elif email and password:
            # 邮箱密码认证逻辑
            enterprise_id = verify_enterprise_credentials(
                email, password
            )  # 从数据库中获取认证id
            if not enterprise_id:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            access_token = create_access_token(data={"sub": str(enterprise_id)})
        else:
            raise HTTPException(status_code=400, detail="Invalid login credentials")

        # 返回登录响应
        return LoginEnterpriseResponse(access_token=access_token, token_type="bearer")
    except Exception as e:
        error_message = (
            str(e) if str(e) else "An unexpected error occurred during login"
        )
        raise HTTPException(status_code=401, detail=error_message)


# 验证邮箱和密码
def verify_enterprise_credentials(email: str, password: str) -> Optional[int]:
    # 从数据库中获取企业数据
    enterprise = get_entity_by_field(TABLE_NAMES.ENTERPRISE, "email", email)

    if enterprise is None:
        return None

    # 获取存储的密码哈希
    stored_password_hash = enterprise.get("password")

    if not stored_password_hash:
        return None

    # 验证密码
    verify_password = hashlib.md5(password.encode()).hexdigest() == stored_password_hash
    if verify_password:
        return int(enterprise.get("id"))
    return None


# 发送忘记密码邮件，允许密码重置
@router.get("/api/enterprise/forgot-password")
async def forgot_password(email: str):
    try:
        # 检查邮箱是否存在
        enterprise = get_entity_by_field(TABLE_NAMES.ENTERPRISE, "email", email)
        if not enterprise:
            raise HTTPException(status_code=404, detail="Email not found")

        # 生成重置令牌
        reset_token = create_access_token(data={"sub": str(enterprise["id"])})

        # 构建重置链接
        reset_link = f"https://yourwebsite.com/reset-password?token={reset_token}"

        # 发送邮件
        subject = "Password Reset Request"
        body = f"Click the following link to reset your password: {reset_link}\n\nThis link will expire in 1 hour."
        send_email(email, subject, body)

        return {"message": "Password reset email sent successfully"}
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# 发送email方法
def send_email(to_email: str, subject: str, body: str):
    # Email configuration
    smtp_server = "smtp.example.com"  # Replace with your SMTP server
    smtp_port = 587  # Replace with your SMTP port
    smtp_username = "your_username"  # Replace with your SMTP username
    smtp_password = "your_password"  # Replace with your SMTP password
    from_email = "noreply@yourcompany.com"  # Replace with your sender email

    # Create message
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    try:
        # Create SMTP session
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Enable TLS
            server.login(smtp_username, smtp_password)

            # Send email
            server.send_message(message)

        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise


# 更新企业信息
@router.put("/api/enterprise/update-profile", response_model=EnterpriseResponse)
async def update_enterprise_profile(
    enterprise_update: EnterpriseResponse,
    enterprise_id: str = Depends(verify_oauth_token),
):
    try:
        # 从数据库获取现有企业信息
        existing_enterprise = get_entity_by_field(
            TABLE_NAMES.ENTERPRISE, PARTITION_KEYS.ROWKEY, enterprise_id
        )
        print(existing_enterprise)
        if not existing_enterprise:
            raise HTTPException(status_code=404, detail="Enterprise not found")

        updated_enterprise = {
            **existing_enterprise,
            **enterprise_update.dict(exclude_unset=True),
        }
        if enterprise_update.email:
            if enterprise_update.email != existing_enterprise[
                "email"
            ] and get_entity_by_field(
                TABLE_NAMES.ENTERPRISE, "email", enterprise_update.email
            ):
                raise HTTPException(status_code=400, detail="Email already exists")
            updated_enterprise["email"] = enterprise_update.email

        # 更新企业信息
        updated_enterprise["updated_at"] = datetime.utcnow().isoformat()

        # 保存更新后的企业信息到数据库
        update_success = update_entity_fields(
            TABLE_NAMES.ENTERPRISE,
            existing_enterprise[PARTITION_KEYS.PARKEY],
            existing_enterprise[PARTITION_KEYS.ROWKEY],
            updated_enterprise,
        )
        if not update_success:
            raise HTTPException(
                status_code=500, detail="Failed to update enterprise profile"
            )

        # Convert the updated_enterprise dictionary to an EnterpriseResponse object
        enterprise_response = EnterpriseResponse(**updated_enterprise)
        return enterprise_response
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# 任务管理
@router.post("/api/task/batch-upload")
async def batch_upload_tasks(files: List[UploadFile] = File(...)):
    return {"message": f"{len(files)} tasks uploaded successfully"}


# 创建单个任务
@router.post("/api/task/create", response_model=Task)
async def create_task(
    task: TaskCreate, enterprise_id: str = Depends(verify_oauth_token)
):
    try:
        # 验证企业用户
        enterprise = get_entity_by_field(
            TABLE_NAMES.ENTERPRISE, PARTITION_KEYS.ROWKEY, enterprise_id
        )
        if not enterprise:
            raise HTTPException(status_code=404, detail="Enterprise not found")

        # 验证任务标题是否已存在
        existing_task = get_entity_by_field(TABLE_NAMES.TASK, "title", task.title)
        if existing_task:
            raise HTTPException(
                status_code=400, detail="A task with this title already exists"
            )

        # 生成新的任务ID
        new_id = get_latest_id_by_partition(TABLE_NAMES.TASK, PARTITION_KEYS.PARKEY)

        # 创建新任务
        new_task = Task(
            id=new_id,
            enterprise_id=int(enterprise_id),
            title=task.title,
            description=task.description,
            type=TaskType(task.type),
            difficulty=TaskDifficulty(task.difficulty),
            status=TaskStatus.PENDING,
            deadline=task.deadline,
            reward_per_unit=task.reward_per_unit,
            total_units=task.total_units,
            completed_units=0,
            resources=[str(resource) for resource in task.resources],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            review_comment="",
            rating=0,
        )
        # 将新任务保存到数据库
        task_entity = {
            PARTITION_KEYS.PARKEY: str(new_task.id),
            PARTITION_KEYS.ROWKEY: str(new_task.id),
            **new_task.dict(),
        }
        # Convert list fields to JSON strings
        if "resources" in task_entity:
            task_entity["resources"] = json.dumps(
                [str(resource) for resource in task_entity["resources"]]
            )

        insert_task = insert_entity(TABLE_NAMES.TASK, task_entity)
        if not insert_task:
            raise HTTPException(status_code=500, detail="Failed to create task")

        # Convert the insert_task response to a Task object
        created_task = Task(
            id=new_task.id,
            enterprise_id=new_task.enterprise_id,
            title=new_task.title,
            description=new_task.description,
            type=new_task.type,
            difficulty=new_task.difficulty,
            status=new_task.status,
            deadline=new_task.deadline,
            reward_per_unit=new_task.reward_per_unit,
            total_units=new_task.total_units,
            completed_units=new_task.completed_units,
            resources=new_task.resources,
            created_at=datetime.fromisoformat(insert_task["date"].isoformat()),
            updated_at=datetime.fromisoformat(insert_task["date"].isoformat()),
            review_comment=new_task.review_comment,
            rating=new_task.rating,
        )

        return created_task
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the task: {str(e)}",
        )


# 获取企业发布的任务列表
@router.get("/api/task/tasks", response_model=TaskListResponse)
async def list_enterprise_tasks(
    enterprise_id: int = Depends(verify_oauth_token),
    status: Optional[TaskStatus] = Query(None),
    type: Optional[TaskType] = Query(None),
    difficulty: Optional[TaskDifficulty] = Query(None),
    min_reward: Optional[float] = Query(None, ge=0),
    max_reward: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    try:
        # 构建查询参数
        search_params = {"enterprise_id": enterprise_id}
        if status:
            search_params["status"] = status.value
        if type:
            search_params["type"] = type.value
        if difficulty:
            search_params["difficulty"] = difficulty.value
        if min_reward is not None:
            search_params["reward_per_unit__ge"] = min_reward
        if max_reward is not None:
            search_params["reward_per_unit__le"] = max_reward

        # 从数据库获取企业发布的任务列表
        all_tasks, total_count = get_all_entities(
            TABLE_NAMES.TASK, page, page_size, **search_params
        )
        # 将原始实体转换为Task对象
        tasks = []
        for task in all_tasks:
            task["resources"] = process_task_resources(task.get("resources"))
            tasks.append(Task(**task))

        return TaskListResponse(total_count=total_count, tasks=tasks)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching enterprise tasks: {str(e)}",
        )


# 查看任务实时进度
@router.get("/api/task/{task_id}/progress", response_model=TaskProgress)
async def get_task_progress(
    task_id: int, enterprise_id: str = Depends(verify_oauth_token)
):
    try:
        # 从数据库获取任务信息
        task_entity = get_entity_by_field(
            TABLE_NAMES.TASK, PARTITION_KEYS.PARKEY, str(task_id)
        )
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")

        # 验证任务是否属于当前企业用户
        if str(task_entity.get("enterprise_id")) != enterprise_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view this task's progress",
            )

        # 将原始实体转换为Task对象
        task_entity["resources"] = process_task_resources(task_entity.get("resources"))
        task = Task(**task_entity)

        # 计算进度百分比
        progress_percentage = (
            (task.completed_units / task.total_units) * 100
            if task.total_units > 0
            else 0
        )

        task_progress = TaskProgress(
            task_id=task_id,
            completed_units=task.completed_units,
            total_units=task.total_units,
            progress_percentage=progress_percentage,
            status=task.status,
        )
        return task_progress
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching task progress: {str(e)}",
        )


# 暂停任务
@router.put("/api/task/{task_id}/pause", response_model=CommonResponseBool)
async def pause_task(task_id: int, enterprise_id: str = Depends(verify_oauth_token)):
    try:
        # 从数据库获取任务
        task_entity = get_entity_by_field(
            TABLE_NAMES.TASK, PARTITION_KEYS.PARKEY, str(task_id)
        )
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")

        # 验证任务是否属于当前企业用户
        if str(task_entity.get("enterprise_id")) != enterprise_id:
            raise HTTPException(
                status_code=403, detail="You don't have permission to pause this task"
            )

        # 检查任务是否可以暂停
        current_status = task_entity.get("status")
        if current_status not in [
            TaskStatus.IN_PROGRESS.value,
            TaskStatus.PENDING.value,
        ]:
            raise HTTPException(
                status_code=400, detail="Task cannot be paused in its current state"
            )

        # 更新任务状态为暂停
        fields_to_update = {
            "status": TaskStatus.PAUSED.value,
            "updated_at": datetime.now().isoformat(),
        }

        # 将更新后的任务保存到数据库
        is_paused = update_entity_fields(
            TABLE_NAMES.TASK,
            task_entity["PartitionKey"],
            task_entity["RowKey"],
            fields_to_update,
        )

        if not is_paused:
            raise HTTPException(status_code=500, detail="Failed to pause the task")

        return CommonResponseBool(result=is_paused)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while pausing the task: {str(e)}",
        )


# 取消任务
@router.delete("/api/task/{task_id}/cancel", response_model=CommonResponseBool)
async def cancel_task(task_id: int, enterprise_id: str = Depends(verify_oauth_token)):
    try:
        # 从数据库获取任务
        task_entity = get_entity_by_field(
            TABLE_NAMES.TASK, PARTITION_KEYS.PARKEY, str(task_id)
        )
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")

        # 验证任务是否属于当前企业用户
        if str(task_entity.get("enterprise_id")) != enterprise_id:
            raise HTTPException(
                status_code=403, detail="You don't have permission to cancel this task"
            )

        # 检查任务是否可以取消
        current_status = TaskStatus(task_entity.get("status"))
        if current_status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            raise HTTPException(
                status_code=400, detail="Task cannot be cancelled in its current state"
            )

        # 更新任务状态为取消
        fields_to_update = {
            "status": TaskStatus.CANCELLED.value,
            "updated_at": datetime.now().isoformat(),
        }

        # 将更新后的任务保存到数据库
        is_cancelled = update_entity_fields(
            TABLE_NAMES.TASK,
            task_entity["PartitionKey"],
            task_entity["RowKey"],
            fields_to_update,
        )

        if not is_cancelled:
            raise HTTPException(status_code=500, detail="Failed to cancel the task")

        return CommonResponseBool(result=is_cancelled)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while cancelling the task: {str(e)}",
        )


# 审核已完成的任务结果，决定是否验收
@router.post("/api/task/{task_id}/review", response_model=CommonResponseBool)
async def review_task(
    task_id: int, is_accepted: bool, enterprise_id: str = Depends(verify_oauth_token)
):
    try:
        # 从数据库获取任务
        task_entity = get_entity_by_field(
            TABLE_NAMES.TASK, PARTITION_KEYS.PARKEY, str(task_id)
        )
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")

        # 验证任务是否属于当前企业用户
        if str(task_entity.get("enterprise_id")) != enterprise_id:
            raise HTTPException(
                status_code=403, detail="You don't have permission to review this task"
            )

        # 检查任务是否可以被审核
        current_status = TaskStatus(task_entity.get("status"))
        if current_status != TaskStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=400, detail="Task is not in progress and cannot be reviewed"
            )

        # 获取任务的总数量和已完成数量
        total_units = task_entity.get("total_units", 0)
        completed_units = task_entity.get("completed_units", 0)

        # 检查是否所有单元都已完成
        if completed_units < total_units:
            raise HTTPException(
                status_code=400,
                detail=f"Not all task units are completed. Completed: {completed_units}/{total_units}",
            )

        # 更新任务状态和审核信息
        fields_to_update = {
            "status": (
                TaskStatus.COMPLETED.value
                if is_accepted
                else TaskStatus.IN_PROGRESS.value
            ),
            "updated_at": datetime.now().isoformat(),
        }

        # 将更新后的任务保存到数据库
        is_updated = update_entity_fields(
            TABLE_NAMES.TASK,
            task_entity["PartitionKey"],
            task_entity["RowKey"],
            fields_to_update,
        )

        if not is_updated:
            raise HTTPException(
                status_code=500, detail="Failed to update the task after review"
            )

        # 如果任务被接受，可以在这里添加奖励发放的逻辑

        return CommonResponseBool(result=True)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while reviewing the task: {str(e)}",
        )


# 提供任务结果反馈和评分
@router.post("/api/task/{task_id}/feedback", response_model=CommonResponseBool)
async def provide_task_feedback(
    task_id: int,
    feedback: TaskFeedbackInfo,
    enterprise_id: str = Depends(verify_oauth_token),
):
    try:
        # 从数据库获取任务
        task_entity = get_entity_by_field(
            TABLE_NAMES.TASK, PARTITION_KEYS.PARKEY, str(task_id)
        )
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")

        # 验证任务是否属于当前企业用户
        if str(task_entity.get("enterprise_id")) != enterprise_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to provide feedback for this task",
            )

        # 检查任务状态是否为已完成
        current_status = TaskStatus(task_entity.get("status"))
        if current_status != TaskStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Task is not completed yet")

        # 更新任务的审核信息
        fields_to_update = {
            "review_comment": feedback.review_comment,
            "rating": feedback.rating,
            "updated_at": datetime.now().isoformat(),
        }

        # 将更新后的任务保存到数据库
        is_updated = update_entity_fields(
            TABLE_NAMES.TASK,
            task_entity["PartitionKey"],
            task_entity["RowKey"],
            fields_to_update,
        )

        if not is_updated:
            raise HTTPException(
                status_code=500, detail="Failed to update task with feedback"
            )

        return CommonResponseBool(result=True)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while providing task feedback: {str(e)}",
        )


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
