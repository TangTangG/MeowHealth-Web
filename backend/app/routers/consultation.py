from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.models.models import Cat, HealthRecord
from app.crud.cat import get_cat
from app.crud.health import (
    create_symptom_log,
    create_vital_sign,
    get_health_record_with_details,
    update_treatment_status,
)
from app.schemas.health import (
    SymptomLogCreate,
    SymptomLogResponse,
    VitalSignCreate,
    VitalSignResponse,
    HealthRecordWithDetails,
    TreatmentStatusUpdate,
)

router = APIRouter(prefix="/consultation", tags=["consultation"])


@router.post("/cats/{cat_id}/symptoms", response_model=SymptomLogResponse, status_code=status.HTTP_201_CREATED)
async def record_symptom(
    cat_id: str,
    data: SymptomLogCreate,
    db: AsyncSession = Depends(get_db),
):
    cat = await get_cat(db, cat_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found")

    payload = data.model_dump()
    payload["cat_id"] = cat_id
    # record_id may be omitted if not provided
    db_obj = await create_symptom_log(db, cat_id=cat_id, data=payload)
    return db_obj


@router.post("/cats/{cat_id}/vitals", response_model=VitalSignResponse, status_code=status.HTTP_201_CREATED)
async def record_vital_sign(
    cat_id: str,
    data: VitalSignCreate,
    db: AsyncSession = Depends(get_db),
):
    cat = await get_cat(db, cat_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found")

    payload = data.model_dump()
    payload["cat_id"] = cat_id
    db_obj = await create_vital_sign(db, cat_id=cat_id, data=payload)
    return db_obj


@router.get("/cats/{cat_id}/health-records", response_model=List[HealthRecordWithDetails])
async def get_cat_health_records(
    cat_id: str,
    db: AsyncSession = Depends(get_db),
):
    cat = await get_cat(db, cat_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found")

    stmt = (
        select(HealthRecord)
        .where(
            HealthRecord.cat_id == cat_id,
            HealthRecord.deleted_at.is_(None),
        )
        .options(
            selectinload(HealthRecord.symptom_logs),
            selectinload(HealthRecord.vital_signs),
            selectinload(HealthRecord.indicators),
            selectinload(HealthRecord.attachments),
        )
        .order_by(HealthRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return records


@router.put("/health-records/{record_id}/status", response_model=HealthRecordWithDetails)
async def update_record_status(
    record_id: str,
    data: TreatmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    updated = await update_treatment_status(
        db,
        record_id=record_id,
        status=data.treatment_status,
        next_followup_at=data.next_followup_at,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record not found")

    record = await get_health_record_with_details(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record not found")
    return record
