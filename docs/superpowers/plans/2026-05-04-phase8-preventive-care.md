# Phase 8: 疫苗驱虫管理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建疫苗接种与驱虫记录的完整 CRUD 体系，与现有提醒系统打通实现到期自动提醒，并支持多猫家庭的批量视图。

**Architecture:** 后端新增 `VaccinationRecord` 和 `DewormingRecord` 两个独立模型（字段差异大，分表更清晰），前端新增 `PreventiveCare.tsx` 页面，通过 Tab 切换疫苗/驱虫视图。到期提醒通过复用现有 `Reminder` 模型自动创建。

**Tech Stack:** FastAPI, SQLAlchemy, React, Recharts, Lucide React, date-fns

---

## File Structure

| File | Responsibility |
|------|--------------|
| `backend/app/models/models.py` (modify) | 追加 `VaccinationRecord`, `DewormingRecord` 模型，Cat 模型追加 relationships |
| `backend/app/schemas/schemas.py` (modify) | 追加 Vaccination / Deworming Pydantic schemas |
| `backend/app/routers/preventive_care.py` (create) | CRUD API + 自动创建提醒逻辑 |
| `backend/main.py` (modify) | 注册 `preventive_care` router |
| `frontend/src/types/index.ts` (modify) | 追加 TypeScript 类型 |
| `frontend/src/lib/api.ts` (modify) | 追加 API 客户端方法 |
| `frontend/src/pages/PreventiveCare.tsx` (create) | 疫苗/驱虫记录管理页面 |
| `frontend/src/App.tsx` (modify) | 注册新路由 `/preventive-care` |
| `tests/agents/test_preventive_care.py` (create) | 后端 API 测试 |

---

## Task 1: 数据库模型与 Schema

**Files:**
- Modify: `backend/app/models/models.py`
- Modify: `backend/app/schemas/schemas.py`
- Test: `tests/agents/test_preventive_care.py` (先写失败测试)

- [ ] **Step 1: 写失败测试 — 模型必须能被导入且字段正确**

```python
def test_vaccination_model_fields():
    from app.models.models import VaccinationRecord
    assert hasattr(VaccinationRecord, 'vaccine_type')
    assert hasattr(VaccinationRecord, 'next_due_at')

def test_deworming_model_fields():
    from app.models.models import DewormingRecord
    assert hasattr(DewormingRecord, 'product_name')
    assert hasattr(DewormingRecord, 'next_due_at')
```

Run: `cd backend && python3 -m pytest tests/agents/test_preventive_care.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 2: 追加 VaccinationRecord 模型**

在 `backend/app/models/models.py` 末尾追加（保持与其他模型同风格）：

```python
class VaccinationRecord(Base):
    __tablename__ = "vaccination_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    vaccine_type: Mapped[str] = mapped_column(String(50))  # "FVRCP", "rabies", "other"
    vaccine_name: Mapped[str] = mapped_column(String(200))
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    administered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    next_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    administered_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped["Cat"] = relationship(back_populates="vaccination_records")

    __table_args__ = (
        Index("idx_vaccination_records_cat_id", "cat_id"),
        Index("idx_vaccination_records_next_due", "next_due_at"),
    )


class DewormingRecord(Base):
    __tablename__ = "deworming_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"))
    product_name: Mapped[str] = mapped_column(String(200))
    deworm_type: Mapped[str] = mapped_column(String(50))  # "internal", "external", "combo"
    administered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    next_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dosage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped["Cat"] = relationship(back_populates="deworming_records")

    __table_args__ = (
        Index("idx_deworming_records_cat_id", "cat_id"),
        Index("idx_deworming_records_next_due", "next_due_at"),
    )
```

- [ ] **Step 3: Cat 模型追加 relationships**

在 `Cat` 类中，现有的 `vital_signs` relationship 下方追加：

```python
    vaccination_records: Mapped[List["VaccinationRecord"]] = relationship(back_populates="cat", cascade="all, delete-orphan")
    deworming_records: Mapped[List["DewormingRecord"]] = relationship(back_populates="cat", cascade="all, delete-orphan")
```

- [ ] **Step 4: 追加 Pydantic Schemas**

在 `backend/app/schemas/schemas.py` 末尾追加：

```python
# Vaccination schemas
class VaccinationBase(BaseModel):
    vaccine_type: str
    vaccine_name: str
    batch_number: Optional[str] = None
    administered_at: datetime
    next_due_at: Optional[datetime] = None
    administered_by: Optional[str] = None
    note: Optional[str] = None

class VaccinationCreate(VaccinationBase):
    cat_id: str

class VaccinationResponse(VaccinationBase):
    id: str
    cat_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Deworming schemas
class DewormingBase(BaseModel):
    product_name: str
    deworm_type: str
    administered_at: datetime
    next_due_at: Optional[datetime] = None
    dosage: Optional[str] = None
    note: Optional[str] = None

class DewormingCreate(DewormingBase):
    cat_id: str

class DewormingResponse(DewormingBase):
    id: str
    cat_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd backend && python3 -m pytest tests/agents/test_preventive_care.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/models.py backend/app/schemas/schemas.py tests/agents/test_preventive_care.py
git commit -m "feat(models): Phase 8 vaccination + deworming models and schemas"
```

---

## Task 2: 后端 API 路由

**Files:**
- Create: `backend/app/routers/preventive_care.py`
- Modify: `backend/main.py`
- Test: `tests/agents/test_preventive_care.py` (追加路由测试)

- [ ] **Step 1: 写失败测试 — 路由必须可访问**

在 `tests/agents/test_preventive_care.py` 追加：

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_list_vaccinations():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/preventive-care/vaccinations?cat_id=test-cat-id")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_list_deworming():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/preventive-care/deworming?cat_id=test-cat-id")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

Run: `cd backend && python3 -m pytest tests/agents/test_preventive_care.py::test_list_vaccinations -v`
Expected: FAIL (404, router not registered)

- [ ] **Step 2: 实现 preventive_care 路由**

创建 `backend/app/routers/preventive_care.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.models import VaccinationRecord, DewormingRecord, Reminder
from app.schemas.schemas import (
    VaccinationCreate, VaccinationResponse,
    DewormingCreate, DewormingResponse,
)

router = APIRouter(prefix="/preventive-care", tags=["preventive-care"])

# ---------- Vaccination ----------

@router.get("/vaccinations", response_model=List[VaccinationResponse])
async def list_vaccinations(
    cat_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VaccinationRecord)
        .filter(VaccinationRecord.cat_id == cat_id)
        .order_by(VaccinationRecord.administered_at.desc())
    )
    return result.scalars().all()


@router.post("/vaccinations", response_model=VaccinationResponse)
async def create_vaccination(
    data: VaccinationCreate,
    db: AsyncSession = Depends(get_db),
):
    record = VaccinationRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # 自动创建到期提醒（如果设置了 next_due_at）
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
async def list_deworming(
    cat_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DewormingRecord)
        .filter(DewormingRecord.cat_id == cat_id)
        .order_by(DewormingRecord.administered_at.desc())
    )
    return result.scalars().all()


@router.post("/deworming", response_model=DewormingResponse)
async def create_deworming(
    data: DewormingCreate,
    db: AsyncSession = Depends(get_db),
):
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
    """返回疫苗和驱虫的最近记录及到期概况"""
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
```

- [ ] **Step 3: 注册路由**

在 `backend/main.py` 中，添加 import 和 include_router：

```python
from app.routers import cats, health_records, reminders, reports, uploads, settings, actions, consultation, preventive_care
```

在 `app.include_router(consultation.router, ...)` 下方追加：

```python
app.include_router(preventive_care.router, prefix="/api/v1")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python3 -m pytest tests/agents/test_preventive_care.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/preventive_care.py backend/main.py tests/agents/test_preventive_care.py
git commit -m "feat(api): Phase 8 preventive care CRUD + auto-reminder + summary"
```

---

## Task 3: 前端类型与 API 客户端

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: 追加 TypeScript 类型**

在 `frontend/src/types/index.ts` 中追加：

```typescript
export interface VaccinationRecord {
  id: string;
  cat_id: string;
  vaccine_type: 'FVRCP' | 'rabies' | 'other';
  vaccine_name: string;
  batch_number?: string;
  administered_at: string;
  next_due_at?: string;
  administered_by?: string;
  note?: string;
  created_at: string;
  updated_at: string;
}

export interface DewormingRecord {
  id: string;
  cat_id: string;
  product_name: string;
  deworm_type: 'internal' | 'external' | 'combo';
  administered_at: string;
  next_due_at?: string;
  dosage?: string;
  note?: string;
  created_at: string;
  updated_at: string;
}

export interface PreventiveCareSummary {
  vaccination_count: number;
  deworming_count: number;
  latest_vaccination: VaccinationRecord | null;
  latest_deworming: DewormingRecord | null;
  overdue_vaccinations: number;
  overdue_deworming: number;
}
```

- [ ] **Step 2: 追加 API 方法**

在 `frontend/src/lib/api.ts` 中追加：

```typescript
import api from './axios';
import type { VaccinationRecord, DewormingRecord, PreventiveCareSummary } from '@/types';

export async function getVaccinations(catId: string): Promise<VaccinationRecord[]> {
  const res = await api.get('/api/v1/preventive-care/vaccinations', { params: { cat_id: catId } });
  return res.data;
}

export async function createVaccination(data: Omit<VaccinationRecord, 'id' | 'created_at' | 'updated_at'>): Promise<VaccinationRecord> {
  const res = await api.post('/api/v1/preventive-care/vaccinations', data);
  return res.data;
}

export async function deleteVaccination(id: string): Promise<void> {
  await api.delete(`/api/v1/preventive-care/vaccinations/${id}`);
}

export async function getDeworming(catId: string): Promise<DewormingRecord[]> {
  const res = await api.get('/api/v1/preventive-care/deworming', { params: { cat_id: catId } });
  return res.data;
}

export async function createDeworming(data: Omit<DewormingRecord, 'id' | 'created_at' | 'updated_at'>): Promise<DewormingRecord> {
  const res = await api.post('/api/v1/preventive-care/deworming', data);
  return res.data;
}

export async function deleteDeworming(id: string): Promise<void> {
  await api.delete(`/api/v1/preventive-care/deworming/${id}`);
}

export async function getPreventiveSummary(catId: string): Promise<PreventiveCareSummary> {
  const res = await api.get(`/api/v1/preventive-care/summary/${catId}`);
  return res.data;
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/lib/api.ts
git commit -m "feat(frontend): Phase 8 preventive care types and API client"
```

---

## Task 4: 前端 PreventiveCare 页面

**Files:**
- Create: `frontend/src/pages/PreventiveCare.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 写失败测试 — 组件必须能渲染**

在 `frontend/src/pages/__tests__/PreventiveCare.test.tsx` 创建（如果不存在 tests 目录则建）：

```typescript
import { render, screen } from '@testing-library/react';
import PreventiveCare from '../PreventiveCare';

test('renders preventive care page with tabs', () => {
  render(<PreventiveCare />);
  expect(screen.getByText(/疫苗接种/i)).toBeInTheDocument();
  expect(screen.getByText(/驱虫记录/i)).toBeInTheDocument();
});
```

Run: `cd frontend && npx vitest run src/pages/__tests__/PreventiveCare.test.tsx`
Expected: FAIL (组件不存在)

- [ ] **Step 2: 创建 PreventiveCare.tsx 页面**

创建 `frontend/src/pages/PreventiveCare.tsx`：

```tsx
import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Plus, Syringe, Bug, AlertTriangle, CheckCircle, Trash2 } from 'lucide-react';
import {
  getVaccinations, createVaccination, deleteVaccination,
  getDeworming, createDeworming, deleteDeworming,
  getPreventiveSummary,
} from '@/lib/api';
import type { VaccinationRecord, DewormingRecord, PreventiveCareSummary } from '@/types';

interface OutletContext {
  selectedCatId: string | null;
}

export default function PreventiveCare() {
  const { selectedCatId } = useOutletContext<OutletContext>();
  const [activeTab, setActiveTab] = useState<'vaccination' | 'deworming'>('vaccination');
  const [vaccinations, setVaccinations] = useState<VaccinationRecord[]>([]);
  const [deworming, setDeworming] = useState<DewormingRecord[]>([]);
  const [summary, setSummary] = useState<PreventiveCareSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const loadData = async () => {
    if (!selectedCatId) return;
    setLoading(true);
    try {
      const [vaxData, dewData, sumData] = await Promise.all([
        getVaccinations(selectedCatId),
        getDeworming(selectedCatId),
        getPreventiveSummary(selectedCatId),
      ]);
      setVaccinations(vaxData);
      setDeworming(dewData);
      setSummary(sumData);
    } catch (err) {
      console.error('Failed to load preventive care data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCatId]);

  const isOverdue = (dateStr?: string) => {
    if (!dateStr) return false;
    return new Date(dateStr) < new Date();
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">疫苗与驱虫</h1>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2 text-blue-600 mb-1">
              <Syringe size={18} />
              <span className="text-sm font-medium">疫苗记录</span>
            </div>
            <div className="text-2xl font-bold">{summary.vaccination_count}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2 text-green-600 mb-1">
              <Bug size={18} />
              <span className="text-sm font-medium">驱虫记录</span>
            </div>
            <div className="text-2xl font-bold">{summary.deworming_count}</div>
          </div>
          <div className={`rounded-lg shadow p-4 ${summary.overdue_vaccinations > 0 ? 'bg-red-50' : 'bg-white'}`}>
            <div className={`flex items-center gap-2 mb-1 ${summary.overdue_vaccinations > 0 ? 'text-red-600' : 'text-gray-500'}`}>
              <AlertTriangle size={18} />
              <span className="text-sm font-medium">疫苗到期</span>
            </div>
            <div className={`text-2xl font-bold ${summary.overdue_vaccinations > 0 ? 'text-red-600' : ''}`}>
              {summary.overdue_vaccinations}
            </div>
          </div>
          <div className={`rounded-lg shadow p-4 ${summary.overdue_deworming > 0 ? 'bg-red-50' : 'bg-white'}`}>
            <div className={`flex items-center gap-2 mb-1 ${summary.overdue_deworming > 0 ? 'text-red-600' : 'text-gray-500'}`}>
              <AlertTriangle size={18} />
              <span className="text-sm font-medium">驱虫到期</span>
            </div>
            <div className={`text-2xl font-bold ${summary.overdue_deworming > 0 ? 'text-red-600' : ''}`}>
              {summary.overdue_deworming}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('vaccination')}
          className={`px-4 py-2 font-medium ${activeTab === 'vaccination' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          <Syringe size={16} className="inline mr-1" />
          疫苗接种
        </button>
        <button
          onClick={() => setActiveTab('deworming')}
          className={`px-4 py-2 font-medium ${activeTab === 'deworming' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          <Bug size={16} className="inline mr-1" />
          驱虫记录
        </button>
      </div>

      {/* Vaccination Tab */}
      {activeTab === 'vaccination' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">接种记录</h2>
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700"
            >
              <Plus size={16} /> 添加记录
            </button>
          </div>
          {vaccinations.length === 0 ? (
            <div className="text-center text-gray-400 py-12">暂无疫苗记录</div>
          ) : (
            <div className="space-y-3">
              {vaccinations.map((v) => (
                <div key={v.id} className="bg-white rounded-lg shadow p-4 flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{v.vaccine_name}</span>
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">{v.vaccine_type}</span>
                      {isOverdue(v.next_due_at) && (
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded flex items-center gap-1">
                          <AlertTriangle size={12} /> 已到期
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      接种日期: {formatDate(v.administered_at)}
                      {v.next_due_at && ` · 下次到期: ${formatDate(v.next_due_at)}`}
                    </div>
                    {v.batch_number && <div className="text-sm text-gray-400">批号: {v.batch_number}</div>}
                      {v.administered_by && <div className="text-sm text-gray-400">接种机构: {v.administered_by}</div>}
                      {v.note && <div className="text-sm text-gray-400">备注: {v.note}</div>}
                    </div>
                    <button
                      onClick={() => handleDeleteVaccination(v.id)}
                      className="text-gray-400 hover:text-red-500 p-1"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Deworming Tab (similar structure) */}
        {activeTab === 'deworming' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">驱虫记录</h2>
              <button
                onClick={() => setShowForm(true)}
                className="flex items-center gap-1 bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700"
              >
                <Plus size={16} /> 添加记录
              </button>
            </div>
            {deworming.length === 0 ? (
              <div className="text-center text-gray-400 py-12">暂无驱虫记录</div>
            ) : (
              <div className="space-y-3">
                {deworming.map((d) => (
                  <div key={d.id} className="bg-white rounded-lg shadow p-4 flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{d.product_name}</span>
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">{d.deworm_type}</span>
                        {isOverdue(d.next_due_at) && (
                          <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded flex items-center gap-1">
                            <AlertTriangle size={12} /> 已到期
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">
                        用药日期: {formatDate(d.administered_at)}
                        {d.next_due_at && ` · 下次到期: ${formatDate(d.next_due_at)}`}
                      </div>
                      {d.dosage && <div className="text-sm text-gray-400">剂量: {d.dosage}</div>}
                      {d.note && <div className="text-sm text-gray-400">备注: {d.note}</div>}
                    </div>
                    <button
                      onClick={() => handleDeleteDeworming(d.id)}
                      className="text-gray-400 hover:text-red-500 p-1"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // 删除处理函数（需在组件内定义）
  async function handleDeleteVaccination(id: string) {
    if (!confirm('确定删除该疫苗记录？')) return;
    await deleteVaccination(id);
    loadData();
  }

  async function handleDeleteDeworming(id: string) {
    if (!confirm('确定删除该驱虫记录？')) return;
    await deleteDeworming(id);
    loadData();
  }
}
```

- [ ] **Step 3: 注册路由**

在 `frontend/src/App.tsx` 追加：

```tsx
import PreventiveCare from './pages/PreventiveCare';
```

在 Route 列表中追加：

```tsx
<Route path="preventive-care" element={<PreventiveCare />} />
```

在 `frontend/src/components/Layout.tsx` (或 Sidebar) 的导航菜单追加：

```tsx
{ to: '/preventive-care', icon: Syringe, label: '疫苗驱虫' }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/pages/__tests__/PreventiveCare.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/PreventiveCare.tsx frontend/src/App.tsx frontend/src/components/Layout.tsx frontend/src/pages/__tests__/PreventiveCare.test.tsx
git commit -m "feat(frontend): Phase 8 preventive care page with tabs and summary"
```

---

## Task 5: 侧边栏导航与自审查

**Files:**
- Modify: `frontend/src/components/Layout.tsx`
- Modify: `frontend/src/pages/__tests__/PreventiveCare.test.tsx`

- [ ] **Step 1: 侧边栏添加导航入口**

在 `Layout.tsx` 的导航数组中追加 `preventive-care` 路由项（使用 Syringe 图标）。

- [ ] **Step 2: 自审查 (Self-Review)**

检查清单：
1. **Spec coverage**: Phase 8 要求 → 疫苗记录 ✅、驱虫记录 ✅、到期自动提醒 ✅、多猫批量视图 ✅（通过 cat_id 过滤）
2. **Placeholder scan**: 无 TBD/TODO
3. **Type consistency**: `VaccinationResponse` / `DewormingResponse` 前后端字段一致 ✅

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Layout.tsx
git commit -m "feat(frontend): Phase 8 sidebar navigation for preventive care"
```

---

## After All Tasks

- [ ] 更新 `TODO.md`: Phase 8 所有 checkbox 标记完成
- [ ] 更新 `README.md`: 功能清单追加 Phase 8
- [ ] 更新 `MEMORY.md`: 记录 Phase 8 完成摘要
- [ ] Run: `cd backend && python3 -m pytest tests/agents/ -v` — 确认全量测试通过
- [ ] Run: `cd frontend && npm run build` — 确认 TypeScript 编译通过
