from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.models import VaccinationRecord, DewormingRecord, Reminder
from app.schemas.schemas import VaccinationCreate, VaccinationResponse, DewormingCreate, DewormingResponse

router = APIRouter(prefix="/preventive-care", tags=["preventive-care"])

# ---------- Vaccination ----------
@router.get("/vaccinations", response_model=List[VaccinationResponse])
async def list_vaccinations(cat_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VaccinationRecord)
        .filter(VaccinationRecord.cat_id == cat_id)
        .order_by(VaccinationRecord.administered_at.desc())
    )
    return result.scalars().all()

@router.post("/vaccinations", response_model=VaccinationResponse)
async def create_vaccination(data: VaccinationCreate, db: AsyncSession = Depends(get_db)):
    record = VaccinationRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    if record.next_due_at:
        reminder = Reminder(
            cat_id=record.cat_id,
            title=f"疫苗到期提醒: {record.vaccine_name}",
            description=f"{record.vaccine_type} 疫苗将于 {record.next_due_at.strftime('%Y-%m-%d')} 到期",
            reminder_type="vaccination",
            due_date=record.next_due_at,
        )
        db.add(reminder)
        await db.commit()
    return record

@router.delete("/vaccinations/{record_id}")
async def delete_vaccination(record_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VaccinationRecord).filter(VaccinationRecord.id == record_id))
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    await db.delete(record)
    await db.commit()
    return {"message": "Vaccination record deleted"}

# ---------- Deworming ----------
@router.get("/deworming", response_model=List[DewormingResponse])
async def list_deworming(cat_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DewormingRecord)
        .filter(DewormingRecord.cat_id == cat_id)
        .order_by(DewormingRecord.administered_at.desc())
    )
    return result.scalars().all()

@router.post("/deworming", response_model=DewormingResponse)
async def create_deworming(data: DewormingCreate, db: AsyncSession = Depends(get_db)):
    record = DewormingRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    if record.next_due_at:
        reminder = Reminder(
            cat_id=record.cat_id,
            title=f"驱虫到期提醒: {record.product_name}",
            description=f"{record.deworm_type} 驱虫将于 {record.next_due_at.strftime('%Y-%m-%d')} 到期",
            reminder_type="deworming",
            due_date=record.next_due_at,
        )
        db.add(reminder)
        await db.commit()
    return record

@router.delete("/deworming/{record_id}")
async def delete_deworming(record_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DewormingRecord).filter(DewormingRecord.id == record_id))
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    await db.delete(record)
    await db.commit()
    return {"message": "Deworming record deleted"}

# ---------- Dashboard summary ----------
@router.get("/summary/{cat_id}")
async def get_summary(cat_id: str, db: AsyncSession = Depends(get_db)):
    vaccinations = await db.execute(
        select(VaccinationRecord)
        .filter(VaccinationRecord.cat_id == cat_id)
        .order_by(VaccinationRecord.administered_at.desc())
    )
    deworming = await db.execute(
        select(DewormingRecord)
        .filter(DewormingRecord.cat_id == cat_id)
        .order_by(DewormingRecord.administered_at.desc())
    )
    vax_list = vaccinations.scalars().all()
    dew_list = deworming.scalars().all()
    now = datetime.now()
    overdue_vax = [v for v in vax_list if v.next_due_at and v.next_due_at < now]
    overdue_dew = [d for d in dew_list if d.next_due_at and d.next_due_at < now]
    return {
        "vaccination_count": len(vax_list),
        "deworming_count": len(dew_list),
        "latest_vaccination": VaccinationResponse.model_validate(vax_list[0]).model_dump() if vax_list else None,
        "latest_deworming": DewormingResponse.model_validate(dew_list[0]).model_dump() if dew_list else None,
        "overdue_vaccinations": len(overdue_vax),
        "overdue_deworming": len(overdue_dew),
    }
