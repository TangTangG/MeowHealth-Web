# MeowHealth Web Phase 2 - 详细任务拆解

> 每个任务包含：文件路径、验收标准、预估时间

---

## Task 1: 修复后端 API

### Step 1.1: 验证 health_records 路由
**文件：** `backend/app/routers/health_records.py`
**验收：** 导入无错误，路由前缀 `/api/v1/health-records`，ID 类型为 string
**预估：** 5 分钟

### Step 1.2: 验证 reminders 路由
**文件：** `backend/app/routers/reminders.py`
**验收：** 导入无错误，路由前缀 `/api/v1/reminders`，ID 类型为 string
**预估：** 5 分钟

### Step 1.3: 启动后端测试端点
**命令：** uvicorn main:app --host 0.0.0.0 --port 8000
**验收：** /api/v1/cats/、/api/v1/health-records/、/api/v1/reminders/ 都返回 200
**预估：** 10 分钟

---

## Task 2: 前端类型定义

### Step 2.1: 创建类型文件
**文件：** `frontend/src/types/index.ts`
**类型清单：**
- Cat (id: string, name, breed, birthday, gender, is_neutered, photo_path, target_weight_min/max, created_at, updated_at)
- CatCreate (name, breed, birthday, gender, is_neutered?, photo_path?, target_weight_min?, target_weight_max?)
- WeightLog (id, cat_id, date, value, note, created_at, updated_at)
- WeightLogCreate (date, value, note?)
- Reminder (id, cat_id?, title, description?, reminder_type, due_date, is_completed, completed_at?, created_at, updated_at)
- ReminderCreate (cat_id?, title, description?, reminder_type, due_date, is_completed?)
- HealthRecord (id, cat_id, date, type, title, note?, ai_summary?, actionable_advice?, created_at, updated_at)
**验收：** TypeScript 编译无错误
**预估：** 10 分钟

---

## Task 3: 前端 API 客户端

### Step 3.1: 创建 API 客户端
**文件：** `frontend/src/lib/api.ts`
**API 清单：**
- getCats(): Promise<Cat[]>
- getCat(id: string): Promise<Cat>
- createCat(cat: CatCreate): Promise<Cat>
- updateCat(id: string, cat: CatCreate): Promise<Cat>
- deleteCat(id: string): Promise<void>
- getWeightLogs(catId: string, limit?: number): Promise<WeightLog[]>
- createWeightLog(catId: string, log: WeightLogCreate): Promise<WeightLog>
- getReminders(catId: string, includeCompleted?: boolean): Promise<Reminder[]>
- createReminder(catId: string, reminder: ReminderCreate): Promise<Reminder>
- completeReminder(reminderId: string): Promise<void>
- deleteReminder(reminderId: string): Promise<void>
- getHealthRecords(catId: string, type?: string, limit?: number): Promise<HealthRecord[]>
**验收：** 所有函数类型正确，axios 配置正确
**预估：** 15 分钟

---

## Task 4: 共享组件

### Step 4.1: 创建目录
**命令：** mkdir -p frontend/src/components frontend/src/lib frontend/src/types
**预估：** 1 分钟

### Step 4.2: CatSelector 组件
**文件：** `frontend/src/components/CatSelector.tsx`
**功能：** 下拉选择猫咪，显示当前猫咪
**Props：** selectedCatId: string | null, onSelect: (catId: string) => void
**验收：** 能获取猫咪列表，选择后触发回调
**预估：** 8 分钟

### Step 4.3: WeightChart 组件
**文件：** `frontend/src/components/WeightChart.tsx`
**功能：** 使用 Recharts 显示体重趋势图
**Props：** catId: string
**验收：** 能获取体重数据，图表正确显示，无数据时显示提示
**预估：** 10 分钟

### Step 4.4: Timeline 组件
**文件：** `frontend/src/components/Timeline.tsx`
**功能：** 健康事件时间轴
**Props：** records: HealthRecord[], weightLogs?: WeightLog[], reminders?: Reminder[]
**验收：** 显示多种类型事件，按时间倒序，不同类型有不同图标颜色
**预估：** 10 分钟

### Step 4.5: TodoCard 组件
**文件：** `frontend/src/components/TodoCard.tsx`
**功能：** 待办提醒卡片
**Props：** reminder: Reminder, onUpdate: () => void
**验收：** 显示标题/描述/到期时间，urgent/overdue 有不同颜色，完成和删除按钮正常
**预估：** 10 分钟

### Step 4.6: Sidebar 组件
**文件：** `frontend/src/components/Sidebar.tsx`
**功能：** 侧边栏导航 + 猫咪切换器
**Props：** selectedCatId: string | null, onSelectCat: (id: string) => void
**验收：** 显示 Logo，嵌入 CatSelector，导航链接正确高亮
**预估：** 8 分钟

---

## Task 5: 页面布局与 Dashboard

### Step 5.1: Layout 组件
**文件：** `frontend/src/components/Layout.tsx`
**功能：** 整体布局框架（Sidebar + Content）
**验收：** 使用 Outlet 传递 selectedCatId 上下文
**预估：** 5 分钟

### Step 5.2: 更新 App.tsx
**文件：** `frontend/src/App.tsx`
**功能：** 使用 Layout 组件，配置路由
**路由：** /(Dashboard), /cats(Cats), /reports(placeholder), /settings(placeholder)
**预估：** 3 分钟

### Step 5.3: Dashboard 页面
**文件：** `frontend/src/pages/Dashboard.tsx`
**功能：** 完整的 Dashboard 页面
**包含：**
- 顶部统计卡片（最新体重、待办提醒数、健康记录数）
- 体重趋势图（WeightChart）
- 待办提醒列表（TodoCard）
- 近期动态时间轴（Timeline）
- 添加提醒表单
**验收：** 能加载数据，显示图表，添加/完成/删除提醒
**预估：** 30 分钟

### Step 5.4: Cats 页面
**文件：** `frontend/src/pages/Cats.tsx`
**功能：** 猫咪列表页面
**包含：**
- 猫咪列表展示
- 添加猫咪表单
- 删除猫咪按钮
**验收：** 能显示列表，添加猫咪，删除猫咪
**预估：** 15 分钟

---

## Task 6: 联调测试

### Step 6.1: 启动后端
**命令：** cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
**验收：** 服务启动，API 可访问
**预估：** 3 分钟

### Step 6.2: 启动前端
**命令：** cd frontend && npm run dev
**验收：** 服务启动在 http://localhost:5173
**预估：** 2 分钟

### Step 6.3: 测试数据流
**测试步骤：**
1. 添加一只猫咪
2. 记录体重
3. 添加提醒
4. 查看 Dashboard 图表和列表
**验收：** 数据正确显示，交互正常
**预估：** 10 分钟

---

## 总时间估算

| Task | 时间 |
|------|------|
| Task 1: 后端 API 修复 | 20 分钟 |
| Task 2: 类型定义 | 10 分钟 |
| Task 3: API 客户端 | 15 分钟 |
| Task 4: 共享组件 | 47 分钟 |
| Task 5: 页面布局 | 53 分钟 |
| Task 6: 联调测试 | 15 分钟 |
| **总计** | **约 2.5 小时** |
