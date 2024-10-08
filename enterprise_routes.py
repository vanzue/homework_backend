import hashlib
import json
import uuid
from fastapi import APIRouter, Body, Depends, File, UploadFile, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from auth_token import create_access_token, verify_oauth_token
from common import process_task_resources, send_email, verify_enterprise_credentials
from schemas import (
    CommonResponseBool,
    EnterpriseRegistration,
    EnterpriseResponse,
    EnterpriseResponse,
    LoginEnterpriseResponse,
    PaymentStatus,
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
            "RowKey": str(uuid.uuid4()),  # Generate a unique UUID
            "id": new_id,  # Convert new_id to string
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
            # 将新企业添加到Azure表存储并获取新添加的企业数据
            new_enterprise_data = insert_entity(TABLE_NAMES.ENTERPRISE, new_enterprise)
            if not new_enterprise_data:
                raise HTTPException(
                    status_code=404, detail="Failed to create new enterprise"
                )

            # 将datetime对象转换为ISO格式字符串
            for date_field in ["establishment_date", "created_at", "updated_at"]:
                if date_field in new_enterprise_data:
                    new_enterprise_data[date_field] = datetime.fromisoformat(
                        new_enterprise_data[date_field]
                    ).isoformat()

            # 转换为EnterpriseResponse对象并返回
            return EnterpriseResponse(**new_enterprise_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Bad Request: {str(e)}")
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


# 发送忘记密码邮件，允许密码重置
@router.get("/api/enterprise/forgot-password", response_model=CommonResponseBool)
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

        return CommonResponseBool(result=True)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# 重置密码
@router.post("/api/enterprise/reset-password", response_model=CommonResponseBool)
async def reset_password(
    reset_token: str,
    new_password: str,
    enterprise_id: str = Depends(verify_oauth_token),
):
    try:
        # 验证重置令牌
        token_enterprise_id = verify_oauth_token(reset_token)
        if token_enterprise_id != enterprise_id:
            raise HTTPException(
                status_code=401, detail="Token does not match the enterprise ID"
            )

        # 从数据库获取企业信息
        enterprise = get_entity_by_field(
            TABLE_NAMES.ENTERPRISE, PARTITION_KEYS.ROWKEY, enterprise_id
        )
        if not enterprise:
            raise HTTPException(status_code=404, detail="Enterprise not found")

        # 更新密码
        new_password_hash = hashlib.md5(new_password.encode()).hexdigest()
        enterprise["password"] = new_password_hash

        # 更新数据库中的企业信息
        update_success = update_entity_fields(
            TABLE_NAMES.ENTERPRISE,
            enterprise[PARTITION_KEYS.PARKEY],
            enterprise[PARTITION_KEYS.ROWKEY],
            enterprise,
        )
        if not update_success:
            raise HTTPException(
                status_code=500, detail="Failed to update enterprise profile"
            )

        return CommonResponseBool(result=True)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# 更新企业信息
@router.put("/api/enterprise/update-profile", response_model=EnterpriseResponse)
async def update_enterprise_profile(
    enterprise_update: EnterpriseRegistration,
    enterprise_id: str = Depends(verify_oauth_token),
):
    try:
        # 从数据库获取现有企业信息
        existing_enterprise = get_entity_by_field(
            TABLE_NAMES.ENTERPRISE, "id", enterprise_id
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
        new_id = get_latest_id_by_partition(TABLE_NAMES.TASK, "id")

        # 创建新任务
        new_task = Task(
            id=new_id,
            enterprise_id=int(enterprise_id),
            title=task.title,
            description=task.description,
            type=task.type,
            difficulty=task.difficulty,
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
            payment_status=PaymentStatus.UNPAID,
        )
        # 将新任务保存到数据库
        task_entity = {
            PARTITION_KEYS.PARKEY: TABLE_NAMES.TASK,
            PARTITION_KEYS.ROWKEY: str(uuid.uuid4()),
            **new_task.dict(),
            "status": new_task.status.value,
            "payment_status": new_task.payment_status.value,
            "type": new_task.type.value,
            "difficulty": new_task.difficulty.value,
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
            created_at=datetime.fromisoformat(insert_task["created_at"].isoformat()),
            updated_at=datetime.fromisoformat(insert_task["updated_at"].isoformat()),
            review_comment=new_task.review_comment,
            rating=new_task.rating,
            payment_status=new_task.payment_status,  # Add this line
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
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, "id", task_id)
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
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, "id", task_id)
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
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, "id", task_id)
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
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, "id", task_id)
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
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, "id", task_id)
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
# 设置指定任务报酬数量
@router.post("/api/reward/{task_id}/set", response_model=CommonResponseBool)
async def set_reward(
    task_id: int, reward_num: float, enterprise_id: str = Depends(verify_oauth_token)
):
    try:
        # 从数据库获取任务
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, "id", task_id)
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")

        # 验证任务是否属于当前企业用户
        if str(task_entity.get("enterprise_id")) != enterprise_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to set reward for this task",
            )

        # 检查奖励数量是否为正数
        if reward_num <= 0:
            raise HTTPException(
                status_code=400, detail="Reward must be a positive number"
            )

        # 更新任务的奖励数量
        fields_to_update = {
            "reward_per_unit": reward_num,
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
            raise HTTPException(status_code=500, detail="Failed to update task reward")

        return CommonResponseBool(result=True)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while setting task reward: {str(e)}",
        )


# 任务通过审核后发起支付
@router.post("/api/reward/{task_id}/pay", response_model=CommonResponseBool)
async def pay_reward(task_id: int, enterprise_id: str = Depends(verify_oauth_token)):
    try:
        # 从数据库获取任务
        task_entity = get_entity_by_field(TABLE_NAMES.TASK, "id", task_id)
        if not task_entity:
            raise HTTPException(status_code=404, detail="Task not found")

        # 验证任务是否属于当前企业用户
        if str(task_entity.get("enterprise_id")) != enterprise_id:
            raise HTTPException(
                status_code=403, detail="You don't have permission to pay for this task"
            )

        # 检查任务状态是否为已完成
        if task_entity.get("status") != TaskStatus.COMPLETED.value:
            raise HTTPException(status_code=400, detail="Task is not completed yet")

        # Mock支付过程
        # 在实际应用中，这里应该调用真实的支付API
        payment_successful = True  # 假设支付总是成功的

        if payment_successful:
            # 更新任务状态为已支付
            fields_to_update = {
                "payment_status": PaymentStatus.PAID.value,
                "updated_at": datetime.now().isoformat(),
            }
            is_updated = update_entity_fields(
                TABLE_NAMES.TASK,
                task_entity["PartitionKey"],
                task_entity["RowKey"],
                fields_to_update,
            )
            if not is_updated:
                raise HTTPException(
                    status_code=500, detail="Failed to update task payment status"
                )

            return CommonResponseBool(result=True)
        else:
            raise HTTPException(status_code=500, detail="Payment failed")

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred during payment: {str(e)}"
        )


# 获取支付历史和报酬明细
@router.get("/api/reward/historys", response_model=TaskListResponse)
async def get_reward_history(
    enterprise_id: str = Depends(verify_oauth_token),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
):
    try:
        # 获取所有已支付的任务
        search_params = {
            "enterprise_id": enterprise_id,
            "payment_status": PaymentStatus.PAID.value,
        }
        # 获取所有任务
        all_paid_tasks, total_count = get_all_entities(
            TABLE_NAMES.TASK, page, page_size, **search_params
        )

        reward_history = []
        for task in all_paid_tasks:
            # 确保 resources 字段是一个列表
            task["resources"] = process_task_resources(task["resources"])
            reward_history.append(Task(**task))

        # Sort reward history by updated_at in descending order
        reward_history.sort(key=lambda x: x.updated_at, reverse=True)

        return TaskListResponse(total_count=total_count, tasks=reward_history)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching reward history: {str(e)}",
        )


# API接口
@router.post("/api/task/integrate")
async def integrate_task():
    return {"message": "Task integration successful"}


@router.get("/api/task/status-callback")
async def task_status_callback():
    return {"message": "Task status updated"}
