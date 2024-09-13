from fastapi import APIRouter, File, UploadFile, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from schemas import CommonResponseBool, Task, TaskDifficulty, TaskStatus, TaskType, TaskCreate
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

@router.post("/api/task/create", response_model=dict)
async def create_task(task: TaskCreate):
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

@router.get("/api/task/{task_id}/progress", response_model=dict) # type: ignore
async def get_task_progress(task_id: int):
    try:
        # 这里应该有从数据库获取任务进度的逻辑
        # 为了演示，我们使用模拟数据
        task_progress = {
            "completed_jobs": 5, # 已完成的工作数量
            "completion_percentage": 35.0,  # 实时进度
            "completed_tasks": 350  # 已完成任务数
        }
        return task_progress
    except Exception as e:
            # 如果发生错误，返回适当的错误响应
            raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/task/{task_id}/pause", response_model=CommonResponseBool)
async def pause_task(task_id: int):
    try:
        # 这里应该是暂停任务的实际逻辑
        # 例如，更新数据库中任务的状态
        # 为了演示，我们假设任务总是能成功暂停
        is_paused = True

        return CommonResponseBool(
            result=is_paused,
        )
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/task/{task_id}/cancel", response_model=CommonResponseBool)
async def cancel_task(task_id: int):
    try:
        # 这里应该是取消任务的实际逻辑
        # 例如，更新数据库中任务的状态
        # 为了演示，我们假设任务总是能成功取消
        is_cancelled = True

        return CommonResponseBool(
            result=is_cancelled,
        )
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/task/{task_id}/review", response_model=dict)
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
        result_data = {
            "task_id": task_id,
            "is_accepted": is_accepted,
            "status": task_status,
            "review_comment": review_comment
        }
        return result_data
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/task/{task_id}/feedback", response_model=dict)
async def provide_task_feedback(task_id: int, feedback: dict):
    try:
        # 从feedback字典中获取反馈信息和评分
        rating = feedback.get('rating', 0)
        comment = feedback.get('comment', '')

        # 这里应该是保存反馈到数据库的逻辑
        # 为了演示，我们假设保存总是成功的
        result_data = {
            "task_id": task_id,
            "rating": rating,
            "comment": comment
        }
        return result_data
    except Exception as e:
        # 如果发生错误，返回适当的错误响应
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
