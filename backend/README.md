# MeowHealth Backend

猫咪健康守护 Web 版后端服务

## 技术栈

- FastAPI - 现代 Python Web 框架
- SQLAlchemy 2.0 - ORM
- SQLite + aiosqlite - 数据库（默认）
- Pydantic - 数据验证

## 项目结构

```
backend/
├── app/
│   ├── core/           # 核心配置
│   │   └── database.py # 数据库配置
│   ├── models/         # SQLAlchemy 模型
│   ├── routers/        # API 路由
│   ├── schemas/        # Pydantic 模型
│   └── services/       # 业务逻辑
├── alembic/            # 数据库迁移
├── uploads/            # 上传文件存储
├── main.py             # FastAPI 入口
├── init_database.py    # 数据库初始化脚本
└── requirements.txt    # 依赖
```

## 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 初始化数据库
```bash
python init_database.py
```

3. 启动服务
```bash
uvicorn main:app --reload
```

4. 访问 API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

- `GET /` - 欢迎信息
- `GET /health` - 健康检查
