"""症状咨询流水线 — 兽医院式分层诊疗状态机

基于 TriageAgent、SymptomCollectorAgent、DiagnosticReasonerAgent 三个纯规则引擎 Agent，
实现 INIT -> TRIAGING -> COLLECTING -> REASONING -> COMPLETED 的状态流转。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.triage_agent import TriageAgent
from app.agents.symptom_collector import SymptomCollectorAgent
from app.agents.diagnostic_reasoner import DiagnosticReasonerAgent
from app.crud.health import create_symptom_log, update_treatment_status
from app.models.models import HealthRecord


# ------------------------------------------------------------------
# 状态定义
# ------------------------------------------------------------------
class ConsultationStatus(str, Enum):
    INIT = "init"                    # 刚创建，尚未分诊
    TRIAGING = "triaging"            # 分诊中
    COLLECTING = "collecting"        # 引导问诊中（多轮对话）
    REASONING = "reasoning"          # 推理诊断中
    COMPLETED = "completed"          # 完成
    CANCELLED = "cancelled"        # 用户取消


# ------------------------------------------------------------------
# 诊疗流水线
# ------------------------------------------------------------------
class ConsultationPipeline:
    """症状咨询流水线 — 兽医院式分层诊疗状态机"""

    def __init__(self):
        self.triage_agent = TriageAgent()
        self.collector_agent = SymptomCollectorAgent()
        self.diagnostic_agent = DiagnosticReasonerAgent()
        # 内存 session 存储（当前阶段不需要 Redis/DB session 表）
        self._sessions: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    async def start(self, cat_id: str, initial_symptoms: str, db: AsyncSession) -> dict[str, Any]:
        """
        启动诊疗流程
        1. 创建 HealthRecord (consultation_type='symptom', treatment_status='pending')
        2. 创建 SymptomLog 记录初始症状
        3. 运行 TriageAgent 分诊
        4. 更新 HealthRecord 的 triage_level
        5. 如果 triage_level == 'emergency'，直接跳到 REASONING（加速）
        6. 否则进入 COLLECTING 阶段，运行 SymptomCollectorAgent Round 1
        7. 返回 session 状态
        """
        try:
            # 1. 创建 HealthRecord
            record = HealthRecord(
                cat_id=cat_id,
                date=datetime.now(),
                type="symptom",
                title="症状咨询",
                consultation_type="symptom",
                treatment_status="pending",
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)

            # 2. 创建初始 SymptomLog
            await create_symptom_log(
                db,
                cat_id,
                {
                    "record_id": record.id,
                    "symptom_description": initial_symptoms,
                    "severity": 3,  # 默认中等
                    "onset_time": datetime.now(),
                    "is_ongoing": True,
                },
            )

            # 3. 运行 TriageAgent
            triage_result = self.triage_agent.triage(initial_symptoms)

            # 4. 更新 HealthRecord 分诊级别
            record.triage_level = triage_result["triage_level"]
            await db.commit()

            # 5. 创建 session
            session_id = str(uuid.uuid4())
            session: dict[str, Any] = {
                "session_id": session_id,
                "cat_id": cat_id,
                "health_record_id": record.id,
                "status": ConsultationStatus.TRIAGING,
                "current_round": 0,
                "collected_info": {"initial_symptoms": initial_symptoms},
                "symptoms": self._extract_symptoms(initial_symptoms),
                "vital_signs": {},
                "triage_result": triage_result,
                "diagnosis_result": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            self._sessions[session_id] = session

            # 6. 如果是 emergency，直接跳到 REASONING
            if triage_result["triage_level"] == "emergency":
                session["status"] = ConsultationStatus.REASONING
                return await self._run_reasoning(session_id, db)

            # 7. 否则进入 COLLECTING Round 1
            session["status"] = ConsultationStatus.COLLECTING
            session["current_round"] = 1
            collect_result = self.collector_agent.collect(
                current_symptoms=session["symptoms"],
                round_num=1,
            )

            return {
                "session_id": session_id,
                "status": session["status"].value,
                "triage_level": triage_result["triage_level"],
                "triage_advice": triage_result["advice"],
                "questions": collect_result["questions"],
                "is_sufficient": collect_result["is_sufficient"],
                "next_action": collect_result["next_action"],
                "health_record_id": record.id,
            }

        except Exception as e:
            return {"error": f"Failed to start consultation: {str(e)}"}

    async def continue_step(
        self, session_id: str, user_input: dict[str, Any], db: AsyncSession
    ) -> dict[str, Any]:
        """
        继续诊疗流程（用户回答了上一轮问题后）
        - 根据当前状态决定下一步动作
        - COLLECTING 阶段：合并用户答案，判断是否需要下一轮追问
        - REASONING 阶段：运行 DiagnosticReasonerAgent，输出 Top 3 疾病
        - COMPLETED 阶段：返回最终报告
        """
        try:
            session = self._sessions.get(session_id)
            if not session:
                return {"error": "Session not found"}

            status = session["status"]

            if status == ConsultationStatus.COLLECTING:
                return await self._handle_collecting(session_id, user_input, db)

            if status == ConsultationStatus.REASONING:
                # 用户可能在补充体征数据
                if user_input.get("vitals"):
                    session["vital_signs"].update(user_input["vitals"])
                    # 重新运行诊断
                    return await self._run_reasoning(session_id, db)

                # 否则返回当前诊断结果
                return {
                    "session_id": session_id,
                    "status": session["status"].value,
                    "diagnosis": session["diagnosis_result"],
                }

            if status == ConsultationStatus.COMPLETED:
                return {
                    "session_id": session_id,
                    "status": session["status"].value,
                    "diagnosis": session["diagnosis_result"],
                    "triage_result": session["triage_result"],
                }

            return {"error": f"Invalid status: {status.value}"}

        except Exception as e:
            return {"error": f"Failed to continue step: {str(e)}"}

    async def get_status(self, session_id: str, db: AsyncSession) -> dict[str, Any]:
        """获取当前诊疗状态"""
        try:
            session = self._sessions.get(session_id)
            if not session:
                return {"error": "Session not found"}

            return {
                "session_id": session_id,
                "status": session["status"].value,
                "current_round": session.get("current_round", 0),
                "triage_result": session.get("triage_result"),
                "collected_summary": session.get("collected_info", {}),
            }

        except Exception as e:
            return {"error": f"Failed to get status: {str(e)}"}

    async def cancel(self, session_id: str, db: AsyncSession) -> dict[str, Any]:
        """取消/中断诊疗流程"""
        try:
            session = self._sessions.get(session_id)
            if not session:
                return {"error": "Session not found"}

            session["status"] = ConsultationStatus.CANCELLED
            session["updated_at"] = datetime.now()

            # 更新 HealthRecord 状态
            if session.get("health_record_id"):
                await update_treatment_status(
                    db,
                    session["health_record_id"],
                    "cancelled",
                )

            return {
                "session_id": session_id,
                "status": ConsultationStatus.CANCELLED.value,
            }

        except Exception as e:
            return {"error": f"Failed to cancel consultation: {str(e)}"}

    # ------------------------------------------------------------------
    # 内部处理
    # ------------------------------------------------------------------
    async def _handle_collecting(
        self, session_id: str, user_input: dict[str, Any], db: AsyncSession
    ) -> dict[str, Any]:
        """处理 COLLECTING 阶段的逻辑"""
        session = self._sessions[session_id]

        # 合并用户答案
        session["collected_info"].update(user_input)
        session["current_round"] += 1

        # 重新提取症状关键词
        all_text = " ".join(str(v) for v in session["collected_info"].values())
        session["symptoms"] = self._extract_symptoms(all_text)

        # 判断信息是否足够
        collector_result = self.collector_agent.collect(
            current_symptoms=session["symptoms"],
            known_info=session["collected_info"],
            round_num=session["current_round"],
        )

        if collector_result["is_sufficient"] or session["current_round"] >= 3:
            # 进入 REASONING
            session["status"] = ConsultationStatus.REASONING
            return await self._run_reasoning(session_id, db)

        # 继续追问
        return {
            "session_id": session_id,
            "status": session["status"].value,
            "current_round": session["current_round"],
            "questions": collector_result["questions"],
            "is_sufficient": collector_result["is_sufficient"],
            "next_action": collector_result["next_action"],
            "collected_summary": collector_result["collected_summary"],
        }

    async def _run_reasoning(self, session_id: str, db: AsyncSession) -> dict[str, Any]:
        """运行诊断推理并保存结果"""
        session = self._sessions[session_id]

        # 1. 运行 DiagnosticReasonerAgent
        diagnosis = self.diagnostic_agent.diagnose(
            symptoms=session["symptoms"],
            vital_signs=session.get("vital_signs"),
            history={"age_months": None, "breed": None},  # 简化，后续可扩展
        )

        # 2. 保存结果到 session
        session["diagnosis_result"] = diagnosis
        session["status"] = ConsultationStatus.COMPLETED
        session["updated_at"] = datetime.now()

        # 3. 更新 HealthRecord
        if session.get("health_record_id"):
            stmt = select(HealthRecord).where(HealthRecord.id == session["health_record_id"])
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()
            if record:
                record.treatment_status = "diagnosed"
                record.ai_summary = diagnosis.get("differential_diagnosis_note", "")
                # actionable_advice 存储 Top 3 疾病的建议
                top_diseases = diagnosis.get("possible_diseases", [])
                advice = [
                    f"{d['disease']}({d['probability']}): {', '.join(d['suggested_exams'])}"
                    for d in top_diseases
                ]
                record.actionable_advice = advice
                await db.commit()

        # 4. 返回
        return {
            "session_id": session_id,
            "status": session["status"].value,
            "triage_result": session["triage_result"],
            "diagnosis": diagnosis,
            "health_record_id": session.get("health_record_id"),
        }

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    def _extract_symptoms(self, text: str) -> list[str]:
        """从文本中提取症状关键词（简单关键词匹配）"""
        all_keywords = {
            "呕吐", "腹泻", "软便", "拒食", "食欲下降", "吐毛球",
            "打喷嚏", "咳嗽", "流鼻涕", "呼吸困难", "鼻塞",
            "尿频", "尿血", "排尿困难", "乱尿", "尿少",
            "掉毛", "抓挠", "红疹", "皮屑", "流泪", "耳垢",
            "行为问题", "踩奶", "躲藏", "攻击性", "过度舔毛", "叫唤",
            "精神萎靡", "发热", "脱水", "体重下降", "腹部疼痛",
            "便秘", "排便困难", "几天不排便",
            "多饮多尿", "亢奋", "黄疸",
            "抽搐", "流口水", "昏迷", "大出血", "带血",
            "窒息", "无法站立", "休克",
        }
        found = []
        for kw in all_keywords:
            if kw in text:
                found.append(kw)
        return found


# ------------------------------------------------------------------
# Self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio

    async def test():
        pipeline = ConsultationPipeline()
        print("ConsultationPipeline created OK")
        print("Status enum values:", [s.value for s in ConsultationStatus])
        # 测试症状提取
        symptoms = pipeline._extract_symptoms("我家猫呕吐、腹泻，精神萎靡，还有点发烧")
        print("Extracted symptoms:", symptoms)

    asyncio.run(test())
