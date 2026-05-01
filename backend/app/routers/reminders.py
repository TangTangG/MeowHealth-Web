from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.models import Reminder
from app.schemas.schemas import ReminderCreate, ReminderResponse

router = APIRouter(prefix="/reminders", tags=["reminders"])

@router.get("/", response_model=List[ReminderResponse])
async def list_reminders(
    db: AsyncSession = Depends(get_db),
    cat_id: str = None,
    include_completed: bool = False
):
    """获取所有待办提醒"""
    stmt = select(Reminder)
    if cat_id:
        stmt = stmt.filter(Reminder.cat_id == cat_id)
    if not include_completed:
        stmt = stmt.filter(Reminder.is_completed == False)
    
    result = await db.execute(stmt.order_by(Reminder.due_date.asc()))
    reminders = result.scalars().all()
    return reminders

@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(reminder_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个提醒详情"""
    result = await db.execute(select(Reminder).filter(Reminder.id == reminder_id))
    reminder = result.scalars().first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder

@router.post("/", response_model=ReminderResponse)
async def create_reminder(reminder: ReminderCreate, db: AsyncSession = Depends(get_db)):
    """创建待办提醒"""
    db_reminder = Reminder(**reminder.dict())
    db.add(db_reminder)
    await db.commit()
    await db.refresh(db_reminder)
    return db_reminder

@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: str,
    reminder: ReminderCreate,
    db: AsyncSession = Depends(get_db)
):
    """更新提醒"""
    result = await db.execute(select(Reminder).filter(Reminder.id == reminder_id))
    db_reminder = result.scalars().first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    for key, value in reminder.dict().items():
        setattr(db_reminder, key, value)
    db_reminder.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(db_reminder)
    return db_reminder

@router.post("/{reminder_id}/complete")
async def complete_reminder(reminder_id: str, db: AsyncSession = Depends(get_db)):
    """标记提醒为已完成"""
    result = await db.execute(select(Reminder).filter(Reminder.id == reminder_id))
    db_reminder = result.scalars().first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    db_reminder.is_completed = True
    db_reminder.completed_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Reminder marked as completed"}

@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: str, db: AsyncSession = Depends(get_db)):
    """删除提醒"""
    result = await db.execute(select(Reminder).filter(Reminder.id == reminder_id))
    db_reminder = result.scalars().first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    await db.delete(db_reminder)
    await db.commit()
    return {"message": "Reminder deleted successfully"}
