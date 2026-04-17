# Phase 2: Dashboard & Core Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Dashboard page with todo reminders, weight trend chart, health timeline, and AI report summary. Initialize frontend project and extend backend APIs.

**Architecture:** FastAPI backend + React/Vite frontend, SQLite database, Recharts for charts.

---

## Task 1: Frontend Project Initialization (20 min)

**Prerequisites:** Node.js 18+ installed

**Files to create:**
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/tailwind.config.js`
- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/index.css`

---

### Step 1.1: Initialize Vite Project

- [ ] **Run Vite init command**

```bash
cd /Users/gu/openclaw_workspace/projects/MeowHealth-Web
npm create vite@latest frontend -- --template react-ts
cd frontend
```

**Expected:** `frontend/` directory created with basic React+TS structure

---

### Step 1.2: Install Dependencies

- [ ] **Install core dependencies**

```bash
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npm install react-router-dom axios recharts date-fns lucide-react
npm install -D @types/node
```

**Expected:** `node_modules/` populated, `package.json` updated

---

### Step 1.3: Configure Tailwind CSS

- [ ] **Initialize Tailwind config**

```bash
npx tailwindcss init -p
```

- [ ] **Update `tailwind.config.js`**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] **Update `src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Expected:** Tailwind directives in place

---

### Step 1.4: Configure Path Aliases

- [ ] **Update `vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

- [ ] **Update `tsconfig.json`**

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**Expected:** `@/` imports working

---

### Step 1.5: Setup Basic App Structure

- [ ] **Update `src/main.tsx`**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

- [ ] **Update `src/App.tsx`**

```tsx
import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Cats from './pages/Cats'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/cats" element={<Cats />} />
      </Routes>
    </div>
  )
}

export default App
```

- [ ] **Create placeholder pages**

```bash
mkdir -p src/pages
```

```tsx
// src/pages/Dashboard.tsx
export default function Dashboard() {
  return <div className="p-4">Dashboard</div>
}
```

```tsx
// src/pages/Cats.tsx
export default function Cats() {
  return <div className="p-4">Cats</div>
}
```

---

### Step 1.6: Verify Dev Server

- [ ] **Start dev server**

```bash
npm run dev
```

**Expected:** Server starts on `http://localhost:5173`, pages render without error

---

### Step 1.7: Commit

- [ ] **Commit initialization**

```bash
git add frontend/
git commit -m "chore: init frontend with Vite+React+TS+Tailwind"
```

---

## Task 2: Backend API Extensions (45 min)

**Files:**
- Modify: `backend/app/models/models.py`
- Create: `backend/app/schemas/health_records.py`
- Create: `backend/app/routers/health_records.py`
- Create: `backend/app/routers/todos.py`

---

### Step 2.1: Extend Database Models

- [ ] **Add HealthRecord model to `backend/app/models/models.py`**

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

class HealthRecord(Base):
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False)
    record_type = Column(String, nullable=False)  # 'weight', 'vaccine', 'deworm', 'symptom', 'other'
    record_date = Column(DateTime, default=datetime.utcnow)
    title = Column(String(100))
    description = Column(Text)
    value = Column(Float)  # For weight
    unit = Column(String(20))  # 'kg', 'g', etc.
    
    cat = relationship("Cat", back_populates="health_records")
```

- [ ] **Add relationship to Cat model**

```python
# In Cat class, add:
health_records = relationship("HealthRecord", back_populates="cat", cascade="all, delete-orphan")
```

- [ ] **Add Todo/Reminder model**

```python
class TodoReminder(Base):
    __tablename__ = "todo_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False)
    title = Column(String(100), nullable=False)
    due_date = Column(DateTime, nullable=False)
    reminder_type = Column(String(50))  # 'vaccine', 'deworm', 'checkup', etc.
    is_completed = Column(Integer, default=0)  # 0 or 1
    created_at = Column(DateTime, default=datetime.utcnow)
    
    cat = relationship("Cat", back_populates="todos")
```

- [ ] **Add todos relationship to Cat model**

```python
todos = relationship("TodoReminder", back_populates="cat", cascade="all, delete-orphan")
```

---

### Step 2.2: Create Health Record Schemas

- [ ] **Create `backend/app/schemas/health_records.py`**

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class HealthRecordBase(BaseModel):
    record_type: str
    record_date: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None

class HealthRecordCreate(HealthRecordBase):
    cat_id: int

class HealthRecordResponse(HealthRecordBase):
    id: int
    cat_id: int
    
    class Config:
        from_attributes = True

class WeightHistoryResponse(BaseModel):
    dates: list[datetime]
    weights: list[float]
```

---

### Step 2.3: Create Health Records Router

- [ ] **Create `backend/app/routers/health_records.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import HealthRecord, Cat
from app.schemas.health_records import HealthRecordCreate, HealthRecordResponse, WeightHistoryResponse
from datetime import datetime

router = APIRouter(prefix="/api/v1/health-records", tags=["health-records"])

@router.post("/", response_model=HealthRecordResponse)
def create_record(record: HealthRecordCreate, db: Session = Depends(get_db)):
    db_record = HealthRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/cat/{cat_id}", response_model=List[HealthRecordResponse])
def get_cat_records(cat_id: int, record_type: str = None, db: Session = Depends(get_db)):
    query = db.query(HealthRecord).filter(HealthRecord.cat_id == cat_id)
    if record_type:
        query = query.filter(HealthRecord.record_type == record_type)
    return query.order_by(HealthRecord.record_date.desc()).all()

@router.get("/cat/{cat_id}/weights", response_model=WeightHistoryResponse)
def get_weight_history(cat_id: int, limit: int = 30, db: Session = Depends(get_db)):
    records = db.query(HealthRecord).filter(
        HealthRecord.cat_id == cat_id,
        HealthRecord.record_type == "weight"
    ).order_by(HealthRecord.record_date.asc()).limit(limit).all()
    
    return WeightHistoryResponse(
        dates=[r.record_date for r in records],
        weights=[r.value for r in records if r.value]
    )

@router.delete("/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(HealthRecord).filter(HealthRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(record)
    db.commit()
    return {"message": "Record deleted"}
```

---

### Step 2.4: Create Todos Router

- [ ] **Create `backend/app/routers/todos.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.models.models import TodoReminder
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])

class TodoCreate(BaseModel):
    cat_id: int
    title: str
    due_date: datetime
    reminder_type: str = "other"

class TodoResponse(BaseModel):
    id: int
    cat_id: int
    title: str
    due_date: datetime
    reminder_type: str
    is_completed: bool
    
    class Config:
        from_attributes = True

@router.post("/", response_model=TodoResponse)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = TodoReminder(**todo.dict(), is_completed=0)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@router.get("/cat/{cat_id}", response_model=List[TodoResponse])
def get_cat_todos(cat_id: int, include_completed: bool = False, db: Session = Depends(get_db)):
    query = db.query(TodoReminder).filter(TodoReminder.cat_id == cat_id)
    if not include_completed:
        query = query.filter(TodoReminder.is_completed == 0)
    return query.order_by(TodoReminder.due_date.asc()).all()

@router.post("/{todo_id}/complete")
def complete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(TodoReminder).filter(TodoReminder.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.is_completed = 1
    db.commit()
    return {"message": "Todo marked as completed"}

@router.delete("/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(TodoReminder).filter(TodoReminder.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
    return {"message": "Todo deleted"}
```

---

### Step 2.5: Register New Routers

- [ ] **Update `backend/main.py`**

```python
from app.routers import cats, settings, health_records, todos

app.include_router(cats.router)
app.include_router(settings.router)
app.include_router(health_records.router)
app.include_router(todos.router)
```

---

### Step 2.6: Run Migrations & Tests

- [ ] **Initialize new tables**

```bash
cd backend
python init_database.py
```

- [ ] **Test new endpoints**

```bash
pytest tests/ -v
```

**Expected:** All tests pass

---

### Step 2.7: Commit

- [ ] **Commit backend changes**

```bash
git add backend/
git commit -m "feat: add health records and todos APIs"
```

---

## Task 3: Frontend API Client (15 min)

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/types/index.ts`

---

### Step 3.1: Define TypeScript Types

- [ ] **Create `frontend/src/types/index.ts`**

```typescript
export interface Cat {
  id: number;
  name: string;
  breed?: string;
  birth_date?: string;
  gender?: string;
  avatar_url?: string;
}

export interface HealthRecord {
  id: number;
  cat_id: number;
  record_type: 'weight' | 'vaccine' | 'deworm' | 'symptom' | 'other';
  record_date: string;
  title?: string;
  description?: string;
  value?: number;
  unit?: string;
}

export interface Todo {
  id: number;
  cat_id: number;
  title: string;
  due_date: string;
  reminder_type: string;
  is_completed: boolean;
}

export interface WeightHistory {
  dates: string[];
  weights: number[];
}
```

---

### Step 3.2: Create API Client

- [ ] **Create `frontend/src/lib/api.ts`**

```typescript
import axios from 'axios';
import type { Cat, HealthRecord, Todo, WeightHistory } from '@/types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cats
export const getCats = () => api.get<Cat[]>('/cats/').then(r => r.data);
export const getCat = (id: number) => api.get<Cat>(`/cats/${id}`).then(r => r.data);

// Health Records
export const getHealthRecords = (catId: number, type?: string) => 
  api.get<HealthRecord[]>(`/health-records/cat/${catId}`, { params: { record_type: type } }).then(r => r.data);

export const createHealthRecord = (record: Omit<HealthRecord, 'id'>) =>
  api.post<HealthRecord>('/health-records/', record).then(r => r.data);

export const getWeightHistory = (catId: number, limit?: number) =>
  api.get<WeightHistory>(`/health-records/cat/${catId}/weights`, { params: { limit } }).then(r => r.data);

// Todos
export const getTodos = (catId: number, includeCompleted?: boolean) =>
  api.get<Todo[]>(`/todos/cat/${catId}`, { params: { include_completed: includeCompleted } }).then(r => r.data);

export const createTodo = (todo: Omit<Todo, 'id' | 'is_completed'>) =>
  api.post<Todo>('/todos/', todo).then(r => r.data);

export const completeTodo = (todoId: number) =>
  api.post(`/todos/${todoId}/complete`).then(r => r.data);

export const deleteTodo = (todoId: number) =>
  api.delete(`/todos/${todoId}`).then(r => r.data);
```

---

### Step 3.3: Commit

- [ ] **Commit API client**

```bash
git add frontend/src/lib/api.ts frontend/src/types/index.ts
git commit -m "feat: add API client and TypeScript types"
```

---

## Task 4: Shared Components (40 min)

**Files:**
- Create: `frontend/src/components/CatSelector.tsx`
- Create: `frontend/src/components/Timeline.tsx`
- Create: `frontend/src/components/WeightChart.tsx`
- Create: `frontend/src/components/TodoCard.tsx`
- Create: `frontend/src/components/Sidebar.tsx`

---

### Step 4.1: Cat Selector Component

- [ ] **Create `frontend/src/components/CatSelector.tsx`**

```tsx
import { useState, useEffect } from 'react';
import { getCats } from '@/lib/api';
import type { Cat } from '@/types';

interface CatSelectorProps {
  selectedCatId: number | null;
  onSelect: (catId: number) => void;
}

export default function CatSelector({ selectedCatId, onSelect }: CatSelectorProps) {
  const [cats, setCats] = useState<Cat[]>([]);

  useEffect(() => {
    getCats().then(setCats);
  }, []);

  return (
    <div className="flex items-center gap-2 p-3 bg-white rounded-lg shadow-sm">
      <span className="text-sm text-gray-500">当前猫咪:</span>
      <select
        value={selectedCatId || ''}
        onChange={(e) => onSelect(Number(e.target.value))}
        className="px-3 py-1 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">请选择</option>
        {cats.map(cat => (
          <option key={cat.id} value={cat.id}>{cat.name}</option>
        ))}
      </select>
    </div>
  );
}
```

---

### Step 4.2: Weight Chart Component

- [ ] **Create `frontend/src/components/WeightChart.tsx`**

```tsx
import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getWeightHistory } from '@/lib/api';

interface WeightChartProps {
  catId: number;
}

export default function WeightChart({ catId }: WeightChartProps) {
  const [data, setData] = useState<{ date: string; weight: number }[]>([]);

  useEffect(() => {
    if (!catId) return;
    getWeightHistory(catId, 30).then(history => {
      const formatted = history.dates.map((date, i) => ({
        date: new Date(date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
        weight: history.weights[i],
      }));
      setData(formatted);
    });
  }, [catId]);

  if (data.length === 0) {
    return <div className="text-gray-400 text-center py-8">暂无体重数据</div>;
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={['dataMin - 0.5', 'dataMax + 0.5']} />
          <Tooltip />
          <Line type="monotone" dataKey="weight" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

---

### Step 4.3: Timeline Component

- [ ] **Create `frontend/src/components/Timeline.tsx`**

```tsx
import type { HealthRecord } from '@/types';
import { Activity, Syringe, Pill, AlertCircle } from 'lucide-react';

interface TimelineProps {
  records: HealthRecord[];
}

const typeIcons = {
  weight: Activity,
  vaccine: Syringe,
  deworm: Pill,
  symptom: AlertCircle,
  other: Activity,
};

const typeColors = {
  weight: 'bg-blue-100 text-blue-600',
  vaccine: 'bg-green-100 text-green-600',
  deworm: 'bg-purple-100 text-purple-600',
  symptom: 'bg-red-100 text-red-600',
  other: 'bg-gray-100 text-gray-600',
};

export default function Timeline({ records }: TimelineProps) {
  return (
    <div className="space-y-3">
      {records.map(record => {
        const Icon = typeIcons[record.record_type] || Activity;
        return (
          <div key={record.id} className="flex gap-3 items-start">
            <div className={`p-2 rounded-full ${typeColors[record.record_type] || typeColors.other}`}>
              <Icon size={16} />
            </div>
            <div className="flex-1">
              <div className="flex justify-between items-start">
                <span className="font-medium">{record.title || record.record_type}</span>
                <span className="text-xs text-gray-400">
                  {new Date(record.record_date).toLocaleDateString('zh-CN')}
                </span>
              </div>
              {record.description && (
                <p className="text-sm text-gray-600 mt-1">{record.description}</p>
              )}
              {record.value && (
                <span className="text-sm font-medium text-blue-600">
                  {record.value} {record.unit}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

---

### Step 4.4: Todo Card Component

- [ ] **Create `frontend/src/components/TodoCard.tsx`**

```tsx
import { useState } from 'react';
import { Check, Trash2, Clock } from 'lucide-react';
import { completeTodo, deleteTodo } from '@/lib/api';
import type { Todo } from '@/types';

interface TodoCardProps {
  todo: Todo;
  onUpdate: () => void;
}

export default function TodoCard({ todo, onUpdate }: TodoCardProps) {
  const [isCompleted, setIsCompleted] = useState(todo.is_completed);

  const handleComplete = async () => {
    await completeTodo(todo.id);
    setIsCompleted(true);
    onUpdate();
  };

  const handleDelete = async () => {
    await deleteTodo(todo.id);
    onUpdate();
  };

  const daysUntil = Math.ceil((new Date(todo.due_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  const isUrgent = daysUntil <= 3 && !isCompleted;

  return (
    <div className={`p-3 rounded-lg border ${isUrgent ? 'border-orange-300 bg-orange-50' : 'border-gray-200 bg-white'}`}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <p className={`font-medium ${isCompleted ? 'line-through text-gray-400' : ''}`}>
            {todo.title}
          </p>
          <div className="flex items-center gap-1 mt-1 text-sm text-gray-500">
            <Clock size={14} />
            <span className={isUrgent ? 'text-orange-600 font-medium' : ''}>
              {daysUntil <= 0 ? '今天到期' : `${daysUntil}天后到期`}
            </span>
          </div>
        </div>
        <div className="flex gap-1">
          {!isCompleted && (
            <button
              onClick={handleComplete}
              className="p-1 text-green-600 hover:bg-green-100 rounded"
            >
              <Check size={18} />
            </button>
          )}
          <button
            onClick={handleDelete}
            className="p-1 text-red-600 hover:bg-red-100 rounded"
          >
            <Trash2 size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

### Step 4.5: Sidebar Component

- [ ] **Create `frontend/src/components/Sidebar.tsx`**

```tsx
import { Home, Cat, Settings, FileText } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import CatSelector from './CatSelector';

interface SidebarProps {
  selectedCatId: number | null;
  onSelectCat: (id: number) => void;
}

const navItems = [
  { path: '/', icon: Home, label: 'Dashboard' },
  { path: '/cats', icon: Cat, label: '猫咪管理' },
  { path: '/reports', icon: FileText, label: '化验报告' },
  { path: '/settings', icon: Settings, label: '设置' },
];

export default function Sidebar({ selectedCatId, onSelectCat }: SidebarProps) {
  const location = useLocation();

  return (
    <aside className="w-64 bg-white border-r h-screen sticky top-0">
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold text-gray-800">MeowHealth</h1>
        <p className="text-xs text-gray-500 mt-1">猫咪健康守护</p>
      </div>
      
      <div className="p-4">
        <CatSelector selectedCatId={selectedCatId} onSelect={onSelectCat} />
      </div>

      <nav className="px-2 py-2">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg mb-1 ${
                isActive ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
```

---

### Step 4.6: Commit

- [ ] **Commit components**

```bash
git add frontend/src/components/
git commit -m "feat: add shared components (CatSelector, WeightChart, Timeline, TodoCard, Sidebar)"
```

---

## Task 5: Dashboard Page (50 min)

**Files:**
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/components/UploadZone.tsx`

---

### Step 5.1: Upload Zone Component

- [ ] **Create `frontend/src/components/UploadZone.tsx`**

```tsx
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image } from 'lucide-react';

interface UploadZoneProps {
  onUpload: (files: File[]) => void;
}

export default function UploadZone({ onUpload }: UploadZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onUpload(acceptedFiles);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf'],
    },
    multiple: true,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
        isDragActive ? 'border-blue-500 bg-blue-50' : 'border-blue-300 hover:border-blue-400'
      }`}
    >
      <input {...getInputProps()} />
      <Upload className="mx-auto mb-2 text-blue-500" size={32} />
      <p className="text-sm text-gray-600">
        {isDragActive ? '松开以上传文件' : '拖拽或点击上传化验单'}
      </p>
      <p className="text-xs text-gray-400 mt-1">
        支持 PDF, JPG, PNG
      </p>
      <div className="flex justify-center gap-4 mt-3">
        <span className="flex items-center gap-1 text-xs text-gray-500">
          <FileText size={14} /> 血常规
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-500">
          <FileText size={14} /> 生化全项
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-500">
          <Image size={14} /> 尿检报告
        </span>
      </div>
    </div>
  );
}
```

- [ ] **Install react-dropzone**

```bash
cd frontend
npm install react-dropzone
```

---

### Step 5.2: Dashboard Page

- [ ] **Update `frontend/src/pages/Dashboard.tsx`**

```tsx
import { useState, useEffect } from 'react';
import { Plus, TrendingUp, ClipboardList } from 'lucide-react';
import WeightChart from '@/components/WeightChart';
import Timeline from '@/components/Timeline';
import TodoCard from '@/components/TodoCard';
import UploadZone from '@/components/UploadZone';
import { getHealthRecords, getTodos, createTodo } from '@/lib/api';
import type { HealthRecord, Todo } from '@/types';

interface DashboardProps {
  selectedCatId: number | null;
}

export default function Dashboard({ selectedCatId }: DashboardProps) {
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [todos, setTodos] = useState<Todo[]>([]);
  const [showAddTodo, setShowAddTodo] = useState(false);
  const [newTodoTitle, setNewTodoTitle] = useState('');
  const [newTodoDate, setNewTodoDate] = useState('');

  useEffect(() => {
    if (!selectedCatId) return;
    loadData();
  }, [selectedCatId]);

  const loadData = async () => {
    if (!selectedCatId) return;
    const [recordsData, todosData] = await Promise.all([
      getHealthRecords(selectedCatId),
      getTodos(selectedCatId),
    ]);
    setRecords(recordsData.slice(0, 10));
    setTodos(todosData);
  };

  const handleAddTodo = async () => {
    if (!selectedCatId || !newTodoTitle || !newTodoDate) return;
    await createTodo({
      cat_id: selectedCatId,
      title: newTodoTitle,
      due_date: new Date(newTodoDate).toISOString(),
      reminder_type: 'other',
    });
    setNewTodoTitle('');
    setNewTodoDate('');
    setShowAddTodo(false);
    loadData();
  };

  const handleUpload = (files: File[]) => {
    // TODO: Implement upload to backend
    console.log('Uploading files:', files);
  };

  if (!selectedCatId) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-500">请先在侧边栏选择一只猫咪</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
        <p className="text-gray-500">猫咪健康概览</p>
      </div>

      {/* Upload Zone */}
      <div className="mb-6">