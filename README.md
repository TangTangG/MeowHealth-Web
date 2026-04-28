# MeowHealth Web

"猫咪健康守护" 网页版，一个支持桌面和移动端的私有化单用户猫咪健康管理系统。

## 当前状态

| 阶段 | 状态 | 完成时间 |
|------|------|----------|
| Phase 1: 基础设施搭建 | ✅ 完成 | 2026-04-11 |
| Phase 2: 核心功能实现 | ✅ 完成 | 2026-04-18 |
| Phase 3: AI 化验单模块 | ✅ 完成 | 2026-04-22 |
| Phase 4.1: AI 多智能体架构重构 (Orchestrator) | ✅ 完成 | 2026-04-29 |
| Phase 4.2: 完善与部署 | ⏳ 待开始 | - |

## 技术栈

- **后端**: Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **前端**: React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React
- **AI**: Gemini API (基于 Multi-Agent 架构: Orchestrator + Vision/Lab/Dietitian)

## 快速开始

### 1. 克隆项目

```bash
cd /Users/gu/openclaw_workspace/projects/MeowHealth-Web
```

### 2. 启动后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

后端服务运行在 http://localhost:8000

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端服务运行在 http://localhost:5173

## 测试

### 后端测试

```bash
cd backend
python3 -m pytest tests/ -v
```

### 前端测试

```bash
cd frontend
npx vitest run
```

## 功能清单

### Phase 2 已完成 ✅

- **猫咪管理**: 添加、删除、查看猫咪档案
- **体重记录**: 记录体重，查看趋势图表
- **待办提醒**: 创建、完成、删除提醒事项
- **健康记录**: 查看健康事件时间轴
- **Dashboard**: 统计卡片、体重图表、待办列表、近期动态

### Phase 3 已完成 ✅

- **文件上传**: 拖拽上传 PDF/JPG/PNG，支持多文件，显示上传进度
- **AI 化验单分析**: Gemini OCR 自动提取指标、标记异常、生成建议
- **报告展示**: 卡片式仪表盘，按系统分类（血液/肝脏/肾脏），异常高亮
- **悬浮对话助手**: 基于当前报告上下文的多轮对话，快捷提问
- **报告管理**: 列表展示、查看详情、删除报告
- **测试覆盖**: 后端 10 个 API 测试 + 前端 3 个组件测试
- **文档**: API 文档 (`docs/API.md`) + 组件文档 (`docs/Components.md`)

## 项目结构

```
MeowHealth-Web/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── core/           # 数据库配置
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── routers/        # API 路由
│   │   ├── schemas/        # Pydantic 模型
│   │   └── services/       # 业务逻辑
│   ├── main.py             # 应用入口
│   └── requirements.txt
├── frontend/               # React 前端
│   ├── src/
│   │   ├── components/     # 共享组件
│   │   ├── lib/            # API 客户端
│   │   ├── pages/          # 页面组件
│   │   └── types/          # TypeScript 类型
│   └── package.json
├── docs/                   # 文档
│   ├── PRD.md              # 需求文档
│   ├── SystemDesign.md     # 技术设计
│   └── superpowers/        # 计划文档
└── README.md
```

## 文档导航

- 需求文档：`docs/PRD.md`
- 技术设计：`docs/SystemDesign.md`
- 数据库设计：`docs/DatabaseSchema.md`
- API 文档：`docs/API.md`
- 组件文档：`docs/Components.md`
- 交互设计规范：`docs/superpowers/specs/2026-04-09-ai-report-analysis-design.md`
- Phase 2 计划：`docs/superpowers/plans/2026-04-17-phase2-detailed.md`
- Phase 3 补全计划：`docs/superpowers/plans/2026-04-22-phase3-completion.md`

## 设计亮点

- **多智能体 AI 架构 (Phase 4.1 新增)**：彻底摒弃单体大模型引发的幻觉，采用 `Orchestrator` 编排 `VisionAgent` (纯结构化提取)、`LabAnalyzer` (病理分析)、`DietitianAgent` (营养师) 的协作流。
- **千猫千面动态诊疗**：系统内置基于 Markdown 的知识技能树 (Skills)。根据猫咪品种 (如缅因猫防心脏病、银渐层防肾病) 和体型 (肥胖防脂肪肝) 动态挂载特定规则，实现精准医疗警告与饮食建议。
- **Dashboard 概览页**：整合待办提醒、体重趋势图、近期健康事件流水。
- **沉浸式 AI 报告交互**：脉冲特效预警异常指标，多智能体流转步骤公示，并自带记忆上下文的主治医生 1V1 追问聊天组件。
- **上传入口**：独立的拖拽多文件上传区 (支持 PDF/JPG/PNG)。
- **多猫支持**：侧边栏嵌入猫咪切换器，方便多猫家庭使用。
