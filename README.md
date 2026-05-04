# MeowHealth Web

"猫咪健康守护" 网页版,一个支持桌面和移动端的私有化单用户猫咪健康管理系统。核心主打 **基于多智能体架构的 AI 兽医诊疗引擎**，提供"千猫千面"的个性化健康分析。包含 7 个专业 Agent 协作：VisionAgent（OCR提取）→ HistoryAnalystAgent（历史趋势）→ LabAnalyzer（病理分析）→ ResearchAgent（知识补充）→ DietitianAgent（营养建议）→ CriticAgent（主任审查）→ ActionableAgent（自动生成复查提醒和购物清单）。

**远程仓库**: [GitHub: TangTangG/MeowHealth-Web](https://github.com/TangTangG/MeowHealth-Web) · 分支 `feature/vet-inspired-agent-flow` · 最新推送 2026-05-04（Phase 8+9 全部完成）

## 🧠 核心特性:多智能体 AI 诊疗引擎

本项目彻底摒弃了传统单体大模型的粗放式分析(极易产生幻觉和遗漏),在 Phase 4.1 中重构了一套对标专业兽医院工作流的 **Multi-Agent 专家组**,将 AI 作为系统的绝对核心:

*   **👨‍⚕️ Orchestrator (主控中枢)**:动态根据当前猫咪档案,向诊断流中挂载特异性的医疗技能(Skills)。
*   **📷 VisionAgent (提取技师)**:高度克制。仅负责医疗影像的 OCR 结构化数值提取,绝不越权做病理评估,将数据遗漏率降至最低。
*   **🔬 LabAnalyzer (病理医生)**:基于提取的化验数据与外置医学 SOP 进行比对,输出异常标志与病理诊断。
*   **🥩 DietitianAgent (营养师)**:接收病理异常列表,开具严格针对病情的饮食、用药与生活护理处方。
*   **🧬 千猫千面 (Dynamic Skills)**:解耦的 Markdown 知识树架构。如果是"缅因猫",系统会自动拉高心脏病(HCM)的敏感度;如果是"超重猫",系统会强制触发脂肪肝防御并禁止断食。
*   **💬 主治医生 1V1 追问**:报告底部内置了带有完整上下文记忆的 Chat 组件,用户可针对化验单明细直接向 Agent 团队追问方案。

## 📍 当前状态

| 阶段 | 状态 | 完成时间 |
|------|------|----------|
| Phase 1: 基础设施搭建 | ✅ 完成 | 2026-04-11 |
| Phase 2: 核心功能实现 | ✅ 完成 | 2026-04-18 |
| Phase 3: AI 化验单模块 | ✅ 完成 | 2026-04-22 |
| Phase 4.1: AI 多智能体架构重构 (Orchestrator) | ✅ 完成 | 2026-04-29 |
| Phase 5: Agent 架构演进与演化 | ✅ 完成 | 2026-05-01 |
| Phase 6: 兽医院式诊疗流水线 | ✅ 完成 | 2026-05-03 |
| Phase 4.2: 部署与安全准备 | ✅ 完成 | 2026-05-01 |

## 🛠 技术栈

- **后端**: Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **前端**: React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React
- **AI**: Gemini API (基于 Multi-Agent 架构: Orchestrator + Vision/Lab/Dietitian)

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/TangTangG/MeowHealth-Web.git
cd MeowHealth-Web
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

## 🐳 Docker 部署(推荐)

### 前置要求
- Docker
- Docker Compose

### 一键启动

```bash
cd MeowHealth-Web
docker-compose up -d --build
```

启动后访问:
- 前端:http://localhost:3000
- 后端 API:http://localhost:8000
- API 文档:http://localhost:8000/docs

### 停止服务

```bash
docker-compose down
```

### 查看日志

```bash
docker-compose logs -f
```

### 数据持久化

SQLite 数据库存储在 Docker 命名卷 `meowhealth-db` 中,即使容器删除数据也不会丢失。

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
- **体重记录**: 记录体重,查看趋势图表
- **待办提醒**: 创建、完成、删除提醒事项
- **健康记录**: 查看健康事件时间轴
- **Dashboard**: 统计卡片、体重图表、待办列表、近期动态

### Phase 3 已完成 ✅

- **文件上传**: 拖拽上传 PDF/JPG/PNG,支持多文件,显示上传进度
- **AI 化验单分析**: Gemini OCR 自动提取指标、标记异常、生成建议
- **报告展示**: 卡片式仪表盘,按系统分类(血液/肝脏/肾脏),异常高亮
- **悬浮对话助手**: 基于当前报告上下文的多轮对话,快捷提问
- **报告管理**: 列表展示、查看详情、删除报告
- **测试覆盖**: 后端 10 个 API 测试 + 前端 3 个组件测试
- **文档**: API 文档 (`docs/API.md`) + 组件文档 (`docs/Components.md`)

### Phase 6 已完成 ✅ (前端交互)

- **健康档案总览**: 顶部信息卡 + 5 Tab 切换（就诊记录/症状日志/体征趋势/化验指标/健康评分）
- **随访提醒界面**: 顶部统计 + 4 Tab + 类型图标区分 + 症状追踪快速记录
- **症状咨询流程**: 兽医院式分诊 → 引导问诊 → 诊断推理 → 健康建议
- **路由与导航**: 新增「健康档案」和「随访提醒」侧边栏入口

### Phase 6 后端已完成 ✅

- **健康档案强化**: HealthRecord 扩展（诊疗类型、分诊等级、状态、随访时间）
- **症状日志**: SymptomLog 模型与 CRUD
- **体征记录**: VitalSign 模型与 CRUD
- **分诊 Agent**: TriageAgent 规则引擎
- **问诊 Agent**: SymptomCollectorAgent 引导式问诊
- **诊断推理**: DiagnosticReasonerAgent 推理辅助
- **健康顾问**: HealthAdvisorAgent 综合建议
- **随访提醒**: MonitoringAgent 定期追踪
- **诊疗流水线**: ConsultationPipeline 状态机编排

### Phase 6.5 已完成 ✅

- **疾病知识树**: `skills/diseases/` — 12 种常见猫疾病 Markdown 知识库（CKD/甲亢/糖尿病/FIP/猫瘟/鼻支/HCM/FLUTD/胰腺炎/脂肪肝/IBD/淋巴瘤）
- **症状鉴别诊断**: `skills/symptoms/` — 8 种症状 Markdown 鉴别诊断（呕吐/腹泻/多饮多尿/精神萎靡/拒食/咳嗽/跛行/皮肤问题）
- **症状-疾病关联引擎**: `SymptomDiseaseMapper` — 从外部 Markdown 加载疾病知识，支持症状匹配 + 品种/年龄/体征加权，Top 5 排序输出
- **健康评分算法**: `HealthScoreEngine` — 后端综合评分引擎（基础80 + 4维度加分），与前端 HealthProfile 评分规则一致
- **测试覆盖**: `tests/agents/test_knowledge_engine.py` — 11 tests passing

### Phase 8 已完成 ✅

- **疫苗接种记录**: `VaccinationRecord` 模型（疫苗类型/名称/批号/接种日期/到期日期），支持 FVRCP/狂犬/其他
- **驱虫记录**: `DewormingRecord` 模型（产品名称/类型/用药日期/到期日期），支持内驱/外驱/内外同驱
- **到期自动提醒**: 创建记录时若设置了 `next_due_at`，自动在 `Reminder` 表中生成到期提醒
- **预防护理页面**: `/preventive-care` — 4 张概览卡片（记录数/到期数，到期标红）+ Tab 切换疫苗/驱虫列表
- **到期高亮**: 已到期记录红色标签提示，统计卡片红色背景
- **删除记录**: 每条记录支持删除（确认弹窗）
- **测试覆盖**: 后端 4 tests + 前端 2 tests passing

## Phase 9 已完成 ✅

- **聚合 Analytics API**: 4 个端点（体重趋势/指标历史/评分历史/指标名称列表），支持日期范围和参考范围
- **Dashboard 增强**: `DashboardIndicatorCard` 组件，展示最多 4 个最新化验指标（数值/单位/异常高亮/趋势箭头）
- **数据洞察页面**: `/analytics` — 体重趋势(90天) + 健康评分趋势(180天) + 化验指标下拉选择对比
- **PDF 导出**: `PDFExportButton` 组件，html2canvas + jsPDF，集成到 Reports 页面
- **侧边栏导航**: 新增「数据洞察」入口
- **测试覆盖**: 后端 2 tests + 前端 1 test passing

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

- 需求文档:`docs/PRD.md`
- 技术设计:`docs/SystemDesign.md`
- 数据库设计:`docs/DatabaseSchema.md`
- API 文档:`docs/API.md`
- 组件文档:`docs/Components.md`
- 交互设计规范:`docs/superpowers/specs/2026-04-09-ai-report-analysis-design.md`
- Phase 2 计划:`docs/superpowers/plans/2026-04-17-phase2-detailed.md`
- Phase 3 补全计划:`docs/superpowers/plans/2026-04-22-phase3-completion.md`

## 设计亮点

- **多智能体 AI 架构 (Phase 4.1 新增)**:彻底摒弃单体大模型引发的幻觉,采用 `Orchestrator` 编排 `VisionAgent` (纯结构化提取)、`LabAnalyzer` (病理分析)、`DietitianAgent` (营养师) 的协作流。
- **千猫千面动态诊疗**:系统内置基于 Markdown 的知识技能树 (Skills)。根据猫咪品种 (如缅因猫防心脏病、银渐层防肾病) 和体型 (肥胖防脂肪肝) 动态挂载特定规则,实现精准医疗警告与饮食建议。
- **Dashboard 概览页**:整合待办提醒、体重趋势图、近期健康事件流水。
- **沉浸式 AI 报告交互**:脉冲特效预警异常指标,多智能体流转步骤公示,并自带记忆上下文的主治医生 1V1 追问聊天组件。
- **上传入口**:独立的拖拽多文件上传区 (支持 PDF/JPG/PNG)。
- **多猫支持**:侧边栏嵌入猫咪切换器,方便多猫家庭使用。
