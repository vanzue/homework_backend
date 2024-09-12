from datetime import datetime, timedelta
from schemas import Task, TaskStatus, TaskType, TaskDifficulty, TaskProgress
from pydantic import HttpUrl

def get_mock_tasks():
    now = datetime.now()
    return [
        Task(
            id=1,
            title="数据输入：客户信息",
            description="将纸质客户信息表格输入到我们的CRM系统中",
            type=TaskType.DATA_ENTRY,
            difficulty=TaskDifficulty.EASY,
            status=TaskStatus.IN_PROGRESS,
            created_at=now,
            updated_at=now,
            deadline=now + timedelta(days=7),
            reward_per_unit=0.5,
            total_units=1000,
            completed_units=350,
            resources=[HttpUrl("https://example.com/customer_info_template.pdf")]
        ),
        Task(
            id=2,
            title="图像标注：街道场景",
            description="为自动驾驶AI标注街道场景中的物体",
            type=TaskType.IMAGE_LABELING,
            difficulty=TaskDifficulty.MEDIUM,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            deadline=now + timedelta(days=14),
            reward_per_unit=0.2,
            total_units=5000,
            completed_units=0,
            resources=[HttpUrl("https://example.com/street_scene_images.zip")]
        ),
        Task(
            id=3,
            title="内容审核：社交媒体帖子",
            description="审核社交媒体帖子是否包含不适当内容",
            type=TaskType.CONTENT_MODERATION,
            difficulty=TaskDifficulty.HARD,
            status=TaskStatus.COMPLETED,
            created_at=now - timedelta(days=5),
            updated_at=now,
            deadline=None,
            reward_per_unit=0.1,
            total_units=10000,
            completed_units=10000,
            resources=[HttpUrl("https://example.com/social_media_posts.json")]
        ),
    ]

def get_mock_task_progress(task_id: int) -> TaskProgress:
    progress_data = {
        1: TaskProgress(
            task_id=1,
            completed_units=350,
            total_units=1000,
            progress_percentage=35.0,
            estimated_completion_time=datetime.now() + timedelta(days=2)
        ),
        2: TaskProgress(
            task_id=2,
            completed_units=0,
            total_units=5000,
            progress_percentage=0.0,
            estimated_completion_time=datetime.now() + timedelta(days=14)
        ),
        3: TaskProgress(
            task_id=3,
            completed_units=10000,
            total_units=10000,
            progress_percentage=100.0,
            estimated_completion_time=None
        )
    }
    return progress_data.get(task_id)