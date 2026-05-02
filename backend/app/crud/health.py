from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import SymptomLog, VitalSign, HealthRecord


async def create_symptom_log(db: AsyncSession, cat_id: str, data: dict) -> SymptomLog:
    db_obj = SymptomLog(cat_id=cat_id, **data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def create_vital_sign(db: AsyncSession, cat_id: str, data: dict) -> VitalSign:
    db_obj = VitalSign(cat_id=cat_id, **data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_symptom_logs_by_cat(db: AsyncSession, cat_id: str, limit: int = 50):
    stmt = (
        select(SymptomLog)
        .where(SymptomLog.cat_id == cat_id)
        .order_by(SymptomLog.onset_time.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_vital_signs_by_cat(db: AsyncSession, cat_id: str, limit: int = 50):
    stmt = (
        select(VitalSign)
        .where(VitalSign.cat_id == cat_id)
        .order_by(VitalSign.measured_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_health_record_with_details(db: AsyncSession, record_id: str):
    stmt = (
        select(HealthRecord)
        .where(HealthRecord.id == record_id)
        .options(
            selectinload(HealthRecord.symptom_logs),
            selectinload(HealthRecord.vital_signs),
            selectinload(HealthRecord.indicators),
            selectinload(HealthRecord.attachments),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_treatment_status(
    db: AsyncSession,
    record_id: str,
    status: str,
    next_followup_at: Optional[datetime] = None,
) -> Optional[HealthRecord]:
    stmt = select(HealthRecord).where(HealthRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        return None

    record.treatment_status = status
    if next_followup_at is not None:
        record.next_followup_at = next_followup_at

    await db.commit()
    await db.refresh(record)
    return record
