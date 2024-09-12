from fastapi import APIRouter, File, UploadFile, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from schemas import Task, TaskDifficulty, TaskStatus, TaskType, TaskCreate, TaskCreateResponse, TaskProgress
from mock_data import get_mock_tasks, get_mock_task_progress

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
    new_task = Task(
        id=1,  # 在实际应用中，这应该是由数据库生成的
        **task.dict(),
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        completed_units=0
    )
    
    return TaskCreateResponse(
        task=new_task,
        message="Task created successfully"
    )

@router.get("/api/task/list", response_model=List[Task])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    type: Optional[TaskType] = Query(None),
    difficulty: Optional[TaskDifficulty] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
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

@router.get("/api/task/{task_id}/progress", response_model=TaskProgress)
async def get_task_progress(task_id: int):
    progress = get_mock_task_progress(task_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return progress

@router.put("/api/task/{task_id}/pause")
async def pause_task(task_id: int):
    return {"message": f"Task {task_id} paused"}

@router.delete("/api/task/{task_id}/cancel")
async def cancel_task(task_id: int):
    return {"message": f"Task {task_id} cancelled"}

@router.get("/api/task/{task_id}/review")
async def review_task(task_id: int):
    return {"message": f"Review for task {task_id} retrieved"}

@router.post("/api/task/{task_id}/feedback")
async def provide_task_feedback(task_id: int):
    return {"message": f"Feedback for task {task_id} submitted"}

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

@router.get("/api/task/{task_id}/details", response_model=Task)
async def get_task_details(task_id: int):
    tasks = get_mock_tasks()
    task = next((task for task in tasks if task.id == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
