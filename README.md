# 难民任务管理平台

这是一个使用 FastAPI 构建的难民任务管理平台的后端 API。该平台旨在连接企业用户和难民用户，提供任务发布、申请、执行和报酬管理等功能。

## 功能特点

- 企业用户和难民用户分别的注册和登录系统
- 任务管理：创建、浏览、申请、执行和提交任务
- 报酬管理：设置报酬、查看历史、提现等
- 用户资料管理
- 支持批量上传任务

## 技术栈

- Python 3.9+
- FastAPI
- Uvicorn (ASGI server)
- Docker

## 项目结构

- `main.py`: 应用程序的入口点
- `enterprise_routes.py`: 企业用户相关的 API 路由
- `refugee_routes.py`: 难民用户相关的 API 路由
- `requirements.txt`: 项目依赖
- `Dockerfile`: 用于构建 Docker 镜像

## 快速开始

1. 克隆仓库：

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

3. 运行应用：

   ```bash
   python main.py
   ```

   应用将在 `http://localhost:8000` 上运行。

4. 使用 Docker（可选）：
   ```bash
   docker build -t refugee-task-platform .
   docker run -d -p 8000:8000 refugee-task-platform
   ```

## API 文档

启动应用后，可以在 `http://localhost:8000/docs` 查看完整的 API 文档。

## 贡献

欢迎提交 issues 和 pull requests 来帮助改进这个项目。

## 许可

[MIT License](LICENSE)
