from fastapi import APIRouter, File, UploadFile, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from schemas import CommonResponse, Task, TaskStatus, TaskType, TaskCreate, TaskCreateResponse

router = APIRouter()

# 账户管理
@router.post("/api/enterprise/register")
async def register_enterprise():
    return {"message": "Enterprise registered successfully"}

@router.post("/api/enterprise/login")
async def login_enterprise():
    return {"message": "Enterprise logged in successfully"}

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

@router.post("/api/task/create", response_model=TaskCreateResponse)
async def create_task(task: TaskCreate):
    # 这里应该是将任务保存到数据库的逻辑
    # 为了演示，我们创建一个模拟的任务对象
    new_task = Task(
        id=1,
        title="数据输入：客户信息",
        description="将纸质客户信息表格输入到我们的CRM系统中",
        type=TaskType.DATA_ENTRY,
        status=TaskStatus.IN_PROGRESS,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        deadline=datetime.now().replace(day=datetime.now().day + 7),
        reward_per_unit=0.5,
        total_units=1000,
        completed_units=350
    )

    # 在实际应用中，这里应该有错误处理逻辑
    
    return TaskCreateResponse(
        task=new_task,
        message="Task created successfully"
    )

@router.get("/api/task/list", response_model=List[Task])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    type: Optional[TaskType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    # 这里应该是从数据库获取任务列表的逻辑
    # 为了演示，我们创建一些模拟数据
    tasks = [
        Task(
            id=1,
            title="数据输入：客户信息",
            description="将纸质客户信息表格输入到我们的CRM系统中",
            type=TaskType.DATA_ENTRY,
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deadline=datetime.now().replace(day=datetime.now().day + 7),
            reward_per_unit=0.5,
            total_units=1000,
            completed_units=350
        ),
        Task(
            id=2,
            title="图像标注：街道场景",
            description="为自动驾驶AI标注街道场景中的物体",
            type=TaskType.IMAGE_LABELING,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deadline=datetime.now().replace(day=datetime.now().day + 14),
            reward_per_unit=0.2,
            total_units=5000,
            completed_units=0
        ),
        Task(
            id=3,
            title="内容审核：社交媒体帖子",
            description="审核社交媒体帖子是否包含不适当内容",
            type=TaskType.CONTENT_MODERATION,
            status=TaskStatus.COMPLETED,
            created_at=datetime.now().replace(day=datetime.now().day - 5),
            updated_at=datetime.now(),
            deadline=None,
            reward_per_unit=0.1,
            total_units=10000,
            completed_units=10000
        ),
    ]

    # 根据查询参数筛选任务
    if status:
        tasks = [task for task in tasks if task.status == status]
    if type:
        tasks = [task for task in tasks if task.type == type]

    # 简单的分页逻辑
    start = (page - 1) * page_size
    end = start + page_size
    return tasks[start:end]

@router.get("/api/task/{task_id}/progress", response_model=CommonResponse) # type: ignore
async def get_task_progress(task_id: int):
    # 这里应该有从数据库获取任务进度的逻辑
    # 为了演示，我们使用模拟数据
    task_progress = {
        "completed_jobs": 5, # 已完成的工作数量
        "completion_percentage": 35.0,  # 实时进度
        "completed_tasks": 350  # 已完成任务数
    }
    return CommonResponse(
        code=1,
        data=task_progress,
        message=f"Progress for task {task_id} retrieved successfully"
    )

@router.put("/api/task/{task_id}/pause", response_model=CommonResponse)
async def pause_task(task_id: int):
    try:
        # 这里应该是暂停任务的实际逻辑
        # 例如，更新数据库中任务的状态
        # 为了演示，我们假设任务总是能成功暂停
        is_paused = True

        return CommonResponse(
            code=1,
            data=is_paused,
            message=f"Task {task_id} paused successfully"
        )
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/task/{task_id}/cancel", response_model=CommonResponse)
async def cancel_task(task_id: int):
    try:
        # 这里应该是取消任务的实际逻辑
        # 例如，更新数据库中任务的状态
        # 为了演示，我们假设任务总是能成功取消
        is_cancelled = True

        return CommonResponse(
            code=1,
            data=is_cancelled,
            message=f"Task {task_id} cancelled successfully"
        )
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/task/{task_id}/review", response_model=CommonResponse)
async def review_task(task_id: int, review_data: dict):
    try:
        # 这里应该是审核任务的实际逻辑
        # 例如，从数据库获取任务结果，进行审核，更新任务状态等
        # 为了演示，我们假设审核总是成功的
        is_accepted = review_data.get('is_accepted', False)
        review_comment = review_data.get('comment', '')

        if is_accepted:
            # 更新任务状态为已完成
            task_status = TaskStatus.COMPLETED
            message = f"Task {task_id} reviewed and accepted"
        else:
            # 如果不接受，可能需要将任务状态设置回进行中或其他适当的状态
            task_status = TaskStatus.IN_PROGRESS
            message = f"Task {task_id} reviewed but not accepted"

        # 这里应该更新数据库中的任务状态和审核信息

        return CommonResponse(
            code=1,
            data={
                "task_id": task_id,
                "is_accepted": is_accepted,
                "status": task_status,
                "review_comment": review_comment
            },
            message=message
        )
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/task/{task_id}/feedback", response_model=CommonResponse)
async def provide_task_feedback(task_id: int, feedback: dict):
    try:
        # 从feedback字典中获取反馈信息和评分
        rating = feedback.get('rating', 0)
        comment = feedback.get('comment', '')

        # 这里应该是保存反馈到数据库的逻辑
        # 为了演示，我们假设保存总是成功的

        return CommonResponse(
            code=1,
            data={
                "task_id": task_id,
                "rating": rating,
                "comment": comment
            },
            message=f"Feedback for task {task_id} submitted successfully"
        )
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

# 报酬管理
@router.post("/api/reward/set")
async def set_reward():
    return {"message": "Reward set successfully"}

@router.get("/api/reward/history")
async def get_reward_history():
    return {"message": "Reward history retrieved"}

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