"""随访提醒 Agent — 跟踪治疗中的猫咪，按随访时间生成提醒。"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import HealthRecord, Cat
from app.crud.health import get_health_record_with_details, update_treatment_status
from app.agents.triage_agent import TriageAgent


class MonitoringAgent:
    """随访提醒 Agent — 跟踪治疗中的猫咪，按随访时间生成提醒"""

    def __init__(self):
        self.triage_agent = TriageAgent()

    async def check_followups(self, db: AsyncSession) -> list[dict]:
        """
        检查所有需要随访的 HealthRecord
        返回: [{"record_id": str, "cat_id": str, "cat_name": str,
                "followup_type": str, "due_date": datetime,
                "overdue_days": int, "status": str, ...}]
        """
        now = datetime.now()
        tomorrow = now + timedelta(days=1)

        # 查询所有需要随访的记录
        stmt = (
            select(HealthRecord, Cat)
            .join(Cat, HealthRecord.cat_id == Cat.id)
            .where(
                and_(
                    HealthRecord.treatment_status.in_(["diagnosed", "treating"]),
                    HealthRecord.next_followup_at.isnot(None),
                )
            )
            .order_by(HealthRecord.next_followup_at.asc())
        )

        result = await db.execute(stmt)
        records = result.all()

        followups = []
        for record, cat in records:
            due_date = record.next_followup_at
            overdue_days = (now - due_date).days if now > due_date else 0

            # 分类随访状态
            if now > due_date + timedelta(days=1):
                status = "overdue"  # 已过期
            elif now > due_date:
                status = "due_today"  # 今天到期
            elif due_date <= tomorrow:
                status = "due_soon"  # 即将到期（24h内）
            else:
                status = "scheduled"  # 计划中

            followups.append({
                "record_id": record.id,
                "cat_id": cat.id,
                "cat_name": cat.name,
                "due_date": due_date.isoformat() if due_date else None,
                "overdue_days": overdue_days,
                "status": status,
                "treatment_status": record.treatment_status,
                "triage_level": record.triage_level,
                "consultation_type": record.consultation_type,
                "last_summary": record.ai_summary,
            })

        return followups

    async def create_followup_reminder(self, record_id: str, db: AsyncSession) -> dict:
        """
        为指定 HealthRecord 创建随访提醒
        """
        record = await get_health_record_with_details(db, record_id)
        if not record:
            return {"error": "Record not found"}

        cat = record.cat
        cat_name = cat.name if cat else "猫咪"
        due_date = record.next_followup_at

        if not due_date:
            return {"error": "No follow-up scheduled for this record"}

        now = datetime.now()
        overdue_days = (now - due_date).days if now > due_date else 0

        if now > due_date + timedelta(days=1):
            status = "overdue"
        elif now > due_date:
            status = "due_today"
        elif due_date <= now + timedelta(days=1):
            status = "due_soon"
        else:
            status = "scheduled"

        return {
            "record_id": record.id,
            "cat_id": cat.id if cat else None,
            "cat_name": cat_name,
            "due_date": due_date.isoformat(),
            "status": status,
            "overdue_days": overdue_days,
            "treatment_status": record.treatment_status,
            "triage_level": record.triage_level,
            "consultation_type": record.consultation_type,
            "message": f"{cat_name} 的随访提醒：请在 {due_date.strftime('%Y-%m-%d %H:%M')} 前完成随访。",
            "disclaimer": "仅供参考，不构成医疗建议",
        }

    async def process_feedback(
        self, record_id: str, feedback: dict, db: AsyncSession
    ) -> dict:
        """
        处理随访反馈
        输入: feedback = {
            "symptom_change": "improved" | "unchanged" | "worsened",
            "notes": str,
            "new_symptoms": list[str]
        }
        返回: 更新后的 HealthRecord 状态
        """
        # 1. 获取当前记录
        record = await get_health_record_with_details(db, record_id)
        if not record:
            return {"error": "Record not found"}

        symptom_change = feedback.get("symptom_change", "unchanged")
        new_symptoms = feedback.get("new_symptoms", [])
        notes = feedback.get("notes", "")

        # 2. 根据反馈决定下一步
        if symptom_change == "worsened":
            # 症状恶化：升级关注，可能需要重新分诊
            new_status = record.treatment_status or "diagnosed"

            # 如果有新症状，重新运行 TriageAgent
            if new_symptoms:
                all_symptoms_text = " ".join(new_symptoms)
                triage_result = self.triage_agent.triage(all_symptoms_text)

                # 如果分诊等级升级，更新记录
                if triage_result["triage_level"] in ("emergency", "urgent"):
                    record.triage_level = triage_result["triage_level"]
                    await db.commit()

                    next_followup = datetime.now() + timedelta(hours=6)
                    await update_treatment_status(
                        db, record_id, new_status, next_followup
                    )

                    return {
                        "record_id": record_id,
                        "action": "escalated",
                        "new_triage_level": triage_result["triage_level"],
                        "message": (
                            f"症状恶化，分诊等级升级为 {triage_result['triage_level']}！"
                            f"{triage_result['advice']}"
                        ),
                        "next_followup_at": next_followup.isoformat(),
                        "requires_immediate_attention": True,
                        "disclaimer": "仅供参考，不构成医疗建议",
                    }

            # 症状恶化但未达到 emergency/urgent
            next_followup = datetime.now() + timedelta(days=1)
            await update_treatment_status(db, record_id, new_status, next_followup)

            return {
                "record_id": record_id,
                "action": "monitor_closely",
                "message": "症状未改善，请密切观察，建议24小时内再次反馈或就医。",
                "next_followup_at": next_followup.isoformat(),
                "requires_immediate_attention": False,
                "disclaimer": "仅供参考，不构成医疗建议",
            }

        elif symptom_change == "improved":
            # 症状改善：延长随访间隔
            next_followup = datetime.now() + timedelta(days=3)
            await update_treatment_status(
                db, record_id, record.treatment_status or "diagnosed", next_followup
            )

            # 如果连续2次改善，可以标记为即将 resolved
            return {
                "record_id": record_id,
                "action": "continue_monitoring",
                "message": "症状有所改善，继续保持观察，3天后再次随访。",
                "next_followup_at": next_followup.isoformat(),
                "suggest_resolve": False,
                "disclaimer": "仅供参考，不构成医疗建议",
            }

        else:  # unchanged
            # 无变化：保持当前随访计划
            next_followup = datetime.now() + timedelta(days=2)
            await update_treatment_status(
                db, record_id, record.treatment_status or "diagnosed", next_followup
            )

            return {
                "record_id": record_id,
                "action": "continue_monitoring",
                "message": "症状无明显变化，请继续观察，2天后再次随访。",
                "next_followup_at": next_followup.isoformat(),
                "disclaimer": "仅供参考，不构成医疗建议",
            }

    async def auto_check_and_escalate(self, db: AsyncSession) -> dict:
        """
        自动检查：
        1. 找出所有治疗中的记录
        2. 检查是否有过期未随访的
        3. 如果有用户反馈症状恶化，升级分诊等级
        4. 返回需要处理的提醒列表
        """
        followups = await self.check_followups(db)

        alerts = []
        for f in followups:
            if f["status"] == "overdue" and f["overdue_days"] >= 3:
                # 过期3天以上，发送紧急提醒
                alerts.append({
                    "type": "overdue_alert",
                    "record_id": f["record_id"],
                    "cat_name": f["cat_name"],
                    "message": (
                        f"{f['cat_name']} 的随访已过期 {f['overdue_days']} 天，"
                        "请尽快确认猫咪状况！"
                    ),
                    "priority": "high",
                })
            elif f["status"] == "due_today":
                alerts.append({
                    "type": "due_reminder",
                    "record_id": f["record_id"],
                    "cat_name": f["cat_name"],
                    "message": f"{f['cat_name']} 的随访今天到期，请检查症状变化。",
                    "priority": "medium",
                })
            elif f["status"] == "due_soon":
                alerts.append({
                    "type": "upcoming_reminder",
                    "record_id": f["record_id"],
                    "cat_name": f["cat_name"],
                    "message": f"{f['cat_name']} 的随访将在24小时内到期。",
                    "priority": "low",
                })

        return {
            "checked_at": datetime.now().isoformat(),
            "total_monitoring": len(followups),
            "urgent_alerts": len([a for a in alerts if a["priority"] == "high"]),
            "alerts": alerts,
            "disclaimer": "仅供参考，不构成医疗建议",
        }


if __name__ == "__main__":
    import asyncio

    async def test():
        agent = MonitoringAgent()
        print("MonitoringAgent created OK")

        # 测试 TriageAgent 集成
        triage_result = agent.triage_agent.triage("呕吐带血")
        print(f"Triage integration OK: {triage_result['triage_level']}")

    asyncio.run(test())
