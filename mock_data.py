from datetime import datetime, timedelta
import random
from schemas import EnterpriseRegistration, EnterpriseResponse, RefugeeTask, RegisterRefugeeTask, Task, TaskStatus, TaskType, TaskDifficulty, TaskProgress
from pydantic import HttpUrl
import hashlib

def get_mock_tasks():
    now = datetime.now()
    return [
        Task(
            id=1,
            user_id=1,  # 添加用户ID字段
            title="数据输入：客户信息",
            description="将纸质客户信息表格输入到我们的CRM系统中",
            type=TaskType.DATA_ENTRY,
            difficulty=TaskDifficulty.EASY,
            status=TaskStatus.IN_PROGRESS,
            created_at=now - timedelta(days=random.randint(1, 30)),
            updated_at=now - timedelta(days=random.randint(0, 7)),
            deadline=now + timedelta(days=7),
            reward_per_unit=0.5,
            total_units=1000,
            completed_units=350,
            resources=[HttpUrl("https://example.com/customer_info_template.pdf")],
            review_comment="",
            rating=None
        ),
        Task(
            id=2,
            user_id=2,  # 添加用户ID字段
            title="图像标注：街道场景",
            description="为自动驾驶AI标注街道场景中的物体",
            type=TaskType.IMAGE_LABELING,
            difficulty=TaskDifficulty.MEDIUM,
            status=TaskStatus.PENDING,
            created_at=now - timedelta(days=random.randint(1, 60)),
            updated_at=now - timedelta(days=random.randint(0, 30)),
            deadline=now + timedelta(days=14),
            reward_per_unit=0.2,
            total_units=5000,
            completed_units=0,
            resources=[HttpUrl("https://example.com/street_scene_images.zip")],
            review_comment="",
            rating=None
        ),
        Task(
            id=3,
            user_id=None,  # 添加用户ID字段
            title="内容审核：社交媒体帖子",
            description="审核社交媒体帖子是否包含不适当内容",
            type=TaskType.CONTENT_MODERATION,
            difficulty=TaskDifficulty.HARD,
            status=TaskStatus.PENDING,
            created_at=now - timedelta(days=random.randint(30, 90)),
            updated_at=now - timedelta(days=random.randint(0, 5)),
            deadline=None,
            reward_per_unit=0.1,
            total_units=10000,
            completed_units=10000,
            resources=[HttpUrl("https://example.com/social_media_posts.json")],
            review_comment="任务完成得很好，所有帖子都已正确审核。",
            rating=4.8
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

def get_mock_enterprises():
    now = datetime.now()
    return [
        EnterpriseResponse(
            id=1,
            name="Tech Innovations Inc.",
            email="contact@techinnovations.com",
            password="password123",  # 添加密码字段
            phone="+1 (555) 123-4567",
            address="123 Silicon Valley, CA 94000, USA",
            industry="Information Technology",
            registration_number="TI12345678",
            legal_representative="John Doe",
            business_scope="Software Development, AI Research",
            establishment_date=now - timedelta(days=365*5),
            registered_capital=1000000.00,
            company_size="Medium",
            website="https://www.techinnovations.com",
            logo_url="https://www.techinnovations.com/logo.png",
            description="Leading the way in innovative tech solutions",
            created_at=now - timedelta(days=30),
            updated_at=now
        ),
        EnterpriseResponse(
            id=2,
            name="Green Energy Solutions",
            email="info@greenenergy.com",
            password="greenpass456",  # 添加密码字段
            phone="+1 (555) 987-6543",
            address="456 Eco Street, NY 10001, USA",
            industry="Renewable Energy",
            registration_number="GES87654321",
            legal_representative="Jane Smith",
            business_scope="Solar Panel Manufacturing, Wind Turbine Installation",
            establishment_date=now - timedelta(days=365*3),
            registered_capital=5000000.00,
            company_size="Large",
            website="https://www.greenenergysolutions.com",
            logo_url="https://www.greenenergysolutions.com/logo.png",
            description="Powering a sustainable future",
            created_at=now - timedelta(days=60),
            updated_at=now - timedelta(days=7)
        ),
        EnterpriseResponse(
            id=3,
            name="Local Cafe Co.",
            email="hello@localcafe.com",
            password="cafepass789",  # 添加密码字段
            phone="+1 (555) 246-8135",
            address="789 Main St, Small Town, ST 12345, USA",
            industry="Food Service",
            registration_number="LC98765432",
            legal_representative="Bob Johnson",
            business_scope="Coffee Shop, Bakery",
            establishment_date=now - timedelta(days=365),
            registered_capital=50000.00,
            company_size="Small",
            website=None,
            logo_url=None,
            description="Your cozy neighborhood cafe",
            created_at=now - timedelta(days=10),
            updated_at=now
        )
    ]

def get_mock_refugee_tasks():
    now = datetime.now()
    return [
        RefugeeTask(
            user_id=1,
            username="refugee1",
            password=hashlib.md5("password123".encode()).hexdigest(),
            phone="+1 (555) 123-4567",
            email="refugee1@example.com",
            created_at=now - timedelta(days=30),
            updated_at=now - timedelta(days=25)
        ),
        RefugeeTask(
            user_id=2,
            username="refugee2",
            password=hashlib.md5("securepass456".encode()).hexdigest(),
            phone="+1 (555) 987-6543",
            email="refugee2@example.com",
            created_at=now - timedelta(days=20),
            updated_at=now - timedelta(days=18)
        ),
        RefugeeTask(
            user_id=3,
            username="refugee3",
            password=hashlib.md5("safeword789".encode()).hexdigest(),
            phone="+1 (555) 246-8135",
            email="refugee3@example.com",
            created_at=now - timedelta(days=15),
            updated_at=now - timedelta(days=10)
        )
    ]


