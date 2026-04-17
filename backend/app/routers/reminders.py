from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.models import Reminder
from app.schemas.schemas import ReminderCreate, ReminderResponse

router = APIRouter(prefix="/reminders", tags=["reminders"])

@router.get("/", response_model=List[ReminderResponse])
def list_reminders(
    db: Session = Depends(get_db),
    cat_id: str = None,
    include_completed: bool = False
):
    """获取所有待办提醒"""
    query = db.query(Reminder)
    if cat_id:
        query = query.filter(Reminder.cat_id == cat_id)
    if not include_completed:
        query = query.filter(Reminder.is_completed == False)
    
    reminders = query.order_by(Reminder.due_date.asc()).all()
    return reminders

@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(reminder_id: str, db: Session = Depends(get_db)):
    """获取单个提醒详情"""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder

@router.post("/", response_model=ReminderResponse)
def create_reminder(reminder: ReminderCreate, db: Session = Depends(get_db)):
    """创建待办提醒"""
    db_reminder = Reminder(**reminder.dict())
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: str,
    reminder: ReminderCreate,
    db: Session = Depends(get_db)
):
    """更新提醒"""
    db_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    for key, value in reminder.dict().items():
        setattr(db_reminder, key, value)
    db_reminder.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

@router.post("/{reminder_id}/complete")
def complete_reminder(reminder_id: str, db: Session = Depends(get_db)):
    """标记提醒为已完成"""
    db_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    db_reminder.is_completed = True
    db_reminder.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Reminder marked as completed"}

@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: str, db: Session = Depends(get_db)):
    """删除提醒"""
    db_reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    db.delete(db_reminder)
    db.commit()
    return {"message": "Reminder deleted successfully"}