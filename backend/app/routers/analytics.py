from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.models import WeightLog, HealthIndicator, HealthRecord, VitalSign
from app.schemas.schemas import VaccinationResponse, DewormingResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/weight-trend")
async def weight_trend(cat_id: str, days: int = 90, db: AsyncSession = Depends(get_db)):
    since = datetime.now() - timedelta(days=days)
    result = await db.execute(
        select(WeightLog)
        .filter(WeightLog.cat_id == cat_id)
        .filter(WeightLog.date >= since)
        .order_by(WeightLog.date.asc())
    )
    logs = result.scalars().all()
    return {
        "cat_id": cat_id,
        "days": days,
        "data": [{"date": log.date.strftime("%Y-%m-%d"), "weight": log.value} for log in logs],
        "count": len(logs),
    }

@router.get("/indicator-history")
async def indicator_history(cat_id: str, indicator_name: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HealthIndicator, HealthRecord.date)
        .join(HealthRecord, HealthIndicator.record_id == HealthRecord.id)
        .filter(HealthRecord.cat_id == cat_id)
        .filter(HealthIndicator.name == indicator_name)
        .order_by(HealthRecord.date.desc())
        .limit(limit)
    )
    rows = result.all()
    data = []
    for indicator, date in reversed(rows):
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": indicator.value,
            "unit": indicator.unit,
            "reference_min": indicator.reference_min,
            "reference_max": indicator.reference_max,
            "is_abnormal": indicator.is_abnormal,
        })
    return data

@router.get("/health-score-history")
async def health_score_history(cat_id: str, days: int = 180, db: AsyncSession = Depends(get_db)):
    since = datetime.now() - timedelta(days=days)
    result = await db.execute(
        select(VitalSign)
        .filter(VitalSign.cat_id == cat_id)
        .filter(VitalSign.measured_at >= since)
        .order_by(VitalSign.measured_at.asc())
    )
    vitals = result.scalars().all()
    
    records_result = await db.execute(
        select(HealthRecord)
        .filter(HealthRecord.cat_id == cat_id)
        .filter(HealthRecord.date >= since)
        .order_by(HealthRecord.date.asc())
    )
    records = records_result.scalars().all()
    
    from app.agents.health_score_engine import HealthScoreEngine
    engine = HealthScoreEngine()
    
    scores = []
    for vital in vitals:
        day_records = [
            {"treatment_status": r.treatment_status}
            for r in records if r.date.date() == vital.measured_at.date()
        ]
        score_result = engine.calculate(weight_kg=vital.weight_kg, records=day_records, symptom_logs=[])
        scores.append({
            "date": vital.measured_at.strftime("%Y-%m-%d"),
            "score": score_result["total_score"],
            "weight": vital.weight_kg,
        })
    
    return {"cat_id": cat_id, "days": days, "data": scores}

@router.get("/indicator-names")
async def list_indicator_names(cat_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HealthIndicator.name, HealthIndicator.display_name)
        .join(HealthRecord, HealthIndicator.record_id == HealthRecord.id)
        .filter(HealthRecord.cat_id == cat_id)
        .distinct()
    )
    rows = result.all()
    return [{"name": name, "display_name": display_name} for name, display_name in rows]
