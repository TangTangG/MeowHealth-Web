# MeowHealth Web 总体技术设计文档

## 1. 架构概览
系统采用前后端分离架构，前端聚焦交互与多端适配，后端负责业务逻辑、AI 调度与数据持久化。

## 2. 技术栈
- **前端 (Frontend)**
  - 框架：React 18 + Vite
  - 样式：Tailwind CSS
  - 组件库：shadcn/ui
  - 路由：React Router
  - 状态管理：Zustand / React Query
- **后端 (Backend)**
  - 框架：Python FastAPI
  - 数据库：SQLite (默认，方便单机私有部署) / PostgreSQL (可选)
  - ORM：SQLAlchemy 2.0
  - AI 集成：`google-genai` (对接 Gemini)
- **部署 (Deployment)**
  - Docker & Docker Compose (Frontend + Backend 编排)

## 3. 核心系统模块设计

### 3.1 档案与记录模块
- **数据结构**：
  - `CatProfile` (猫咪实体)
  - `HealthRecord` (健康事件流水表，基于类型分类：weight, vaccine, symptom等)
- **交互**：前端通过表单提交，后端校验后入库，提供按时间轴检索的 API。

### 3.2 AI 报告分析模块
- **处理管线**：
  1. 前端多文件上传 (File Upload API)。
  2. 后端接收文件并转存至本地存储卷。
  3. 后端组装 Prompt 并调用 Gemini API 进行 OCR 和解读。
  4. 结构化结果 (JSON) 入库，并返回给前端展示。
- **存储**：原始文件路径和解析后的结构化数据分开存储，便于后续追溯和重新分析。

### 3.3 通知与提醒模块 (Web 化方案)
- iOS 版使用本地推送，Web 版转为：
  1. 数据库级的 `Reminder` 表单。
  2. Dashboard 登录即拉取。
  3. (可选进阶) Web Push API 或集成 Server酱/Telegram Bot 发送外部提醒。

## 4. API 路由规划 (草案)
- `GET /api/v1/cats` - 获取猫咪列表
- `POST /api/v1/cats` - 新增档案
- `GET /api/v1/records/{cat_id}` - 获取健康流水
- `POST /api/v1/ai/analyze-report` - 提交化验单分析
- `GET /api/v1/reminders` - 获取待办提醒

