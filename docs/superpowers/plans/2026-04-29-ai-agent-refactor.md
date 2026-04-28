# MeowHealth Web - AI Agent 重构计划 (Phase 4.1)

## 目标
将现有的单体式化验单 AI 分析逻辑 (`ai_service.py`)，重构为「Orchestrator 主控 + Subagents 专项执行 + Skills 知识外置」的多智能体架构。引入**个性化诊疗**能力，根据猫咪的品种（Breed）和体重（Weight）动态挂载不同的 Skill 策略。

## 架构设计

*   **Orchestrator (主控)**: 接收化验单和猫咪档案（品种、体重、年龄），统筹流转，动态加载匹配的专属 Skill，聚合结果。
*   **VisionAgent (提取技师)**: 只负责图片 OCR 结构化，不做医学判断。
*   **LabAnalyzer (病理医生)**: 根据提取的数值和动态挂载的品种/体型 Skill，出具个性化病理分析（例如缅因猫和无毛猫的某些指标参考范围不同）。
*   **DietitianAgent (营养师)**: 根据异常指标和猫咪的体重等级（如超重/偏瘦），结合专属饮食 Skill，出具精准的护理和喂养建议。
*   **Skills (知识库)**: 树状结构的 Markdown/JSON 知识库，支持通用规则与品种/体重特异性规则的叠加。

## 实施阶段

- [ ] **Step 1: 建立目录结构与分层 Skills 体系** 
  - 创建 `backend/app/ai/` 及其子目录 `subagents/` 和 `skills/`。
  - 建立分类 Skill 目录：
    - `skills/common/`: 通用化验标准 (`general_lab.md`) 与通用护理 (`general_diet.md`)。
    - `skills/breeds/`: 特定品种 SOP (如 `british_shorthair.md`, `maine_coon.md` 易发心脏病)。
    - `skills/weights/`: 体重特异性 SOP (如 `overweight.md` 减脂策略, `underweight.md` 增肌策略)。

- [ ] **Step 2: 实现专职 Subagents**
  - 实现 `vision_agent.py`: 封装独立 Prompt，仅输出指标的字面数值与参考范围 JSON。
  - 实现 `lab_analyzer.py`: 接收 OCR 数据与 `[通用Skill + 品种Skill]`，进行逻辑比对，输出异常标志与病理分析。
  - 实现 `dietitian_agent.py`: 接收异常列表与 `[品种Skill + 体重Skill]`，输出可执行的个性化饮食建议。

- [ ] **Step 3: 实现 Orchestrator 动态调度引擎**
  - 实现 `orchestrator.py`: 
    - 接收 `(image_data, cat_profile)` 参数。
    - 路由并读取对应的 Skill 文件（基于猫咪的品种和体重动态组合 Context）。
    - 调度三个子 Agent 并捕获异常，输出标准化 JSON。

- [ ] **Step 4: 路由迁移与测试闭环**
  - 将 API 层调用替换为 `Orchestrator.run(image, cat_profile)`，确保前端传入猫咪的档案数据。
  - 补充测试用例，特别是**同一种化验结果，不同品种/体重猫咪得出不同建议**的场景测试。
  - 移除旧的 `ai_service.py` 逻辑。