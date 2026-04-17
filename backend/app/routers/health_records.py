from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
def get_cat_health_records(
    cat_id: str,
    db: Session = Depends(get_db),
    record_type: str = None,
    limit: int = 50
):
    """获取猫咪健康记录"""
    query = db.query(HealthRecord).filter(
        HealthRecord.cat_id == cat_id,
        HealthRecord.deleted_at.is_(None)
    )
    if record_type:
        query = query.filter(HealthRecord.type == record_type)
    
    records = query.order_by(HealthRecord.date.desc()).limit(limit).all()
    return records

@router.get("/{record_id}", response_model=HealthRecordResponse)
def get_health_record(record_id: str, db: Session = Depends(get_db)):
    """获取单个健康记录详情"""
    record = db.query(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.deleted_at.is_(None)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Health record not found")
    return record

@router.post("/", response_model=HealthRecordResponse)
def create_health_record(
    record: HealthRecordCreate,
    db: Session = Depends(get_db)
):
    """创建健康记录"""
    db_record = HealthRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.put("/{record_id}", response_model=HealthRecordResponse)
def update_health_record(
    record_id: str,
    record: HealthRecordCreate,
    db: Session = Depends(get_db)
):
    """更新健康记录"""
    db_record = db.query(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.deleted_at.is_(None)
    ).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Health record not found")
    
    for key, value in record.dict().items():
        setattr(db_record, key, value)
    db_record.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_record)
    return db_record

@router.delete("/{record_id}")
def delete_health_record(record_id: str, db: Session = Depends(get_db)):
    """软删除健康记录"""
    db_record = db.query(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.deleted_at.is_(None)
    ).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Health record not found")
    
    db_record.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Health record deleted successfully"}

# Indicators endpoints
@router.get("/{record_id}/indicators", response_model=List[HealthIndicatorResponse])
def get_record_indicators(record_id: str, db: Session = Depends(get_db)):
    """获取记录的所有指标"""
    indicators = db.query(HealthIndicator).filter(
        HealthIndicator.record_id == record_id
    ).all()
    return indicators

@router.post("/{record_id}/indicators", response_model=HealthIndicatorResponse)
def create_indicator(
    record_id: str,
    indicator: HealthIndicatorCreate,
    db: Session = Depends(get_db)
):
    """添加健康指标"""
    db_indicator = HealthIndicator(record_id=record_id, **indicator.dict())
    db.add(db_indicator)
    db.commit()
    db.refresh(db_indicator)
    return db_indicator