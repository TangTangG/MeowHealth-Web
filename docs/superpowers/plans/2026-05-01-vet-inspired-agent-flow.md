# MeowHealth Web — 兽医院诊疗流程驱动的 Agent 架构演进计划

> **创建时间**: 2026-05-01  
> **灵感来源**: 真实动物医院的分层诊断流程  
> **核心理念**: 分层筛查、逐级升级、千猫千面

---

## 一、现状分析

### 已有架构（Phase 4.1）

```
用户上传化验单
    ↓
VisionAgent (OCR 提取)
    ↓
HistoryAnalystAgent (历史趋势)
    ↓
LabAnalyzer (病理分析)
    ↓
ResearchAgent (知识补充)
    ↓
DietitianAgent (营养建议)
    ↓
CriticAgent (主任审查)
    ↓
ActionableAgent (行动建议)
```

**问题**:
1. **单一流水线**：只能处理化验单上传场景，不支持日常症状咨询
2. **无分诊机制**：所有问题走同一条流水线，轻症和重症无区别
3. **无结构化问诊**：缺少引导式症状采集，依赖用户自由描述
4. **无持续追踪**：没有随访/监测机制，每次交互是孤立的
5. **数据模型局限**：HealthRecord 偏向事件记录，缺少时间序列分析能力

### 目标架构（对标兽医院）

```
┌──────────────────────────────────────────────────────────────┐
│                     MeowHealth Agent 系统                     │
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────────┐   │
│  │ TriageAgent  │──▶│SymptomCollector│──▶│DiagnosticReasoner│  │
│  │ (分诊台)     │   │ (问诊台)      │   │ (检验科+诊断)    │   │
│  └─────────────┘   └─────────────┘   └──────────────────┘   │
│         │                                      │              │
│         ▼                                      ▼              │
│  ┌─────────────┐                    ┌──────────────────┐     │
│  │ 紧急就医指引  │                    │ HealthAdvisorAgent│     │
│  │ (急诊通道)   │                    │ (主治医生)        │     │
│  └─────────────┘                    └──────────────────┘     │
│                                            │                 │
│                                            ▼                 │
│                                   ┌──────────────────┐      │
│                                   │ MonitoringAgent   │      │
│                                   │ (随访护士)        │      │
│                                   └──────────────────┘      │
│                                                              │
│  ── 已有 Agent（保留并适配）──                                  │
│  VisionAgent │ LabAnalyzer │ DietitianAgent │ CriticAgent    │
│  ResearchAgent │ HistoryAnalystAgent │ ActionableAgent       │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、Phase 计划

### Phase 6: 健康档案强化（数据层基础）

> 对标：医院的病历档案系统。没有好的病历，医生无法做准确诊断。

#### Task 6.1: 扩展 HealthRecord 模型

**目标**: 将 HealthRecord 从"事件记录"升级为"结构化病历"

```python
# 新增字段
class HealthRecord:
    # 已有: type, title, note, ai_summary, actionable_advice
    
    # 新增: 结构化分类
    record_category: str    # "lab_report" | "symptom" | "diagnosis" | "vaccination" | "checkup" | "medication"
    severity: Optional[str]  # "info" | "warning" | "critical"
    diagnosis: Optional[dict]  # {"primary": "...", "differentials": [...], "confidence": 0.85}
    symptoms: Optional[list]   # [{"name": "食欲下降", "severity": 3, "duration": "3天"}]
    medications: Optional[list] # [{"name": "阿莫西林", "dosage": "50mg", "frequency": "BID", "start": "...", "end": "..."}]
    follow_up_date: Optional[datetime]  # 复查日期
    vet_name: Optional[str]   # 就诊兽医
    hospital_name: Optional[str] # 就诊医院
```

**文件**: `backend/app/models/models.py`, `backend/app/schemas/schemas.py`  
**测试**: 模型迁移测试 + CRUD 测试

#### Task 6.2: 新增 SymptomLog 模型

**目标**: 轻量级症状日志，区别于完整的 HealthRecord

```python
class SymptomLog(Base):
    __tablename__ = "symptom_logs"
    
    id: str
    cat_id: str
    timestamp: datetime
    symptom_name: str        # "食欲下降" / "呕吐" / "精神萎靡"
    severity: int            # 1-5 量表
    duration: Optional[str]  # "3天" / "1周"
    context: Optional[str]   # "吃完罐头后" / "换季时"
    resolved: bool           # 是否已缓解
    resolved_at: Optional[datetime]
    linked_record_id: Optional[str]  # 关联的 HealthRecord（就诊后）
```

**价值**: 
- 用户可以随时记录轻微症状，不需要走完整就诊流程
- 积累的数据供 DiagnosticReasonerAgent 做趋势分析
- 类似医院的"预检分诊记录"

#### Task 6.3: 新增 VitalSign 模型

**目标**: 生命体征时间序列（体重已有，扩展到更多指标）

```python
class VitalSign(Base):
    __tablename__ = "vital_signs"
    
    id: str
    cat_id: str
    timestamp: datetime
    sign_type: str    # "weight" | "temperature" | "heart_rate" | "respiratory_rate" | "water_intake" | "food_intake"
    value: float
    unit: str
    note: Optional[str]
```

**价值**: 体重曲线已有，补充其他体征的时间序列，为趋势分析提供数据基础。

---

### Phase 7: 分诊与问诊 Agent（交互层核心）

> 对标：医院的挂号分诊台 + 医生问诊。

#### Task 7.1: TriageAgent（分诊 Agent）

**目标**: 用户输入症状 → 判断紧急程度 → 路由到合适流程

```
输入: "我的猫今天吐了三次，不吃东西"
      + 猫咪档案（品种、年龄、既往病史）
      
输出: {
  "urgency": "warning",           # info / warning / urgent / emergency
  "category": "消化系统",          
  "recommended_action": "问诊",    # 问诊 / 自查 / 立即就医
  "reasoning": "呕吐+厌食组合在幼猫中可能...",
  "red_flags": []                  # 触发的危险信号
}
```

**路由逻辑**:
| 紧急程度 | 路由 | 示例 |
|---------|------|------|
| `emergency` | 直接显示就医指引，不走 Agent 流水线 | 呼吸困难、大量出血、抽搐 |
| `urgent` | 快速问诊 → 建议就医 | 持续呕吐 24h+、完全拒食 |
| `warning` | 完整问诊流水线 | 偶尔呕吐、轻度腹泻 |
| `info` | 自查指引 + 记录 | 打喷嚏但精神好 |

**文件**: `backend/app/ai/subagents/triage_agent.py`  
**集成**: 作为新入口，替代用户直接上传化验单

#### Task 7.2: SymptomCollectorAgent（结构化问诊 Agent）

**目标**: 引导式问答，将模糊描述转为结构化数据

```
对话流程:
Agent: "猫咪食欲怎么样？"
  → [正常] [比平时少吃] [完全不吃] [只吃零食]

用户: "比平时少吃"

Agent: "持续多久了？"
  → [今天才开始] [2-3天了] [一周以上]

Agent: "还有其他症状吗？"（多选）
  → [呕吐] [腹泻] [精神不好] [喝水增多] [排尿异常] [无]

输出: {
  "symptoms": [
    {"name": "食欲下降", "severity": 2, "duration": "2-3天"},
    {"name": "喝水增多", "severity": 2, "duration": "不确定"}
  ],
  "structured_data": {
    "appetite": "decreased",
    "water_intake": "increased",
    "vomiting": false,
    "diarrhea": false,
    "lethargy": false
  },
  "suggested_checks": ["尿检", "生化（肾功能）"]
}
```

**前端交互**: 选项卡片式 UI，不是自由文本输入  
**文件**: `backend/app/ai/subagents/symptom_collector.py`

#### Task 7.3: DiagnosticReasonerAgent（诊断推理 Agent）

**目标**: 综合症状 + 历史档案 + 化验数据 → 输出诊断推理

```
输入:
  - 结构化症状（来自 SymptomCollectorAgent）
  - 猫咪档案（品种、年龄、体重、既往病史）
  - 历史 HealthRecords（既往诊断、检查数据）
  - 已上传的化验单数据（如有）

输出: {
  "working_diagnosis": [
    {"disease": "慢性肾病早期", "probability": 0.45, "evidence": ["多饮多尿", "食欲下降", "年龄>10岁"]},
    {"disease": "甲状腺功能亢进", "probability": 0.25, "evidence": ["食欲变化", "体重下降"]}
  ],
  "recommended_tests": [
    {"test": "血常规+生化", "reason": "确认肾功能指标", "priority": "high"},
    {"test": "甲状腺T4", "reason": "排除甲亢", "priority": "medium"}
  ],
  "confidence": 0.3,
  "needs_more_data": true
}
```

**关键设计**:
- 不做确定性诊断（AI 不是兽医），只做**推理辅助**
- 输出置信度，低于阈值时主动要求更多数据
- 集成品种特异性知识（千猫千面 Skills）

**文件**: `backend/app/ai/subagents/diagnostic_reasoner.py`

---

### Phase 8: 诊疗流水线编排（流程层整合）

> 对标：从挂号到出院的完整就诊流程。

#### Task 8.1: 诊疗模式路由

**目标**: 在 Orchestrator 层区分两种模式

```python
class MedicalOrchestrator:
    def process(self, mode: str, **kwargs):
        """
        mode:
          - "report_analysis": 化验单分析（已有流程）
          - "symptom_consult": 症状咨询（新流程）
          - "follow_up": 随访（新流程）
        """
        if mode == "report_analysis":
            return self._report_pipeline(**kwargs)      # 已有
        elif mode == "symptom_consult":
            return self._consult_pipeline(**kwargs)     # 新增
        elif mode == "follow_up":
            return self._follow_up_pipeline(**kwargs)   # 新增
```

#### Task 8.2: 症状咨询流水线

```
用户描述症状
    ↓
TriageAgent (判断紧急程度)
    ↓ (非紧急)
SymptomCollectorAgent (引导问诊)
    ↓
DiagnosticReasonerAgent (推理诊断)
    ↓
┌─────────────────────────────────┐
│ 置信度 >= 0.6?                   │
│  是 → HealthAdvisorAgent (建议)  │
│  否 → 引导用户上传化验单/就医     │
└─────────────────────────────────┘
    ↓
ActionableAgent (后续行动)
```

#### Task 8.3: HealthAdvisorAgent（健康建议 Agent）

**目标**: 综合诊断结果，给出可执行的建议

```
输出: {
  "summary": "根据症状分析，疑似...",
  "immediate_actions": [
    "增加饮水量",
    "观察排尿情况"
  ],
  "diet_advice": {...},      # 复用 DietitianAgent
  "when_to_see_vet": "如果 48 小时内症状未改善",
  "monitoring_plan": {
    "track": ["饮水量", "排尿频率", "食欲"],
    "frequency": "每天记录",
    "duration": "3天"
  }
}
```

#### Task 8.4: MonitoringAgent（随访 Agent）

**目标**: 定期追踪症状变化，提醒用户记录

```
触发方式: Cron Job（每天一次）
逻辑:
  1. 查找所有未解决的 SymptomLog
  2. 查找有 follow_up_date 的 HealthRecord
  3. 向用户发送温和的提醒:
     "🐱 豆豆的食欲有好转吗？"
     → [好多了] [还是老样子] [更差了]
  4. 记录回复，更新 SymptomLog
  5. 如果恶化，触发 TriageAgent 重新评估
```

**文件**: `backend/app/ai/subagents/monitoring_agent.py`  
**集成**: OpenClaw Cron 或 Heartbeat

---

### Phase 9: 前端交互重构（体验层）

> 对标：医院的导诊台 + 诊室交互。

#### Task 9.1: 首页诊疗入口

```
Dashboard 页面新增两个入口:
┌──────────────────────────────────┐
│  🏥 我感觉猫咪不太对             │  → 症状咨询流程
│  📋 上传化验单分析                │  → 化验单分析流程（已有）
│  📊 查看健康档案                 │  → 健康档案总览
└──────────────────────────────────┘
```

#### Task 9.2: 问诊对话界面

**设计要点**:
- 选项卡片式交互（不是自由聊天）
- 进度条显示问诊进度（1/5 → 2/5 → ...）
- 实时显示 Agent 思考状态（"正在分析症状..."）
- 结果页展示诊断推理过程（可折叠）

#### Task 9.3: 健康档案总览页

```
猫咪健康档案
├── 📊 基础信息（品种、年龄、体重曲线）
├── 🏥 就诊记录（时间轴）
├── 💊 用药记录
├── 💉 疫苗/驱虫
├── 📝 症状日志
├── 🔬 检查数据（化验单指标趋势图）
└── 📈 健康评分（综合评估）
```

#### Task 9.4: 随访提醒界面

- 卡片式提醒："豆豆的食欲下降已经第 3 天了，有好转吗？"
- 快速记录按钮（好/一般/差）
- 趋势可视化（症状严重度时间曲线）

---

### Phase 10: 知识库与千猫千面深化

> 对标：医院的专科门诊 + 会诊制度。

#### Task 10.1: 疾病知识树

```
skills/
├── diseases/
│   ├── ckd.md           # 慢性肾病
│   ├── hyperthyroid.md  # 甲亢
│   ├── diabetes.md      # 糖尿病
│   ├── uti.md           # 尿路感染
│   └── ...
├── breeds/              # 已有
├── weights/             # 已有
└── symptoms/
    ├── vomiting.md      # 呕吐鉴别诊断
    ├── diarrhea.md      # 腹泻鉴别诊断
    ├── polyuria.md      # 多饮多尿
    └── ...
```

#### Task 10.2: 症状-疾病关联引擎

```python
class SymptomDiseaseMapper:
    """症状组合 → 可能疾病映射"""
    
    def map(self, symptoms: list, breed: str, age: int) -> list:
        """
        输入: ["多饮多尿", "食欲下降", "体重减轻"]
        输出: [
            {"disease": "慢性肾病", "match_score": 0.8, "age_factor": "high"},
            {"disease": "糖尿病", "match_score": 0.5, "age_factor": "medium"},
        ]
        """
```

#### Task 10.3: 健康评分系统

```python
class HealthScoreEngine:
    """综合健康评分（0-100）"""
    
    factors:
        - 体重趋势（稳定+正常范围 → 高分）
        - 最近化验指标（正常 → 高分）
        - 症状频率（少 → 高分）
        - 疫苗/驱虫时效（在有效期内 → 高分）
        - 年龄修正（老年猫标准放宽）
```

---

## 三、任务优先级总览

| Phase | 主题 | 优先级 | 依赖 | 预估工作量 |
|-------|------|--------|------|-----------|
| **6** | 健康档案强化 | **P0** | 无 | 3-4 Tasks |
| **7** | 分诊与问诊 Agent | **P1** | Phase 6 | 3 Tasks |
| **8** | 诊疗流水线编排 | **P1** | Phase 7 | 4 Tasks |
| **9** | 前端交互重构 | **P2** | Phase 8 | 4 Tasks |
| **10** | 知识库深化 | **P2** | Phase 7 | 3 Tasks |

**建议执行顺序**: Phase 6 → 7 → 8 → (9 & 10 并行)

---

## 四、技术决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 问诊交互方式 | 选项卡片式 | 比自由文本数据质量高，比纯表单体验好 |
| 诊断置信度阈值 | 0.6 | 低于此值不给出诊断建议，引导就医 |
| 随访触发方式 | Cron Job | 定时独立执行，不依赖用户在线 |
| 症状存储 | 独立 SymptomLog 表 | 轻量级记录，不污染 HealthRecord |
| 知识库格式 | Markdown Skills | 复用已有架构，易于维护和扩展 |

---

## 五、与 Trading Orchestrator 的架构复用

MeowHealth 和 Trading Orchestrator 共享以下架构模式：

| 模式 | Trading | MeowHealth |
|------|---------|------------|
| 多 Agent 编排 | Orchestrator + 8 角色 | MedicalOrchestrator + 7 Agent |
| 动态技能加载 | prompts/ | skills/ (Markdown) |
| 分层决策 | Triage → Analysis → Action | Triage → Diagnosis → Treatment |
| 时间序列分析 | 价格/指标数据 | 体重/体征/症状数据 |

可复用的组件思路：
- **EventBus 模式**: Agent 间事件驱动通信
- **动态权重**: 根据数据质量调整 Agent 权重
- **Health Check**: Agent 健康状态监控
