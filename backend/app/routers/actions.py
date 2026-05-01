from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.models.models import Reminder, HealthRecord, HealthIndicator, Cat

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/execute/{report_id}")
async def execute_actions(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据分析结果自动生成提醒和购物清单"""
    result = await db.execute(
        select(HealthRecord)
        .filter(HealthRecord.id == report_id)
        .options(selectinload(HealthRecord.indicators))
    )
    record = result.scalars().first()
    if not record:
        raise HTTPException(404, "报告不存在")

    cat_result = await db.execute(select(Cat).filter(Cat.id == record.cat_id))
    cat = cat_result.scalars().first()

    cat_profile = {
        "name": cat.name if cat else "未知",
        "breed": cat.breed if cat else "未知"
    }

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
