# 前端组件文档

> **文档层级**: 前端组件使用指南
>
> 本文档描述 MeowHealth Web 前端的核心组件及其使用方式。

---

## 通用组件

### UploadZone

**功能说明**: 文件上传组件，支持拖拽上传和点击选择。用于上传猫咪化验单（PDF、JPG、PNG），上传后自动调用 AI 分析生成报告。

**Props**:

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `catId` | `string` | ✅ | 关联的猫咪 ID |
| `onUploadComplete` | `(reportId: string) => void` | ✅ | 上传完成回调，返回报告 ID |

**内部状态**:

| 状态 | 类型 | 说明 |
|------|------|------|
| `uploadingFiles` | `UploadingFile[]` | 当前正在上传的文件列表 |

**UploadingFile 类型**:

```typescript
interface UploadingFile {
  id: string;           // 文件唯一标识
  file: File;           // 原生文件对象
  progress: number;     // 上传进度 (0-100)
  status: 'uploading' | 'analyzing' | 'complete' | 'error';
  error?: string;       // 错误信息
  reportId?: string;    // 生成报告的 ID
}
```

**使用示例**:

```tsx
import { UploadZone } from '@/components/UploadZone';

function ReportsPage() {
  const handleUploadComplete = (reportId: string) => {
    console.log('报告已生成:', reportId);
    // 刷新报告列表
    loadReports();
  };

  return (
    <UploadZone
      catId={selectedCatId}
      onUploadComplete={handleUploadComplete}
    />
  );
}
```

**功能特性**:
- 支持拖拽上传和点击选择
- 支持 PDF、JPG、PNG 格式
- 单个文件最大 10MB
- 实时显示上传进度（上传中 → AI 分析中 → 完成）
- 错误状态提示
- 可移除正在上传的文件
- 预设标签提示：血常规、生化全项、尿检报告

---

### ReportCard

**功能说明**: 化验报告展示组件，按系统分类展示指标，支持展开/收起，异常指标高亮显示。

**Props**:

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | `string` | ✅ | 报告标题 |
| `date` | `string` | ✅ | 报告日期 (ISO 格式) |
| `summary` | `string` | ✅ | AI 生成的报告摘要 |
| `indicators` | `Indicator[]` | ✅ | 检测指标数组 |
| `recommendations` | `string[]` | ✅ | AI 建议列表 |

**Indicator 类型定义**:

```typescript
interface Indicator {
  id: string;               // 指标唯一标识
  name: string;             // 指标代码 (如 WBC, ALT)
  display_name: string;     // 显示名称 (如 白细胞计数)
  value: number | null;    // 检测值
  unit: string;             // 单位 (如 10^9/L)
  reference_min: number | null;  // 参考范围最小值
  reference_max: number | null;  // 参考范围最大值
  is_abnormal: boolean;     // 是否异常
  explanation: string | null; // 异常说明
}
```

**使用示例**:

```tsx
import { ReportCard } from '@/components/ReportCard';

function ReportDetail({ report }) {
  return (
    <ReportCard
      title={report.title}
      date={report.date}
      summary={report.ai_summary}
      indicators={report.indicators}
      recommendations={report.actionable_advice}
    />
  );
}
```

**功能特性**:
- 按系统分类展示指标：血液系统、肝脏功能、肾脏功能、其他指标
- 自动检测异常指标（高于/低于参考范围）
- 异常指标高亮显示（红色=偏高，黄色=偏低）
- 分类面板默认展开（当该分类存在异常指标时）
- 显示参考范围和异常说明
- AI 建议列表带序号展示

---

### ChatAssistant

**功能说明**: AI 对话助手组件，用于解读化验报告。支持与 AI 对话询问报告相关问题。

**Props**:

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `reportId` | `string` | ✅ | 关联的报告 ID |

**内部状态**:

| 状态 | 类型 | 说明 |
|------|------|------|
| `messages` | `Message[]` | 对话消息列表 |
| `input` | `string` | 当前输入内容 |
| `loading` | `boolean` | 是否正在发送/等待回复 |
| `isOpen` | `boolean` | 面板是否展开 |

**Message 类型**:

```typescript
interface Message {
  id: string;
  role: 'user' | 'model';
  content: string;
  created_at: string;
}
```

**使用示例**:

```tsx
import { ChatAssistant } from '@/components/ChatAssistant';

function ReportDetail({ report }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <ReportCard {...report} />
      </div>
      <div className="lg:col-span-1">
        <ChatAssistant reportId={report.id} />
      </div>
    </div>
  );
}
```

**功能特性**:
- 自动加载历史对话记录
- 支持快捷提问预设（肌酐偏高严重吗？/ 建议换什么处方粮？/ 对比上次有改善吗？/ 需要注意什么？）
- Enter 发送，Shift+Enter 换行
- 消息气泡样式区分（用户=蓝色，AI=灰色）
- 可收起为悬浮按钮
- 发送状态加载动画

---

## 页面组件

### Dashboard

**路径**: `frontend/src/pages/Dashboard.tsx`

**功能模块**:

| 模块 | 说明 | 依赖组件 |
|------|------|----------|
| 统计卡片 | 展示最新体重、待办提醒数、健康记录数 | 自定义卡片 |
| 体重趋势 | 展示猫咪体重变化图表 | `WeightChart` |
| 近期动态 | 展示最近的健康记录和体重记录时间线 | `Timeline` |
| 待办提醒 | 展示并管理提醒事项，支持添加新提醒 | `TodoCard` |

**数据加载**:
- `getHealthRecords(catId)` - 健康记录
- `getWeightLogs(catId, limit)` - 体重记录
- `getReminders(catId, completed)` - 待办提醒

**状态管理**:
- `records` - 健康记录列表
- `weightLogs` - 体重记录列表
- `reminders` - 提醒列表
- `showAddReminder` - 是否显示添加提醒表单
- `newReminder` - 新提醒表单数据

**布局结构**:
```
Dashboard
├── Header (标题 + 描述)
├── Stats Cards (3 列网格)
│   ├── 最新体重
│   ├── 待办提醒
│   └── 健康记录
└── Main Content Grid (2 列)
    ├── Left Column
    │   ├── 体重趋势 (WeightChart)
    │   └── 近期动态 (Timeline)
    └── Right Column
        └── 待办提醒 (TodoCard 列表)
```

---

### Cats

**路径**: `frontend/src/pages/Cats.tsx`

**功能模块**:

| 模块 | 说明 |
|------|------|
| 猫咪列表 | 网格展示所有猫咪卡片 |
| 添加猫咪 | 表单添加新猫咪档案 |
| 删除猫咪 | 删除猫咪及关联数据 |

**数据加载**:
- `getCats()` - 获取猫咪列表

**状态管理**:
- `cats` - 猫咪列表
- `showAddForm` - 是否显示添加表单
- `newCat` - 新猫咪表单数据

**CatCreate 类型**:

```typescript
interface CatCreate {
  name: string;        // 名字
  breed: string;       // 品种
  birthday: string;    // 生日
  gender: 'male' | 'female';  // 性别
  is_neutered: boolean;       // 是否绝育
}
```

**布局结构**:
```
Cats
├── Header (标题 + 添加按钮)
├── Add Form (条件渲染)
│   ├── 名字输入
│   ├── 品种输入
│   ├── 生日选择
│   ├── 性别选择
│   ├── 绝育复选框
│   └── 保存/取消按钮
└── Cats Grid (1-3 列响应式)
    └── Cat Card
        ├── 名字
        ├── 品种
        ├── 生日
        ├── 性别标签
        ├── 绝育标签
        └── 删除按钮
```

---

### Reports

**路径**: `frontend/src/pages/Reports.tsx`

**功能模块**:

| 模块 | 说明 | 依赖组件 |
|------|------|----------|
| API Key 配置 | 配置 Gemini API Key | 模态框 |
| 文件上传 | 上传化验单 | `UploadZone` |
| 报告列表 | 展示所有报告卡片 | 自定义卡片 |
| 报告详情 | 展示单份报告完整内容 | `ReportCard` + `ChatAssistant` |
| 删除报告 | 删除单份报告 | - |

**数据加载**:
- `api.get('/reports/')` - 获取报告列表
- `api.get('/settings/gemini-api-key')` - 检查 API Key

**状态管理**:
- `reports` - 报告列表
- `selectedReport` - 当前选中的报告（null 表示列表页）
- `apiKeyConfigured` - API Key 是否已配置
- `showApiKeyInput` - 是否显示 API Key 输入框
- `apiKey` - 输入的 API Key

**布局结构**:
```
Reports
├── Header (标题 + API Key 配置按钮)
├── API Key Modal (条件渲染)
├── UploadZone
├── Reports List (网格布局)
│   └── Report Card
│       ├── 文件图标
│       ├── 标题
│       ├── 日期
│       └── AI 摘要预览
└── Report Detail (当 selectedReport 存在)
    ├── 返回按钮 + 标题 + 删除按钮
    └── Grid (3 列)
        ├── ReportCard (占 2 列)
        └── ChatAssistant (占 1 列)
```

**页面状态流转**:
```
列表页 (selectedReport = null)
  ↓ 点击报告卡片
详情页 (selectedReport = report)
  ↓ 点击返回
列表页 (selectedReport = null)
```

---

## 类型定义汇总

### 核心类型

```typescript
// 检测指标
interface Indicator {
  id: string;
  name: string;
  display_name: string;
  value: number | null;
  unit: string;
  reference_min: number | null;
  reference_max: number | null;
  is_abnormal: boolean;
  explanation: string | null;
}

// 化验报告
interface Report {
  id: string;
  cat_id: string;
  title: string;
  date: string;
  ai_summary: string;
  actionable_advice: string[];
  indicators: Indicator[];
  file_name?: string;
  created_at: string;
}

// 猫咪
interface Cat {
  id: string;
  name: string;
  breed: string;
  birthday: string;
  gender: 'male' | 'female';
  is_neutered: boolean;
}

// 新建猫咪
interface CatCreate {
  name: string;
  breed: string;
  birthday: string;
  gender: 'male' | 'female';
  is_neutered: boolean;
}
```

---

*文档版本: 2026-04-22*
