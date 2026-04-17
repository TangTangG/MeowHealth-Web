# MeowHealth Web TODO List

## Phase 1: 基础设施搭建 ✅ (2026-04-11 完成)
- [x] 后端：初始化 FastAPI 项目，配置 SQLAlchemy (SQLite)，设置基础的 CORS 和目录结构。
- [x] 前端：使用 Vite 初始化 React 项目，引入 Tailwind CSS 和 React Router。
- [x] 定义并迁移基础数据库模型 (Cat, HealthRecord, WeightLog, Reminder)。

## Phase 2: 核心功能实现 ✅ (2026-04-18 完成)
- [x] 后端：实现猫咪档案 CRUD 接口。
- [x] 后端：实现体重、提醒等基础健康记录接口。
- [x] 前端：实现 Dashboard 页面（统计卡片、体重图表、待办提醒、时间轴）。
- [x] 前端：实现猫咪列表页（添加、删除）。
- [x] 前端：实现健康事件时间轴组件。
- [ ] 前端：实现 AI 化验单报告的卡片仪表盘展示与悬浮对话助手（移至 Phase 3）。

## Phase 3: AI 化验单模块 🔄 (进行中)
- [ ] 后端：实现文件上传接口和本地存储逻辑。
- [ ] 后端：集成 Gemini API，编写 OCR 与解读的 Prompt。
- [ ] 前端：实现文件拖拽上传组件。
- [ ] 前端：实现化验单分析结果的渲染和对比页面。

## Phase 4: 完善与部署 ⏳ (待开始)
- [ ] 实现基础登录/Token 鉴权。
- [ ] 编写 Dockerfile 和 docker-compose.yml。
- [ ] 编写部署指南。
