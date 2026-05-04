# Phase 9: 健康数据可视化增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对现有健康数据进行深度可视化挖掘，新增化验指标历史对比、健康评分趋势、PDF 报告导出，并扩展 Dashboard 数据洞察能力。

**Architecture:** 后端新增聚合 API（指标历史、评分趋势），前端新增 `Analytics.tsx` 数据洞察页面，Dashboard 增强化验指标迷你图，报告页面增加 PDF 导出按钮。PDF 导出采用前端 `html2canvas + jsPDF` 方案，避免后端依赖膨胀。

**Tech Stack:** FastAPI, SQLAlchemy, React, Recharts, Lucide React, jsPDF, html2canvas

---

## File Structure

| File | Responsibility |
|------|--------------|
| `backend/app/routers/analytics.py` (create) | 聚合数据 API：体重趋势、指标历史、评分趋势 |
| `backend/app/agents/health_score_engine.py` (modify) | 追加批量评分计算接口 |
| `backend/main.py` (modify) | 注册 `analytics` router |
| `frontend/src/lib/api.ts` (modify) | 追加 analytics API 方法 |
| `frontend/src/types/index.ts` (modify) | 追加 analytics 类型 |
| `frontend/src/pages/Analytics.tsx` (create) | 数据洞察中心页面 |
| `frontend/src/components/IndicatorChart.tsx` (create) | 化验指标历史对比折线图 |
| `frontend/src/components/HealthScoreChart.tsx` (create) | 健康评分趋势图 |
| `frontend/src/components/PDFExportButton.tsx` (create) | PDF 导出按钮组件 |
| `frontend/src/pages/Dashboard.tsx` (modify) | 新增化验指标概览卡片 |
| `frontend/src/App.tsx` (modify) | 注册 `/analytics` 路由 |
| `frontend/package.json` (modify) | 安装 jsPDF + html2canvas |
| `tests/agents/test_analytics.py` (create) | 后端聚合 API 测试 |

---

## Task 1: 后端聚合 Analytics API

**Files:**
- Create: `backend/app/routers/analytics.py`
- Modify: `backend/main.py`
- Modify: `backend/app/agents/health_score_engine.py`
- Test: `tests/agents/test_analytics.py`

- [ ] **Step 1: 写失败测试**

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_weight_trend_api():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/weight-trend?cat_id=test")
    assert response.status_code == 200
    assert "data" in response.json()

@pytest.mark.asyncio
async def test_indicator_history_api():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/indicator-history?cat_id=test&indicator_name=WBC")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

Run: `cd backend && python3 -m pytest tests/agents/test_analytics.py -v`
Expected: FAIL (router not registered)

- [ ] **Step 2: 实现 analytics 路由**

创建 `backend/app/routers/analytics.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.models import WeightLog, HealthIndicator, HealthRecord, VitalSign

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/weight-trend")
async def weight_trend(
    cat_id: str,
    days: int = 90,
    db: AsyncSession = Depends(get_db),
):
    """返回最近 N 天的体重趋势数据"""
    since = datetime.now() - timedelta(days=days)
    result = await db.execute(
        select(WeightLog)
        .filter(WeightLog.cat_id == cat_id)
        .filter(WeightLog.date >= since)
        .order_by(WeightLog.date.asc())
    )
    logs = result.scalars().all()
    return {
        "cat_id": cat_id,
        "days": days,
        "data": [
            {"date": log.date.strftime("%Y-%m-%d"), "weight": log.value}
            for log in logs
        ],
        "count": len(logs),
    }


@router.get("/indicator-history")
async def indicator_history(
    cat_id: str,
    indicator_name: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """返回指定化验指标的历史变化"""
    result = await db.execute(
        select(HealthIndicator, HealthRecord.date)
        .join(HealthRecord, HealthIndicator.record_id == HealthRecord.id)
        .filter(HealthRecord.cat_id == cat_id)
        .filter(HealthIndicator.name == indicator_name)
        .order_by(HealthRecord.date.desc())
        .limit(limit)
    )
    rows = result.all()
    data = []
    for indicator, date in reversed(rows):  # 从早到晚
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": indicator.value,
            "unit": indicator.unit,
            "reference_min": indicator.reference_min,
            "reference_max": indicator.reference_max,
            "is_abnormal": indicator.is_abnormal,
        })
    return data


@router.get("/health-score-history")
async def health_score_history(
    cat_id: str,
    days: int = 180,
    db: AsyncSession = Depends(get_db),
):
    """返回基于 vital_signs 和 health_records 的历史评分趋势（按天计算）"""
    # 简化：基于 vital_signs 记录的时间点计算评分
    since = datetime.now() - timedelta(days=days)
    result = await db.execute(
        select(VitalSign)
        .filter(VitalSign.cat_id == cat_id)
        .filter(VitalSign.measured_at >= since)
        .order_by(VitalSign.measured_at.asc())
    )
    vitals = result.scalars().all()

    # 同时获取该时间段内的 health_records 用于计算指标正常率
    records_result = await db.execute(
        select(HealthRecord)
        .filter(HealthRecord.cat_id == cat_id)
        .filter(HealthRecord.date >= since)
        .order_by(HealthRecord.date.asc())
    )
    records = records_result.scalars().all()

    # 按天聚合评分
    from app.agents.health_score_engine import HealthScoreEngine
    engine = HealthScoreEngine()

    scores = []
    for vital in vitals:
        # 找到 vital 当天的 health_records
        day_records = [r for r in records if r.date.date() == vital.measured_at.date()]
        score = engine.calculate(
            weight=vital.weight_kg,
            records=day_records,
            symptoms=[],
        )
        scores.append({
            "date": vital.measured_at.strftime("%Y-%m-%d"),
            "score": score,
            "weight": vital.weight_kg,
        })

    return {
        "cat_id": cat_id,
        "days": days,
        "data": scores,
    }


@router.get("/indicator-names")
async def list_indicator_names(
    cat_id: str,
    db: AsyncSession = Depends(get_db),
):
    """返回该猫咪所有出现过的化验指标名称列表"""
    result = await db.execute(
        select(HealthIndicator.name, HealthIndicator.display_name)
        .join(HealthRecord, HealthIndicator.record_id == HealthRecord.id)
        .filter(HealthRecord.cat_id == cat_id)
        .distinct()
    )
    rows = result.all()
    return [
        {"name": name, "display_name": display_name}
        for name, display_name in rows
    ]
```

- [ ] **Step 3: 注册路由**

在 `backend/main.py` 中追加：

```python
from app.routers import cats, health_records, reminders, reports, uploads, settings, actions, consultation, preventive_care, analytics
```

在 preventive_care router 下方追加：

```python
app.include_router(analytics.router, prefix="/api/v1")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python3 -m pytest tests/agents/test_analytics.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/analytics.py backend/main.py tests/agents/test_analytics.py
git commit -m "feat(api): Phase 9 analytics aggregation APIs"
```

---

## Task 2: 前端依赖安装与类型定义

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: 安装 jsPDF 和 html2canvas**

```bash
cd frontend && npm install jspdf html2canvas
```

- [ ] **Step 2: 追加 TypeScript 类型**

在 `frontend/src/types/index.ts` 追加：

```typescript
export interface WeightTrendData {
  date: string;
  weight: number;
}

export interface WeightTrendResponse {
  cat_id: string;
  days: number;
  data: WeightTrendData[];
  count: number;
}

export interface IndicatorHistoryPoint {
  date: string;
  value: number | null;
  unit: string;
  reference_min: number | null;
  reference_max: number | null;
  is_abnormal: boolean;
}

export interface HealthScorePoint {
  date: string;
  score: number;
  weight: number;
}

export interface HealthScoreHistoryResponse {
  cat_id: string;
  days: number;
  data: HealthScorePoint[];
}

export interface IndicatorNameItem {
  name: string;
  display_name: string;
}
```

- [ ] **Step 3: 追加 API 方法**

在 `frontend/src/lib/api.ts` 追加：

```typescript
import type {
  WeightTrendResponse,
  IndicatorHistoryPoint,
  HealthScoreHistoryResponse,
  IndicatorNameItem,
} from '@/types';

export async function getWeightTrend(catId: string, days = 90): Promise<WeightTrendResponse> {
  const res = await api.get('/api/v1/analytics/weight-trend', { params: { cat_id: catId, days } });
  return res.data;
}

export async function getIndicatorHistory(
  catId: string,
  indicatorName: string,
  limit = 20
): Promise<IndicatorHistoryPoint[]> {
  const res = await api.get('/api/v1/analytics/indicator-history', {
    params: { cat_id: catId, indicator_name: indicatorName, limit },
  });
  return res.data;
}

export async function getHealthScoreHistory(catId: string, days = 180): Promise<HealthScoreHistoryResponse> {
  const res = await api.get('/api/v1/analytics/health-score-history', { params: { cat_id: catId, days } });
  return res.data;
}

export async function getIndicatorNames(catId: string): Promise<IndicatorNameItem[]> {
  const res = await api.get('/api/v1/analytics/indicator-names', { params: { cat_id: catId } });
  return res.data;
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/types/index.ts frontend/src/lib/api.ts
git commit -m "feat(frontend): Phase 9 analytics types, API client, install jsPDF/html2canvas"
```

---

## Task 3: Dashboard 增强 — 化验指标概览卡片

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/components/DashboardIndicatorCard.tsx`

- [ ] **Step 1: 创建 DashboardIndicatorCard 组件**

创建 `frontend/src/components/DashboardIndicatorCard.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { Activity, TrendingUp, TrendingDown } from 'lucide-react';
import { getIndicatorNames, getIndicatorHistory } from '@/lib/api';

interface Props {
  catId: string;
}

export default function DashboardIndicatorCard({ catId }: Props) {
  const [latestIndicators, setLatestIndicators] = useState<Array<{
    name: string;
    display_name: string;
    value: number | null;
    unit: string;
    is_abnormal: boolean;
    trend: 'up' | 'down' | 'stable';
  }>>([]);

  useEffect(() => {
    if (!catId) return;
    const load = async () => {
      try {
        const names = await getIndicatorNames(catId);
        const indicators = await Promise.all(
          names.slice(0, 4).map(async (n) => {
            const history = await getIndicatorHistory(catId, n.name, 2);
            if (history.length === 0) return null;
            const latest = history[history.length - 1];
            const prev = history.length > 1 ? history[history.length - 2] : null;
            const trend = prev && latest.value && prev.value
              ? latest.value > prev.value ? 'up' : latest.value < prev.value ? 'down' : 'stable'
              : 'stable';
            return {
              name: n.name,
              display_name: n.display_name,
              value: latest.value,
              unit: latest.unit,
              is_abnormal: latest.is_abnormal,
              trend,
            };
          })
        );
        setLatestIndicators(indicators.filter(Boolean) as any);
      } catch (e) {
        console.error('Failed to load indicator card:', e);
      }
    };
    load();
  }, [catId]);

  if (latestIndicators.length === 0) return null;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center gap-2 text-purple-600 mb-3">
        <Activity size={18} />
        <h3 className="font-semibold text-sm">近期化验指标</h3>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {latestIndicators.map((ind) => (
          <div key={ind.name} className={`p-2 rounded ${ind.is_abnormal ? 'bg-red-50' : 'bg-gray-50'}`}>
            <div className="text-xs text-gray-500">{ind.display_name}</div>
            <div className={`text-lg font-bold ${ind.is_abnormal ? 'text-red-600' : 'text-gray-800'}`}>
              {ind.value !== null ? `${ind.value} ${ind.unit}` : '—'}
            </div>
            {ind.trend === 'up' && <TrendingUp size={14} className="text-red-500 inline" />}
            {ind.trend === 'down' && <TrendingDown size={14} className="text-green-500 inline" />}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 在 Dashboard 中引入**

在 `frontend/src/pages/Dashboard.tsx` 的导入区域追加：

```tsx
import DashboardIndicatorCard from '@/components/DashboardIndicatorCard';
```

在 WeightChart 下方（或合适位置）插入：

```tsx
<DashboardIndicatorCard catId={selectedCatId} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DashboardIndicatorCard.tsx frontend/src/pages/Dashboard.tsx
git commit -m "feat(frontend): Phase 9 Dashboard indicator overview card"
```

---

## Task 4: 数据洞察中心 Analytics 页面

**Files:**
- Create: `frontend/src/pages/Analytics.tsx`
- Create: `frontend/src/components/IndicatorChart.tsx`
- Create: `frontend/src/components/HealthScoreChart.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 IndicatorChart 组件**

创建 `frontend/src/components/IndicatorChart.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea } from 'recharts';
import { getIndicatorHistory } from '@/lib/api';
import type { IndicatorHistoryPoint } from '@/types';

interface Props {
  catId: string;
  indicatorName: string;
  displayName: string;
}

export default function IndicatorChart({ catId, indicatorName, displayName }: Props) {
  const [data, setData] = useState<IndicatorHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!catId || !indicatorName) return;
    setLoading(true);
    getIndicatorHistory(catId, indicatorName, 30)
      .then(setData)
      .finally(() => setLoading(false));
  }, [catId, indicatorName]);

  if (loading) return <div className="h-64 flex items-center justify-center text-gray-400">加载中...</div>;
  if (data.length === 0) return <div className="h-64 flex items-center justify-center text-gray-400">暂无数据</div>;

  const minRef = data[0]?.reference_min;
  const maxRef = data[0]?.reference_max;

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          {minRef !== null && maxRef !== null && (
            <ReferenceArea y1={minRef} y2={maxRef} stroke="transparent" fill="#22c55e" fillOpacity={0.05} />
          )}
          <Line type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
      <div className="text-center text-sm text-gray-500 mt-1">{displayName}</div>
    </div>
  );
}
```

- [ ] **Step 2: 创建 HealthScoreChart 组件**

创建 `frontend/src/components/HealthScoreChart.tsx`：

```tsx
import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { getHealthScoreHistory } from '@/lib/api';
import type { HealthScorePoint } from '@/types';

interface Props {
  catId: string;
}

export default function HealthScoreChart({ catId }: Props) {
  const [data, setData] = useState<HealthScorePoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!catId) return;
    setLoading(true);
    getHealthScoreHistory(catId, 180)
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [catId]);

  if (loading) return <div className="h-64 flex items-center justify-center text-gray-400">加载中...</div>;
  if (data.length === 0) return <div className="h-64 flex items-center justify-center text-gray-400">暂无评分数据</div>;

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} domain={[40, 100]} />
          <Tooltip formatter={(value: number) => [`${value} 分`, '健康评分']} />
          <ReferenceLine y={80} stroke="#22c55e" strokeDasharray="3 3" label="优秀" />
          <ReferenceLine y={60} stroke="#eab308" strokeDasharray="3 3" label="良好" />
          <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 3: 创建 Analytics.tsx 页面**

创建 `frontend/src/pages/Analytics.tsx`：

```tsx
import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { BarChart3, Activity, TrendingUp } from 'lucide-react';
import WeightChart from '@/components/WeightChart';
import IndicatorChart from '@/components/IndicatorChart';
import HealthScoreChart from '@/components/HealthScoreChart';
import { getIndicatorNames } from '@/lib/api';
import type { IndicatorNameItem } from '@/types';

interface OutletContext {
  selectedCatId: string | null;
}

export default function Analytics() {
  const { selectedCatId } = useOutletContext<OutletContext>();
  const [indicatorNames, setIndicatorNames] = useState<IndicatorNameItem[]>([]);
  const [selectedIndicator, setSelectedIndicator] = useState<string>('');

  useEffect(() => {
    if (!selectedCatId) return;
    getIndicatorNames(selectedCatId).then((names) => {
      setIndicatorNames(names);
      if (names.length > 0) setSelectedIndicator(names[0].name);
    });
  }, [selectedCatId]);

  if (!selectedCatId) {
    return <div className="p-8 text-center text-gray-400">请先选择一只猫咪</div>;
  }

  const selectedDisplayName = indicatorNames.find((n) => n.name === selectedIndicator)?.display_name || '';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">数据洞察</h1>

      {/* 体重趋势 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-2 text-blue-600 mb-3">
          <TrendingUp size={18} />
          <h2 className="font-semibold">体重趋势 (90天)</h2>
        </div>
        <WeightChart catId={selectedCatId} />
      </div>

      {/* 健康评分趋势 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-2 text-green-600 mb-3">
          <Activity size={18} />
          <h2 className="font-semibold">健康评分趋势 (180天)</h2>
        </div>
        <HealthScoreChart catId={selectedCatId} />
      </div>

      {/* 化验指标对比 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-purple-600">
            <BarChart3 size={18} />
            <h2 className="font-semibold">化验指标历史对比</h2>
          </div>
          <select
            value={selectedIndicator}
            onChange={(e) => setSelectedIndicator(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-1 text-sm"
          >
            {indicatorNames.map((n) => (
              <option key={n.name} value={n.name}>{n.display_name}</option>
            ))}
          </select>
        </div>
        {selectedIndicator && (
          <IndicatorChart
            catId={selectedCatId}
            indicatorName={selectedIndicator}
            displayName={selectedDisplayName}
          />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 注册路由**

在 `frontend/src/App.tsx` 追加 import 和 Route：

```tsx
import Analytics from './pages/Analytics';
```

```tsx
import Analytics from './pages/Analytics';
```

在 Route 列表中追加：

```tsx
<Route path="analytics" element={<Analytics />} />
```

在 `frontend/src/components/Layout.tsx` 导航菜单追加：

```tsx
{ to: '/analytics', icon: BarChart3, label: '数据洞察' }
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd frontend && npx vitest run src/pages/Analytics.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Analytics.tsx frontend/src/components/IndicatorChart.tsx frontend/src/components/HealthScoreChart.tsx frontend/src/App.tsx frontend/src/components/Layout.tsx
git commit -m "feat(frontend): Phase 9 Analytics page with indicator and score charts"
```

---

## Task 5: PDF 导出按钮组件

**Files:**
- Create: `frontend/src/components/PDFExportButton.tsx`
- Modify: `frontend/src/pages/Reports.tsx`

- [ ] **Step 1: 创建 PDFExportButton 组件**

创建 `frontend/src/components/PDFExportButton.tsx`：

```tsx
import { useRef, useState } from 'react';
import { Download } from 'lucide-react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

interface Props {
  targetRef: React.RefObject<HTMLDivElement | null>;
  fileName?: string;
}

export default function PDFExportButton({ targetRef, fileName = 'health-report.pdf' }: Props) {
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!targetRef.current) return;
    setExporting(true);
    try {
      const canvas = await html2canvas(targetRef.current, { scale: 2 });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(fileName);
    } catch (err) {
      console.error('PDF export failed:', err);
      alert('导出失败，请重试');
    } finally {
      setExporting(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={exporting}
      className="flex items-center gap-1 bg-gray-800 text-white px-3 py-1.5 rounded-lg hover:bg-gray-700 disabled:opacity-50"
    >
      <Download size={16} />
      {exporting ? '导出中...' : '导出 PDF'}
    </button>
  );
}
```

- [ ] **Step 2: 在 Reports 页面集成**

在 `frontend/src/pages/Reports.tsx` 中：

```tsx
import { useRef } from 'react';
import PDFExportButton from '@/components/PDFExportButton';

// 在页面根元素添加 ref
const reportRef = useRef<HTMLDivElement>(null);

// JSX 中
<div ref={reportRef}>
  {/* 现有报告内容 */}
</div>

// 在标题栏或操作区插入
<PDFExportButton targetRef={reportRef} fileName={`report-${selectedReport?.id}.pdf`} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/PDFExportButton.tsx frontend/src/pages/Reports.tsx
git commit -m "feat(frontend): Phase 9 PDF export for health reports"
```

---

## Task 6: 侧边栏导航与自审查

**Files:**
- Modify: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: 侧边栏添加导航入口**

在 `Layout.tsx` 的导航数组中追加 `analytics` 路由项（使用 BarChart3 图标）。

- [ ] **Step 2: 自审查 (Self-Review)**

检查清单：
1. **Spec coverage**: Phase 9 要求 → 化验指标历史对比 ✅、健康评分趋势 ✅、PDF 导出 ✅、Dashboard 增强 ✅
2. **Placeholder scan**: 无 TBD/TODO
3. **Type consistency**: `IndicatorHistoryPoint` / `HealthScorePoint` 前后端一致 ✅

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Layout.tsx
git commit -m "feat(frontend): Phase 9 sidebar navigation for analytics"
```

---

## After All Tasks

- [ ] 更新 `TODO.md`: Phase 9 所有 checkbox 标记完成
- [ ] 更新 `README.md`: 功能清单追加 Phase 9
- [ ] 更新 `MEMORY.md`: 记录 Phase 9 完成摘要
- [ ] Run: `cd backend && python3 -m pytest tests/agents/ -v` — 确认全量测试通过
- [ ] Run: `cd frontend && npm run build` — 确认 TypeScript 编译通过
