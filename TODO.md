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

## Phase 3: AI 化验单模块 ✅ (2026-04-22 完成)
- [x] 后端：实现文件上传接口 (`/api/uploads/`)
- [x] 后端：增强 AI 分析服务，支持结构化数据解析
- [x] 后端：实现报告创建和对话接口 (`/api/reports/`)
- [x] 后端：更新 Pydantic Schemas
- [x] 前端：实现拖拽上传组件 (`UploadZone`)
- [x] 前端：实现报告卡片展示 (`ReportCard`)
- [x] 前端：实现悬浮对话助手 (`ChatAssistant`)
- [x] 前端：更新 Reports 页面集成所有组件
- [x] 测试：后端 API 测试（上传、报告 CRUD、对话）— 10 tests passing
- [x] 测试：前端组件测试（ReportCard）— 3 tests passing
- [x] 文档：API 文档 (`docs/API.md`)
- [x] 文档：组件文档 (`docs/Components.md`)

## Phase 4: 完善与重构
### 4.1 AI 多智能体架构重构 (✅ 2026-04-29 完成)
- [x] 重构单体 AI 分析，引入 Orchestrator + Subagents (Vision/Lab/Dietitian) 架构。
- [x] 实现基于 Markdown 的分层 Skills 体系（通用/品种特异/体型特异）。
- [x] 更新 `ReportCard.tsx`：增加追踪溯源 Trace 面板与个性化干预 Badges。
- [x] 实现并绑定自带上下文记忆的 AI 追问聊天组件。
- [x] 修复后端 Pydantic v2 和 FastAPI lifespan 等技术债。

### 4.2 部署与安全准备 ✅ (2026-05-01 完成)
- [x] ~~实现基础登录/Token 鉴权。（移除，不需要）~~
- [x] 编写 Dockerfile 和 docker-compose.yml。
- [x] 编写部署指南。

## Phase 5: Agent 架构演进与演化 (Future 🚀)
- [x] **引入 Critic Agent (主任医师审查机制)**：在最终结果输出前进行交叉验证，构成 Actor-Critic 纠错架构，确保营养建议与病理分析不发生医学冲突。
- [x] **引入时间序列推理 (Cross-Temporal Reasoning)**：新增 HistoryAnalystAgent，结合过去的健康记录、体重趋势进行跨时间周期的纵向动态诊断（如早期慢性病预警）。
- [x] **引入 RAG 动态外脑 (Research Agent)**：升级静态 Markdown 技能树，当遭遇疑难指标时自动检索最新兽医文献、临床指南数据库，实现医学知识自我更新。
- [x] **进化为 Actionable Agent (工具调用)**：打破纯文本诊断，赋予 Agent 调用内部/外部 API 的能力。例如分析后自动调用 `/reminders` 生成 30 天后的复查提醒，或生成对应处方粮的外部购买清单。

## Phase 6: 兽医院式诊疗流水线 (进行中 🚧)
### 6.1 健康档案强化 (Backend) ✅ 完成
- [x] 扩展 HealthRecord 模型（诊疗类型、分诊等级、状态、随访时间）
- [x] 新增 SymptomLog 症状模型
- [x] 新增 VitalSign 体征模型
- [x] CRUD + Schemas（症状/体征读写）
- [x] API 路由（POST/GET/PUT）

### 6.2 分诊与问诊 Agent (进行中 🚧)
- [x] TriageAgent 分诊规则引擎
- [x] SymptomCollectorAgent 引导问诊
- [ ] DiagnosticReasonerAgent 推理诊断

### 6.3 诊疗流水线编排
- [ ] ConsultationPipeline 状态机
- [ ] HealthAdvisorAgent 健康顾问
- [ ] MonitoringAgent 随访提醒
- [ ] Orchestrator 整合

### 6.4 前端交互重构
- [ ] 诊疗入口界面
- [ ] 问诊对话界面
- [ ] 健康档案总览
- [ ] 随访提醒界面

### 6.5 知识库深化
- [ ] 疾病知识树
- [ ] 症状-疾病关联引擎
- [ ] 健康评分算法
