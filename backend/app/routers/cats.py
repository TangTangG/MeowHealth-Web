from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.models import Cat, WeightLog, Reminder
from app.schemas.schemas import CatCreate, CatResponse, WeightLogCreate, WeightLogResponse, ReminderCreate, ReminderResponse

router = APIRouter(prefix="/cats", tags=["cats"])

@router.get("/", response_model=List[CatResponse])
async def list_cats(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """获取所有猫咪列表"""
    result = await db.execute(select(Cat).filter(Cat.deleted_at.is_(None)).offset(skip).limit(limit))
    cats = result.scalars().all()
    return cats

@router.get("/{cat_id}", response_model=CatResponse)
async def get_cat(cat_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个猫咪详情"""
    result = await db.execute(select(Cat).filter(Cat.id == cat_id, Cat.deleted_at.is_(None)))
    cat = result.scalars().first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    return cat

@router.post("/", response_model=CatResponse)
async def create_cat(cat: CatCreate, db: AsyncSession = Depends(get_db)):
    """创建新猫咪"""
    db_cat = Cat(**cat.model_dump())
    db.add(db_cat)
    await db.commit()
    await db.refresh(db_cat)
    return db_cat

@router.put("/{cat_id}", response_model=CatResponse)
async def update_cat(cat_id: str, cat: CatCreate, db: AsyncSession = Depends(get_db)):
    """更新猫咪信息"""
    result = await db.execute(select(Cat).filter(Cat.id == cat_id, Cat.deleted_at.is_(None)))
    db_cat = result.scalars().first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    
    for key, value in cat.model_dump().items():
        setattr(db_cat, key, value)
    
    await db.commit()
    await db.refresh(db_cat)
    return db_cat

@router.delete("/{cat_id}")
async def delete_cat(cat_id: str, db: AsyncSession = Depends(get_db)):
    """软删除猫咪"""
    result = await db.execute(select(Cat).filter(Cat.id == cat_id, Cat.deleted_at.is_(None)))
    db_cat = result.scalars().first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    
    db_cat.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "Cat deleted successfully"}

# Weight logs endpoints
@router.get("/{cat_id}/weights", response_model=List[WeightLogResponse])
async def get_weight_logs(
    cat_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(30, ge=1, le=365)
):
    """获取猫咪体重历史"""
    result = await db.execute(
        select(WeightLog).filter(WeightLog.cat_id == cat_id).order_by(WeightLog.date.asc()).limit(limit)
    )
    weights = result.scalars().all()
    return weights

@router.post("/{cat_id}/weights", response_model=WeightLogResponse)
async def create_weight_log(
    cat_id: str,
    weight: WeightLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """记录猫咪体重"""
    db_weight = WeightLog(cat_id=cat_id, **weight.dict())
    db.add(db_weight)
    await db.commit()
    await db.refresh(db_weight)
    return db_weight

# Reminders endpoints
@router.get("/{cat_id}/reminders", response_model=List[ReminderResponse])
async def get_reminders(
    cat_id: str,
    db: AsyncSession = Depends(get_db),
    include_completed: bool = False
):
    """获取猫咪待办提醒"""
    stmt = select(Reminder).filter(Reminder.cat_id == cat_id)
    if not include_completed:
        stmt = stmt.filter(Reminder.is_completed == False)
    result = await db.execute(stmt.order_by(Reminder.due_date.asc()))
    reminders = result.scalars().all()
    return reminders

@router.post("/{cat_id}/reminders", response_model=ReminderResponse)
async def create_reminder(
    cat_id: str,
    reminder: ReminderCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建待办提醒"""
    db_reminder = Reminder(cat_id=cat_id, **reminder.dict())
    db.add(db_reminder)
    await db.commit()
    await db.refresh(db_reminder)
    return db_reminder
