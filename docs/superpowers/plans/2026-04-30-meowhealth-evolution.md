# MeowHealth Web — 架构修复 + Phase 5 演进计划

> 📅 2026-04-30 | 基于全量代码审查制定

---

## 总览

```
Phase 4.2 (架构修复) → Phase 4.3 (功能补齐) → Phase 5.1 (Critic Agent) → Phase 5.2 (时间序列) → Phase 5.3 (RAG) → Phase 5.4 (Actionable)
```

预估总工时：~15-20 小时（子代理并行可压缩到 10-12 小时）

---

## Phase 4.2: 架构修复与清理 🔧

> 目标：消除技术债，统一架构，确保代码一致性

### Task 1: 统一 DB 引擎为异步 ✏️
- **文件**: `backend/app/core/database.py`
- **改动**:
  - 真正使用 `aiosqlite` 异步引擎
  - 所有路由从 `def` 改为 `async def`
  - 所有 `db.query()` 改为 `select()` + `await db.execute()`
  - 同步测试 fixtures 适配 async
- **影响**: 全部路由文件、测试文件
- **预计**: 2-3 小时

### Task 2: 合并两套 AI 实现 ✏️
- **文件**: `backend/app/services/ai_service.py`, `backend/app/routers/reports.py`
- **改动**:
  - 删除 `ai_service.py` 中的 `analyze_report()` (已被 orchestrator 替代)
  - 将 `chat_about_report()` 迁移到 `ai/orchestrator.py` 或 `ai/chat.py`
  - reports 路由统一使用 orchestrator 体系
  - 删除重复的 `parse_reference_range()` (已在 orchestrator 和 ai_service 中各有一份)
- **预计**: 1 小时

### Task 3: 修复 Settings API 断裂 ✏️
- **新增文件**: `backend/app/routers/settings.py`
- **修改文件**: `backend/app/schemas/schemas.py`, `backend/main.py`, `frontend/src/lib/api.ts`
- **改动**:
  - 新增 settings 路由: `GET /api/settings/api-key/status`, `POST /api/settings/api-key`
  - API Key 持久化到数据库 (新增 `SystemSetting` 模型或复用现有)
  - 前端 Settings 页面对接真实 API
  - `config.py` 改为从 DB 读取 key，保留环境变量作为 fallback
- **预计**: 1-1.5 小时

### Task 4: 统一 Upload → Analyze 流程 ✏️
- **文件**: `backend/app/routers/uploads.py`, `backend/app/routers/reports.py`, `frontend/src/lib/api.ts`
- **改动**:
  - 合并 uploads 和 reports 路由逻辑：上传后自动触发分析
  - 前端 `uploadReport` 对齐后端实际 endpoint
  - 上传接口绑定 cat_id
- **预计**: 1 小时

### Task 5: 清理死代码与冗余 ✏️
- **文件**: 多处
- **改动**:
  - 移除 `Layout.tsx` 中无用的全局 `<ChatAssistant />`
  - 删除 `CatFood` 模型或标记为 Phase 6 预留
  - 清理 reports 路由中的手动级联删除，改用 ORM cascade
- **预计**: 30 分钟

### Task 6: 测试补全 🧪
- **文件**: `backend/tests/`, `frontend/src/components/__tests__/`
- **改动**:
  - 现有测试适配 async 改动
  - 新增 settings 路由测试
  - 新增 upload+analyze 集成测试
- **预计**: 1 小时

---

## Phase 4.3: 功能补齐 🏗️

> 目标：补全核心功能，达到 iOS 版功能对等

### Task 7: Settings 前端页面 ✏️
- **文件**: `frontend/src/App.tsx`, `frontend/src/pages/Settings.tsx`
- **改动**:
  - 实现 API Key 配置界面（输入/保存/状态显示）
  - 显示当前 AI 模型信息
  - 基础设置（语言/主题预留）
- **预计**: 1 小时

### Task 8: 体重录入表单 ✏️
- **文件**: `frontend/src/pages/Dashboard.tsx` 或独立组件
- **改动**:
  - 在体重图表旁添加录入表单（日期+体重+备注）
  - 对接 `createWeightLog` API
  - 录入后自动刷新图表
- **预计**: 30 分钟

### Task 9: 品种 Skills Fallback 机制 ✏️
- **文件**: `backend/app/ai/orchestrator.py`, `backend/app/ai/skills/`
- **改动**:
  - 新增 `backend/app/ai/skills/breeds/_default.md` — 通用品种默认策略
  - orchestrator 加载 skill 时：精确匹配 → 模糊匹配 → default fallback
  - 补充 3-5 个常见品种（英短、美短、暹罗、橘猫、狸花）
- **预计**: 1 小时

### Task 10: 错误处理与用户反馈 ✏️
- **文件**: 前端全局
- **改动**:
  - 引入 Toast 通知组件 (sonner 或自制)
  - API 调用统一 catch → Toast 提示
  - Loading 状态骨架屏
- **预计**: 1 小时

---

## Phase 5.1: Critic Agent (主任医师审查) 🧠

> 目标：引入交叉验证机制，减少 AI 幻觉和医学冲突

### Task 11: 实现 CriticAgent ✏️
- **新增文件**: `backend/app/ai/subagents/critic_agent.py`
- **改动**:
  - 新建 CriticAgent，职责：审查 Orchestrator 输出的完整诊断
  - 检查项：
    - 病理诊断与营养建议是否存在医学冲突
    - 异常指标是否遗漏未解释
    - 建议是否与品种/体型知识库矛盾
  - 输出：`{ approved: bool, corrections: [...], confidence: float }`
- **预计**: 1.5 小时

### Task 12: Orchestrator 集成 Critic 流水线 ✏️
- **文件**: `backend/app/ai/orchestrator.py`
- **改动**:
  - `process_report()` 新增 Step 5: Critic 审查
  - 如果 `approved=false`，将 corrections 注入最终结果
  - ReportCard Trace 面板展示 Critic 审查步骤
- **预计**: 1 小时

### Task 13: Critic Agent 测试 🧪
- **文件**: `backend/tests/test_critic_agent.py`
- **改动**:
  - 构造有医学冲突的 mock 数据，验证 Critic 能捕获
  - 构造正常数据，验证 Critic 不误报
- **预计**: 45 分钟

---

## Phase 5.2: 时间序列推理 (跨时间诊断) 📈

> 目标：结合历史记录，实现"比上次恶化了吗？"类型的纵向分析

### Task 14: HistoryAnalystAgent ✏️
- **新增文件**: `backend/app/ai/subagents/history_analyst.py`
- **改动**:
  - 新建 HistoryAnalystAgent
  - 输入：当前报告指标 + 该猫所有历史同类报告
  - 输出：趋势判断（恶化/稳定/改善）、预警（连续上升的指标）、纵向对比摘要
- **预计**: 1.5 小时

### Task 15: 历史数据查询服务 ✏️
- **文件**: `backend/app/routers/reports.py` 或新增 service
- **改动**:
  - 新增 `get_historical_reports(cat_id, indicator_names)` 查询
  - 返回按时间排序的指标变化序列
- **预计**: 30 分钟

### Task 16: 前端趋势展示增强 ✏️
- **文件**: `frontend/src/components/ReportCard.tsx`
- **改动**:
  - 新增"历史对比"面板：关键指标折线图 (recharts)
  - 标注本次值 vs 历史均值
  - 展示 HistoryAnalyst 的趋势判断
- **预计**: 1 小时

---

## Phase 5.3: RAG 动态外脑 🔍

> 目标：从静态 Markdown 技能树升级为可检索的知识库

### Task 17: 知识库向量化存储 ✏️
- **新增文件**: `backend/app/ai/knowledge/`, `backend/app/ai/retriever.py`
- **改动**:
  - 将现有 Markdown 技能文件分 chunk 向量化
  - 使用轻量方案：本地 sentence-transformers + FAISS/ChromaDB
  - 或远程方案：Gemini embedding API
- **预计**: 2 小时

### Task 18: Orchestrator 集成 RAG ✏️
- **文件**: `backend/app/ai/orchestrator.py`, `backend/app/ai/subagents/lab_analyzer.py`
- **改动**:
  - `_load_skill()` 改为 `_retrieve_knowledge(query)` — 语义检索替代精确匹配
  - LabAnalyzer 的 prompt 动态注入检索到的知识片段
  - 保留静态 skill 作为 fallback
- **预计**: 1 小时

### Task 19: 知识库管理 API ✏️
- **新增**: `backend/app/routers/knowledge.py`
- **改动**:
  - `POST /api/knowledge/upload` — 上传兽医文献/指南 PDF
  - `GET /api/knowledge/` — 列出已索引的知识源
  - 文档上传后自动分 chunk 入库
- **预计**: 1.5 小时

---

## Phase 5.4: Actionable Agent (工具调用) 🛠️

> 目标：打破纯文本输出，Agent 可调用系统 API 执行动作

### Task 20: Tool/Function Calling 基础设施 ✏️
- **新增文件**: `backend/app/ai/tools/`
- **改动**:
  - 定义 Tool schema：`{ name, description, parameters, handler }`
  - 实现 ToolRegistry：注册/查找/执行工具
  - 初期工具：`create_reminder`, `generate_diet_plan`, `export_report_pdf`
- **预计**: 1.5 小时

### Task 21: Orchestrator 集成 Tool Calling ✏️
- **文件**: `backend/app/ai/orchestrator.py`
- **改动**:
  - DietitianAgent 输出结构化 tool_calls 而非纯文本
  - Orchestrator 解析 tool_calls 并执行对应 handler
  - 执行结果反馈到最终报告（"已为您创建 30 天后复查提醒"）
- **预计**: 1 小时

### Task 22: 前端展示工具执行结果 ✏️
- **文件**: `frontend/src/components/ReportCard.tsx`
- **改动**:
  - 报告底部展示"自动执行的操作"列表
  - 可点击跳转到对应功能（如提醒列表）
- **预计**: 45 分钟

---

## 执行顺序与依赖

```
Phase 4.2 (Tasks 1-6) ──必须先完成──→ Phase 4.3 (Tasks 7-10)
                                           │
                                           ├──→ Phase 5.1 (Tasks 11-13)
                                           ├──→ Phase 5.2 (Tasks 14-16)
                                           │         ↑
                                           │    需要 Task 1 (async DB)
                                           ├──→ Phase 5.3 (Tasks 17-19)
                                           └──→ Phase 5.4 (Tasks 20-22)
                                                     ↑
                                                需要 Phase 5.1
```

**推荐并行策略：**
- Phase 4.2 的 Tasks 可按 1→2→3→4→5→6 串行（有依赖）
- Phase 4.3 的 Tasks 7-10 可并行
- Phase 5.1 和 5.2 可并行启动
- Phase 5.3 独立于 5.1/5.2
- Phase 5.4 需要等 5.1 完成

---

## 里程碑检查点

| 检查点 | 完成标志 | 验证方式 |
|--------|---------|---------|
| Phase 4.2 完成 | 所有路由 async，AI 代码无重复，Settings 可用 | `pytest` 全绿 + 手动走查 Settings 页面 |
| Phase 4.3 完成 | 前端无占位页面，Toast 通知工作，品种 fallback 生效 | 手动测试全流程 |
| Phase 5.1 完成 | Critic 审查在报告 Trace 中可见 | 构造冲突数据验证 |
| Phase 5.2 完成 | 报告页面显示历史对比 | 上传两次报告验证趋势 |
| Phase 5.3 完成 | 未知品种也能给出建议 | 上传非预设品种化验单 |
| Phase 5.4 完成 | 分析后自动生成提醒 | 检查 reminders 表新增记录 |
