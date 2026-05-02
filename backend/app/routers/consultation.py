from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.consultation_pipeline import ConsultationPipeline
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
    ConsultationStartRequest,
    ConsultationContinueRequest,
    ConsultationResponse,
    ConsultationStatusResponse,
)

router = APIRouter(prefix="/consultation", tags=["consultation"])

# 全局 Pipeline 实例（单例）
pipeline = ConsultationPipeline()


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


@router.post("/start", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def start_consultation(
    data: ConsultationStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """启动症状咨询诊疗流程"""
    from app.crud.cat import get_cat
    
    cat = await get_cat(db, data.cat_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cat not found")
    
    result = await pipeline.start(
        cat_id=data.cat_id,
        initial_symptoms=data.initial_symptoms,
        db=db,
    )
    
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result


@router.post("/{session_id}/continue", response_model=ConsultationResponse)
async def continue_consultation(
    session_id: str,
    data: ConsultationContinueRequest,
    db: AsyncSession = Depends(get_db),
):
    """继续诊疗流程（回答追问）"""
    result = await pipeline.continue_step(
        session_id=session_id,
        user_input=data.user_input,
        db=db,
    )
    
    if "error" in result:
        if "Session not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result


@router.get("/{session_id}/status", response_model=ConsultationStatusResponse)
async def get_consultation_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取当前诊疗状态"""
    result = await pipeline.get_status(session_id=session_id, db=db)
    
    if "error" in result:
        if "Session not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result


@router.post("/{session_id}/cancel", response_model=ConsultationResponse)
async def cancel_consultation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """取消诊疗流程"""
    result = await pipeline.cancel(session_id=session_id, db=db)
    
    if "error" in result:
        if "Session not found" in result["error"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    
    return result
