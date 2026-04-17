# MeowHealth Web TODO List

## Phase 1: 基础设施搭建 (计划已编写)
- [ ] 后端：初始化 FastAPI 项目，配置 SQLAlchemy (SQLite)，设置基础的 CORS 和目录结构。
- [ ] 前端：使用 Vite 初始化 React 项目，引入 Tailwind CSS 和 shadcn/ui。
- [ ] 定义并迁移基础数据库模型 (CatProfile, HealthRecord)。

## Phase 2: 核心功能实现 (设计已确认)
- [ ] 后端：实现猫咪档案 CRUD 接口。
- [ ] 后端：实现体重、疫苗等基础健康记录接口。
- [ ] 前端：实现 Dashboard 和 猫咪列表页 (含拖拽上传、待办提醒、体重图)。
- [ ] 前端：实现健康事件时间轴组件。
- [ ] 前端：实现 AI 化验单报告的卡片仪表盘展示与悬浮对话助手。
- [ ] 生成交互设计 Mockup (2026-04-09 已完成：dashboard.html + index.html)。

## Phase 3: AI 化验单模块 (待开始)
- [ ] 后端：实现文件上传接口和本地存储逻辑。
- [ ] 后端：集成 Gemini API，编写 OCR 与解读的 Prompt。
- [ ] 前端：实现文件拖拽上传组件。
- [ ] 前端：实现化验单分析结果的渲染和对比页面。

## Phase 4: 完善与部署 (待开始)
- [ ] 实现基础登录/Token 鉴权。
- [ ] 编写 Dockerfile 和 docker-compose.yml。
- [ ] 编写部署指南。
