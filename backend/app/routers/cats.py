from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.models import Cat, WeightLog, Reminder
from app.schemas.schemas import CatCreate, CatResponse, WeightLogCreate, WeightLogResponse, ReminderCreate, ReminderResponse

router = APIRouter(prefix="/cats", tags=["cats"])

@router.get("/", response_model=List[CatResponse])
def list_cats(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """获取所有猫咪列表"""
    cats = db.query(Cat).filter(Cat.deleted_at.is_(None)).offset(skip).limit(limit).all()
    return cats

@router.get("/{cat_id}", response_model=CatResponse)
def get_cat(cat_id: str, db: Session = Depends(get_db)):
    """获取单个猫咪详情"""
    cat = db.query(Cat).filter(Cat.id == cat_id, Cat.deleted_at.is_(None)).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    return cat

@router.post("/", response_model=CatResponse)
def create_cat(cat: CatCreate, db: Session = Depends(get_db)):
    """创建新猫咪"""
    db_cat = Cat(**cat.dict())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.put("/{cat_id}", response_model=CatResponse)
def update_cat(cat_id: str, cat: CatCreate, db: Session = Depends(get_db)):
    """更新猫咪信息"""
    db_cat = db.query(Cat).filter(Cat.id == cat_id, Cat.deleted_at.is_(None)).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    
    for key, value in cat.dict().items():
        setattr(db_cat, key, value)
    
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.delete("/{cat_id}")
def delete_cat(cat_id: str, db: Session = Depends(get_db)):
    """软删除猫咪"""
    db_cat = db.query(Cat).filter(Cat.id == cat_id, Cat.deleted_at.is_(None)).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    
    db_cat.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Cat deleted successfully"}

# Weight logs endpoints
@router.get("/{cat_id}/weights", response_model=List[WeightLogResponse])
def get_weight_logs(
    cat_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(30, ge=1, le=365)
):
    """获取猫咪体重历史"""
    weights = db.query(WeightLog).filter(
        WeightLog.cat_id == cat_id
    ).order_by(WeightLog.date.asc()).limit(limit).all()
    return weights

@router.post("/{cat_id}/weights", response_model=WeightLogResponse)
def create_weight_log(
    cat_id: str,
    weight: WeightLogCreate,
    db: Session = Depends(get_db)
):
    """记录猫咪体重"""
    db_weight = WeightLog(cat_id=cat_id, **weight.dict())
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight

# Reminders endpoints
@router.get("/{cat_id}/reminders", response_model=List[ReminderResponse])
def get_reminders(
    cat_id: str,
    db: Session = Depends(get_db),
    include_completed: bool = False
):
    """获取猫咪待办提醒"""
    query = db.query(Reminder).filter(Reminder.cat_id == cat_id)
    if not include_completed:
        query = query.filter(Reminder.is_completed == False)
    reminders = query.order_by(Reminder.due_date.asc()).all()
    return reminders

@router.post("/{cat_id}/reminders", response_model=ReminderResponse)
def create_reminder(
    cat_id: str,
    reminder: ReminderCreate,
    db: Session = Depends(get_db)
):
    """创建待办提醒"""
    db_reminder = Reminder(cat_id=cat_id, **reminder.dict())
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder