# Phase 5: Agent 架构演进与演化 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 MeowHealth AI 诊疗引擎从三专家流水线升级为具备审查、纵向推理、外脑检索和工具调用能力的五专家协作系统。

**Architecture:** 在现有 `MedicalOrchestrator` 流水线末端插入 Critic Agent 做最终审查；新增 HistoryAnalystAgent 在分析前注入历史趋势上下文；新增 ResearchAgent 在知识库不足时检索外部文献；ActionableAgent 在分析完成后调用内部 API 生成提醒和购物清单。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, google-generativeai (Gemini 2.0 Flash), httpx

---

## Phase 5A: Critic Agent + HistoryAnalystAgent

### Task 1: Critic Agent — 主任医师审查

**Files:**
- Create: `backend/app/ai/subagents/critic_agent.py`
- Modify: `backend/app/ai/orchestrator.py`

- [ ] **Step 1: 创建 CriticAgent 类**

```python
# backend/app/ai/subagents/critic_agent.py
import google.generativeai as genai
import json
from typing import Dict, Any, List
from app.ai.utils import clean_and_parse_json

CRITIC_PROMPT_TEMPLATE = """你是一位资深兽医科主任，负责审查下级医生的诊断报告和营养处方。

【病理分析报告】
{lab_report}

【营养处方建议】
{dietitian_advice}

【猫咪档案】
{cat_profile}

审查要求：
1. 检查病理诊断与营养建议之间是否存在医学冲突（如：肝指标异常但建议高蛋白饮食）。
2. 检查是否遗漏了关键警告（如：多项指标严重异常但未建议复查）。
3. 检查建议是否过于激进或保守。
4. 如果一切合理，直接通过。

返回 JSON：
{
  "approved": true/false,
  "flags": ["冲突或遗漏描述1", ...],
  "revised_summary": "如果需要修改，给出修正后的总结；如果通过，原样返回",
  "revised_recommendations": ["修正后的建议1", ...]  // 如果通过，原样返回
}"""

class CriticAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def review(
        self,
        lab_result: Dict[str, Any],
        recommendations: List[str],
        cat_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """审查病理报告和营养处方"""
        prompt = CRITIC_PROMPT_TEMPLATE.format(
            lab_report=json.dumps(lab_result, ensure_ascii=False, indent=2),
            dietitian_advice=json.dumps(recommendations, ensure_ascii=False),
            cat_profile=json.dumps(cat_profile, ensure_ascii=False)
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            result = clean_and_parse_json(text)
            if isinstance(result, dict):
                return result
            return {"approved": True, "flags": [], "revised_summary": "", "revised_recommendations": []}
        except Exception:
            return {"approved": True, "flags": [], "revised_summary": "", "revised_recommendations": []}
```

- [ ] **Step 2: 在 Orchestrator 中集成 CriticAgent**

修改 `backend/app/ai/orchestrator.py`：

- 在 `__init__` 中初始化 `self.critic = CriticAgent(self.api_key)`
- 在 `process_report` 方法中，第 4 步（Dietitian）之后、第 5 步（格式化）之前，插入 Critic 审查：

```python
# 4.5 Critic 审查
critic_result = self.critic.review(lab_result, recommendations, cat_profile)
if not critic_result.get("approved", True):
    # 使用修正后的版本
    lab_result["summary"] = critic_result.get("revised_summary", lab_result.get("summary"))
    recommendations = critic_result.get("revised_recommendations", recommendations)
    lab_result["critic_flags"] = critic_result.get("flags", [])
```

- [ ] **Step 3: 添加测试**

创建 `backend/tests/test_critic_agent.py`，测试：
- approved=True 场景（无冲突）
- approved=False 场景（发现冲突，返回修正建议）
- API 调用失败时的降级处理（默认通过）

- [ ] **Step 4: 运行测试验证**

```bash
cd backend && python -m pytest tests/test_critic_agent.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/ai/subagents/critic_agent.py backend/app/ai/orchestrator.py backend/tests/test_critic_agent.py
git commit -m "feat: add CriticAgent for cross-validation before final output"
```

---

### Task 2: HistoryAnalystAgent — 时间序列推理

**Files:**
- Create: `backend/app/ai/subagents/history_agent.py`
- Modify: `backend/app/ai/orchestrator.py`
- Modify: `backend/app/routers/reports.py`

- [ ] **Step 1: 创建 HistoryAnalystAgent 类**

```python
# backend/app/ai/subagents/history_agent.py
import google.generativeai as genai
import json
from typing import Dict, Any, List, Optional
from app.ai.utils import clean_and_parse_json

HISTORY_ANALYSIS_PROMPT = """你是一位擅长纵向分析的兽医。请对比猫咪的历史化验数据与当前数据，识别趋势和早期预警信号。

【猫咪档案】
{cat_profile}

【历史化验记录（按时间倒序）】
{history_records}

【当前化验数据】
{current_data}

分析要求：
1. 对比关键指标的历史变化趋势（如：肌酐从 3 个月前的 120 升至现在的 180）。
2. 识别慢性病早期信号（如：肾功能指标持续上升）。
3. 给出基于趋势的预警。

返回 JSON：
{
  "trends": [
    {"indicator": "CREA", "values": [120, 145, 180], "dates": ["2026-02", "2026-03", "2026-04"], "direction": "rising", "concern": "high"}
  ],
  "warnings": ["肌酐持续升高，提示肾功能可能进行性下降"],
  "historical_context": "该猫近 3 个月肾功能指标呈上升趋势，建议密切关注"
}"""

class HistoryAnalystAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def analyze(
        self,
        cat_profile: Dict[str, Any],
        history_records: List[Dict[str, Any]],
        current_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """纵向分析历史趋势"""
        if not history_records:
            return {"trends": [], "warnings": [], "historical_context": "无历史记录，首次分析"}

        prompt = HISTORY_ANALYSIS_PROMPT.format(
            cat_profile=json.dumps(cat_profile, ensure_ascii=False),
            history_records=json.dumps(history_records, ensure_ascii=False, indent=2),
            current_data=json.dumps(current_data, ensure_ascii=False, indent=2)
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            result = clean_and_parse_json(text)
            if isinstance(result, dict):
                return result
            return {"trends": [], "warnings": [], "historical_context": "历史分析解析失败"}
        except Exception:
            return {"trends": [], "warnings": [], "historical_context": "历史分析不可用"}
```

- [ ] **Step 2: 在 Orchestrator 中集成 HistoryAnalystAgent**

修改 `backend/app/ai/orchestrator.py`：

- 在 `__init__` 中初始化 `self.history_analyst = HistoryAnalystAgent(self.api_key)`
- 修改 `process_report` 方法签名，增加 `history_records` 参数：

```python
def process_report(self, file_path: str, mime_type: str, cat_profile: Dict[str, Any], history_records: List[Dict[str, Any]] = None) -> Dict[str, Any]:
```

- 在 Vision 提取之后、Lab 分析之前，调用历史分析：

```python
# 1.5 历史趋势分析
history_result = self.history_analyst.analyze(cat_profile, history_records or [], vision_result)
```

- 将历史上下文注入 Lab 分析的 prompt（通过新增 `historical_context` 参数）：

```python
# 2. Lab 病理分析（增加历史上下文）
lab_result = self.analyzer.analyze(vision_result, general_lab, breed_skill, history_result.get("historical_context", ""))
```

- [ ] **Step 3: 修改 LabAnalyzer 支持历史上下文**

修改 `backend/app/ai/subagents/lab_analyzer.py`：

- 在 `LAB_ANALYSIS_PROMPT_TEMPLATE` 中增加 `【历史趋势上下文】\n{historical_context}` 段落
- 修改 `analyze` 方法签名，增加 `historical_context: str = ""` 参数

- [ ] **Step 4: 修改 reports router 查询历史记录**

修改 `backend/app/routers/reports.py` 的 `create_report_from_upload` 函数：

```python
# 查询该猫的历史化验记录（最近 5 次）
from sqlalchemy import select
from app.models.models import HealthRecord, HealthIndicator

history_stmt = (
    select(HealthRecord)
    .filter(HealthRecord.cat_id == cat_id, HealthRecord.type == "lab_report")
    .order_by(HealthRecord.date.desc())
    .limit(5)
)
history_result = await db.execute(history_stmt)
history_records_db = history_result.scalars().all()

history_records = []
for rec in history_records_db:
    indicators_data = []
    for ind in rec.indicators:
        indicators_data.append({
            "name": ind.name,
            "display_name": ind.display_name,
            "value": ind.value,
            "unit": ind.unit,
            "is_abnormal": ind.is_abnormal
        })
    history_records.append({
        "date": rec.date.isoformat(),
        "summary": rec.ai_summary,
        "indicators": indicators_data
    })
```

- 将 `history_records` 传入 `orchestrator.process_report()`

- [ ] **Step 5: 添加测试**

创建 `backend/tests/test_history_agent.py`，测试：
- 无历史记录时的降级处理
- 有历史记录时的趋势分析
- LabAnalyzer 带历史上下文的分析

- [ ] **Step 6: 运行测试验证**

```bash
cd backend && python -m pytest tests/test_history_agent.py -v
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/ai/subagents/history_agent.py backend/app/ai/subagents/lab_analyzer.py backend/app/ai/orchestrator.py backend/app/routers/reports.py backend/tests/test_history_agent.py
git commit -m "feat: add HistoryAnalystAgent for cross-temporal reasoning"
```

---

## Phase 5B: Research Agent (RAG) + Actionable Agent

### Task 3: Research Agent — RAG 动态外脑

**Files:**
- Create: `backend/app/ai/subagents/research_agent.py`
- Modify: `backend/app/ai/orchestrator.py`

- [ ] **Step 1: 创建 ResearchAgent 类**

```python
# backend/app/ai/subagents/research_agent.py
import google.generativeai as genai
import json
from typing import Dict, Any, List
from app.ai.utils import clean_and_parse_json

RESEARCH_PROMPT = """你是一位兽医文献检索专家。当遇到疑难指标或知识库未覆盖的情况时，你需要基于已有医学常识提供补充信息。

【未覆盖的异常指标】
{unmatched_indicators}

【品种特异性上下文】
{breed_context}

任务：
1. 针对每个未匹配的异常指标，给出可能的临床意义。
2. 提供需要关注的并发症。
3. 给出建议的复查项目。

返回 JSON：
{
  "supplementary_findings": [
    {"indicator": "指标名", "finding": "临床意义", "follow_up": "建议复查项目"}
  ],
  "literature_notes": ["相关医学知识要点"]
}"""

class ResearchAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def research(
        self,
        unmatched_indicators: List[Dict[str, Any]],
        breed_context: str = ""
    ) -> Dict[str, Any]:
        """对知识库未覆盖的指标进行补充研究"""
        if not unmatched_indicators:
            return {"supplementary_findings": [], "literature_notes": []}

        prompt = RESEARCH_PROMPT.format(
            unmatched_indicators=json.dumps(unmatched_indicators, ensure_ascii=False, indent=2),
            breed_context=breed_context or "无特殊品种上下文"
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            result = clean_and_parse_json(text)
            if isinstance(result, dict):
                return result
            return {"supplementary_findings": [], "literature_notes": []}
        except Exception:
            return {"supplementary_findings": [], "literature_notes": []}
```

- [ ] **Step 2: 在 Orchestrator 中集成 ResearchAgent**

修改 `backend/app/ai/orchestrator.py`：

- 在 `__init__` 中初始化 `self.researcher = ResearchAgent(self.api_key)`
- 在 Lab 分析之后，检查是否有未匹配知识库的异常指标：

```python
# 3.5 Research 补充（知识库未覆盖的指标）
abnormal_indicators = [i for i in lab_result.get("indicators", []) if i.get("status") in ["high", "low"]]
# 简单判断：如果异常指标的 explanation 为空或很短，认为知识库未充分覆盖
unmatched = [i for i in abnormal_indicators if not i.get("explanation") or len(i.get("explanation", "")) < 10]
if unmatched:
    research_result = self.researcher.research(unmatched, breed_skill)
    # 将研究结果注入到对应指标的 explanation 中
    for finding in research_result.get("supplementary_findings", []):
        for ind in lab_result.get("indicators", []):
            if ind.get("name") == finding.get("indicator") and not ind.get("explanation"):
                ind["explanation"] = finding.get("finding", "")
```

- [ ] **Step 3: 添加测试**

创建 `backend/tests/test_research_agent.py`，测试：
- 无未匹配指标时的空返回
- 有未匹配指标时的补充研究
- 结果注入到对应指标

- [ ] **Step 4: Commit**

```bash
git add backend/app/ai/subagents/research_agent.py backend/app/ai/orchestrator.py backend/tests/test_research_agent.py
git commit -m "feat: add ResearchAgent for RAG dynamic knowledge supplementation"
```

---

### Task 4: Actionable Agent — 工具调用能力

**Files:**
- Create: `backend/app/ai/subagents/actionable_agent.py`
- Create: `backend/app/routers/actions.py`
- Modify: `backend/app/ai/orchestrator.py`
- Modify: `backend/main.py`

- [ ] **Step 1: 创建 ActionableAgent 类**

```python
# backend/app/ai/subagents/actionable_agent.py
import google.generativeai as genai
import json
from typing import Dict, Any, List
from app.ai.utils import clean_and_parse_json

ACTION_PROMPT = """你是一位将诊断转化为行动的兽医助手。根据化验结果，生成可执行的行动清单。

【病理摘要】
{summary}

【异常指标】
{abnormals}

【营养建议】
{recommendations}

【猫咪档案】
{cat_profile}

任务：
1. 生成复查提醒（指定多少天后需要复查哪些指标）。
2. 生成处方粮/补充剂购买清单（如果需要）。
3. 每个行动必须是具体的、可执行的。

返回 JSON：
{
  "reminders": [
    {"title": "复查肾功能", "description": "需复查 CREA、BUN、SDMA", "days_from_now": 30, "reminder_type": "vet_visit"}
  ],
  "shopping_list": [
    {"item": "肾脏处方粮", "reason": "CREA 偏高", "priority": "high"}
  ]
}"""

class ActionableAgent:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def generate_actions(
        self,
        summary: str,
        abnormals: List[Dict[str, Any]],
        recommendations: List[str],
        cat_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成可执行的行动清单"""
        prompt = ACTION_PROMPT.format(
            summary=summary,
            abnormals=json.dumps(abnormals, ensure_ascii=False, indent=2),
            recommendations=json.dumps(recommendations, ensure_ascii=False),
            cat_profile=json.dumps(cat_profile, ensure_ascii=False)
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            result = clean_and_parse_json(text)
            if isinstance(result, dict):
                return result
            return {"reminders": [], "shopping_list": []}
        except Exception:
            return {"reminders": [], "shopping_list": []}
```

- [ ] **Step 2: 创建 actions API 路由**

创建 `backend/app/routers/actions.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.models.models import Reminder, HealthRecord, HealthIndicator, Cat
from app.schemas.schemas import ReminderResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/execute/{report_id}")
async def execute_actions(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据分析结果自动生成提醒和购物清单"""
    # 获取报告数据
    result = await db.execute(
        select(HealthRecord)
        .filter(HealthRecord.id == report_id)
        .options(selectinload(HealthRecord.indicators))
    )
    record = result.scalars().first()
    if not record:
        raise HTTPException(404, "报告不存在")

    # 获取猫咪档案
    cat_result = await db.execute(select(Cat).filter(Cat.id == record.cat_id))
    cat = cat_result.scalars().first()

    cat_profile = {
        "name": cat.name if cat else "未知",
        "breed": cat.breed if cat else "未知"
    }

    # 调用 ActionableAgent
    from app.ai.subagents.actionable_agent import ActionableAgent
    from app.core.config import get_gemini_api_key

    api_key = get_gemini_api_key()
    if not api_key:
        raise HTTPException(400, "Gemini API Key 未设置")

    agent = ActionableAgent(api_key)
    abnormals = [
        {"name": i.name, "display_name": i.display_name, "value": i.value, "unit": i.unit}
        for i in record.indicators if i.is_abnormal
    ]

    actions = agent.generate_actions(
        summary=record.ai_summary or "",
        abnormals=abnormals,
        recommendations=record.actionable_advice or [],
        cat_profile=cat_profile
    )

    # 创建提醒
    created_reminders = []
    for r in actions.get("reminders", []):
        reminder = Reminder(
            id=str(uuid.uuid4()),
            cat_id=record.cat_id,
            title=r.get("title", "复查提醒"),
            description=r.get("description", ""),
            reminder_type=r.get("reminder_type", "vet_visit"),
            due_date=datetime.now() + timedelta(days=r.get("days_from_now", 30)),
            is_completed=False
        )
        db.add(reminder)
        created_reminders.append(reminder)

    await db.commit()

    return {
        "reminders_created": len(created_reminders),
        "shopping_list": actions.get("shopping_list", []),
        "reminders": [
            {"id": str(r.id), "title": r.title, "due_date": r.due_date.isoformat()}
            for r in created_reminders
        ]
    }
```

- [ ] **Step 3: 注册路由**

修改 `backend/main.py`，添加：
```python
from app.routers import actions
# ...
app.include_router(actions.router, prefix="/api/v1")
```

- [ ] **Step 4: 添加测试**

创建 `backend/tests/test_actionable_agent.py`，测试：
- ActionableAgent 生成提醒和购物清单
- API 端点 /actions/execute/{report_id}
- 无异常指标时的空返回

- [ ] **Step 5: 运行全量测试**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/ai/subagents/actionable_agent.py backend/app/routers/actions.py backend/main.py backend/tests/test_actionable_agent.py
git commit -m "feat: add ActionableAgent for tool-calling (reminders + shopping list)"
```

---

### Task 5: 前端集成 — 展示新功能

**Files:**
- Modify: `frontend/src/components/ReportCard.tsx`（或对应的报告详情组件）
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: API 客户端增加新接口**

修改 `frontend/src/lib/api.ts`，添加：

```typescript
// ========== 行动 API ==========

export const executeActions = (reportId: string) =>
  api.post(`/actions/execute/${reportId}`).then(r => r.data);
```

- [ ] **Step 2: 报告详情页增加「执行行动」按钮**

在报告详情组件中添加：
- 显示 Critic Agent 的 flags（如果有）
- 显示历史趋势数据（如果有）
- 「自动生成复查提醒」按钮（调用 executeActions）

- [ ] **Step 3: 前端构建验证**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/components/ReportCard.tsx
git commit -m "feat: frontend integration for Phase 5 agent capabilities"
```

---

### Task 6: 文档更新与最终验证

**Files:**
- Modify: `README.md`
- Modify: `TODO.md`

- [ ] **Step 1: 更新 README.md**

在核心特性中增加：
- Critic Agent 审查机制
- 历史趋势纵向分析
- RAG 动态知识补充
- 行动自动化（提醒 + 购物清单）

- [ ] **Step 2: 更新 TODO.md**

标记 Phase 5 所有任务为完成。

- [ ] **Step 3: 运行全量测试**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 4: 最终 Commit**

```bash
git add README.md TODO.md
git commit -m "docs: update README and TODO for Phase 5 completion"
```
