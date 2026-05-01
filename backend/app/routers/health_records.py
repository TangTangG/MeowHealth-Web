from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.models import HealthRecord, HealthIndicator, ReportAttachment
from app.schemas.schemas import (
    HealthRecordCreate, HealthRecordResponse,
    HealthIndicatorCreate, HealthIndicatorResponse
)

router = APIRouter(prefix="/health-records", tags=["health-records"])

@router.get("/cat/{cat_id}", response_model=List[HealthRecordResponse])
async def get_cat_health_records(
    cat_id: str,
    db: AsyncSession = Depends(get_db),
    record_type: str = None,
    limit: int = 50
):
    """获取猫咪健康记录"""
    stmt = select(HealthRecord).filter(
        HealthRecord.cat_id == cat_id,
        HealthRecord.deleted_at.is_(None)
    )
    if record_type:
        stmt = stmt.filter(HealthRecord.type == record_type)
    
    result = await db.execute(stmt.order_by(HealthRecord.date.desc()).limit(limit))
    records = result.scalars().all()
    return records

@router.get("/{record_id}", response_model=HealthRecordResponse)
async def get_health_record(record_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个健康记录详情"""
    result = await db.execute(select(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.deleted_at.is_(None)
    ))
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    return record

@router.post("/", response_model=HealthRecordResponse)
async def create_health_record(
    record: HealthRecordCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建健康记录"""
    db_record = HealthRecord(**record.dict())
    db.add(db_record)
    await db.commit()
    await db.refresh(db_record)
    return db_record

@router.put("/{record_id}", response_model=HealthRecordResponse)
async def update_health_record(
    record_id: str,
    record: HealthRecordCreate,
    db: AsyncSession = Depends(get_db)
):
    """更新健康记录"""
    result = await db.execute(select(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.deleted_at.is_(None)
    ))
    db_record = result.scalars().first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Health record not found")
    
    for key, value in record.dict().items():
        setattr(db_record, key, value)
    db_record.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_record)
    return db_record

@router.delete("/{record_id}")
async def delete_health_record(record_id: str, db: AsyncSession = Depends(get_db)):
    """软删除健康记录"""
    result = await db.execute(select(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.deleted_at.is_(None)
    ))
    db_record = result.scalars().first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Health record not found")
    
    db_record.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "Health record deleted successfully"}

# Indicators endpoints
@router.get("/{record_id}/indicators", response_model=List[HealthIndicatorResponse])
async def get_record_indicators(record_id: str, db: AsyncSession = Depends(get_db)):
    """获取记录的所有指标"""
    result = await db.execute(select(HealthIndicator).filter(
        HealthIndicator.record_id == record_id
    ))
    indicators = result.scalars().all()
    return indicators

@router.post("/{record_id}/indicators", response_model=HealthIndicatorResponse)
async def create_indicator(
    record_id: str,
    indicator: HealthIndicatorCreate,
    db: AsyncSession = Depends(get_db)
):
    """添加健康指标"""
    db_indicator = HealthIndicator(record_id=record_id, **indicator.dict())
    db.add(db_indicator)
    await db.commit()
    await db.refresh(db_indicator)
    return db_indicator
