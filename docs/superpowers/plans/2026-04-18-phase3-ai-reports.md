# Phase 3: AI 化验单模块开发计划

> 目标：实现文件上传、Gemini OCR 解读、结果展示功能

---

## 任务总览

| 任务 | 内容 | 预估时间 |
|------|------|---------|
| Task 1 | 后端文件上传接口 | 20 分钟 |
| Task 2 | Gemini API 集成 | 25 分钟 |
| Task 3 | 前端拖拽上传组件 | 20 分钟 |
| Task 4 | 化验单结果展示页面 | 30 分钟 |
| Task 5 | 悬浮对话助手 | 25 分钟 |
| Task 6 | 联调测试 | 15 分钟 |
| **总计** | | **约 2.5 小时** |

---

## Task 1: 后端文件上传接口

### Step 1.1: 配置文件上传目录

**文件：** `backend/app/core/config.py`（新建）

```python
import os

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

os.makedirs(UPLOAD_DIR, exist_ok=True)
```

### Step 1.2: 创建上传路由

**文件：** `backend/app/routers/reports.py`（新建）

```python
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import ReportAttachment, HealthRecord
import uuid
import shutil
from pathlib import Path

router = APIRouter(prefix="/reports", tags=["reports"])

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload/{cat_id}")
async def upload_report(
    cat_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传化验单文件"""
    # 验证文件类型
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".jpg", ".jpeg", ".png"]:
        raise HTTPException(400, "不支持的文件格式")
    
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{ext}"
    
    # 保存文件
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # 创建记录
    attachment = ReportAttachment(
        id=file_id,
        cat_id=cat_id,
        file_name=file.filename,
        file_path=str(file_path),
        file_type=ext,
    )
    db.add(attachment)
    db.commit()
    
    return {"id": file_id, "file_name": file.filename}

@router.get("/cat/{cat_id}")
def get_cat_reports(cat_id: str, db: Session = Depends(get_db)):
    """获取猫咪的所有化验单"""
    reports = db.query(ReportAttachment).filter(
        ReportAttachment.cat_id == cat_id
    ).order_by(ReportAttachment.created_at.desc()).all()
    return reports
```

### Step 1.3: 注册路由

**文件：** `backend/main.py`

```python
from app.routers import reports

app.include_router(reports.router, prefix="/api/v1")
```

**验收：**
- [ ] POST /api/v1/reports/upload/{cat_id} 能上传文件
- [ ] GET /api/v1/reports/cat/{cat_id} 能获取列表
- [ ] 文件保存到 ./uploads 目录

---

## Task 2: Gemini API 集成

### Step 2.1: 配置 Gemini

**文件：** `backend/app/core/config.py`

```python
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
```

### Step 2.2: 创建 AI 服务

**文件：** `backend/app/services/ai_service.py`（新建）

```python
import google.generativeai as genai
from app.core.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

REPORT_ANALYSIS_PROMPT = """
你是一位专业的兽医化验单解读助手。请分析以下宠物化验单内容，并输出 JSON 格式的结果。

要求：
1. 提取所有检测指标（名称、数值、单位、参考范围）
2. 标记异常指标（偏高/偏低）
3. 给出整体健康评估
4. 提供 actionable 的建议

输出格式：
{
  "indicators": [
    {
      "name": "指标名称",
      "value": "检测值",
      "unit": "单位",
      "reference_range": "参考范围",
      "status": "normal|high|low",
      "explanation": "简要说明"
    }
  ],
  "summary": "整体评估摘要",
  "recommendations": ["建议1", "建议2"]
}
"""

async def analyze_report(file_path: str, file_type: str) -> dict:
    """使用 Gemini 分析化验单"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # 读取文件
    if file_type in [".jpg", ".jpeg", ".png"]:
        with open(file_path, "rb") as f:
            image_data = f.read()
        response = model.generate_content([
            REPORT_ANALYSIS_PROMPT,
            {"mime_type": f"image/{file_type[1:]}", "data": image_data}
        ])
    else:
        # PDF 处理（简化版，实际需要 pdf2image 转换）
        with open(file_path, "rb") as f:
            pdf_data = f.read()
        response = model.generate_content([
            REPORT_ANALYSIS_PROMPT,
            {"mime_type": "application/pdf", "data": pdf_data}
        ])
    
    # 解析 JSON 响应
    import json
    import re
    text = response.text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return {"error": "无法解析结果", "raw": text}
```

### Step 2.3: 添加分析端点

**文件：** `backend/app/routers/reports.py`

```python
from app.services.ai_service import analyze_report
from sqlalchemy.orm import Session
from app.core.database import get_db

@router.post("/{report_id}/analyze")
async def analyze_report_endpoint(
    report_id: str,
    db: Session = Depends(get_db)
):
    """分析化验单"""
    report = db.query(ReportAttachment).filter(ReportAttachment.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    
    # 调用 AI 分析
    result = await analyze_report(report.file_path, report.file_type)
    
    # 创建健康记录
    health_record = HealthRecord(
        cat_id=report.cat_id,
        type="checkup",
        title=f"化验单分析: {report.file_name}",
        ai_summary=result.get("summary", ""),
        actionable_advice=result.get("recommendations", [])
    )
    db.add(health_record)
    db.commit()
    db.refresh(health_record)
    
    # 添加指标
    for ind in result.get("indicators", []):
        indicator = HealthIndicator(
            record_id=health_record.id,
            name=ind["name"],
            display_name=ind["name"],
            value=float(ind["value"]) if ind.get("value") else None,
            unit=ind.get("unit", ""),
            is_abnormal=ind.get("status") != "normal",
            explanation=ind.get("explanation", "")
        )
        db.add(indicator)
    
    db.commit()
    
    return {
        "record_id": health_record.id,
        "analysis": result
    }
```

**验收：**
- [ ] POST /api/v1/reports/{id}/analyze 返回分析结果
- [ ] 结果保存到 HealthRecord 和 HealthIndicator
- [ ] 需要 GEMINI_API_KEY 环境变量

---

## Task 3: 前端拖拽上传组件

### Step 3.1: 安装依赖

```bash
cd frontend && npm install react-dropzone
```

### Step 3.2: 创建上传组件

**文件：** `frontend/src/components/UploadZone.tsx`

```tsx
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image } from 'lucide-react';

interface UploadZoneProps {
  onUpload: (files: File[]) => void;
  uploading?: boolean;
}

export default function UploadZone({ onUpload, uploading }: UploadZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onUpload(acceptedFiles);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.jpg', '.jpeg', '.png'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
      } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} disabled={uploading} />
      
      <div className="flex justify-center gap-4 mb-4">
        <FileText size={32} className="text-red-500" />
        <Image size={32} className="text-blue-500" />
      </div>
      
      {uploading ? (
        <p className="text-gray-500">上传中...</p>
      ) : isDragActive ? (
        <p className="text-blue-600">拖放文件到这里</p>
      ) : (
        <>
          <p className="text-gray-600 mb-2">
            拖拽文件到这里，或 <span className="text-blue-600">点击选择</span>
          </p>
          <p className="text-sm text-gray-400">
            支持 PDF、JPG、PNG，最大 10MB
          </p>
        </>
      )}
    </div>
  );
}
```

### Step 3.3: 添加上传 API

**文件：** `frontend/src/lib/api.ts`

```typescript
// 上传化验单
export const uploadReport = (catId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(`/reports/upload/${catId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};

// 获取猫咪的化验单列表
export const getReports = (catId: string) =>
  api.get(`/reports/cat/${catId}`).then(r => r.data);

// 分析化验单
export const analyzeReport = (reportId: string) =>
  api.post(`/reports/${reportId}/analyze`).then(r => r.data);
```

**验收：**
- [ ] 支持拖拽上传
- [ ] 显示上传进度
- [ ] 文件类型验证

---

## Task 4: 化验单结果展示页面

### Step 4.1: 创建 Reports 页面

**文件：** `frontend/src/pages/Reports.tsx`

```tsx
import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import UploadZone from '@/components/UploadZone';
import { getReports, uploadReport, analyzeReport } from '@/lib/api';
import { FileText, Loader2, Sparkles } from 'lucide-react';

interface OutletContext {
  selectedCatId: string | null;
}

export default function Reports() {
  const { selectedCatId } = useOutletContext<OutletContext>();
  const [reports, setReports] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState<string | null>(null);

  const loadReports = async () => {
    if (!selectedCatId) return;
    const data = await getReports(selectedCatId);
    setReports(data);
  };

  useEffect(() => {
    loadReports();
  }, [selectedCatId]);

  const handleUpload = async (files: File[]) => {
    if (!selectedCatId) return;
    setUploading(true);
    try {
      for (const file of files) {
        await uploadReport(selectedCatId, file);
      }
      loadReports();
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async (reportId: string) => {
    setAnalyzing(reportId);
    try {
      await analyzeReport(reportId);
      loadReports();
    } finally {
      setAnalyzing(null);
    }
  };

  if (!selectedCatId) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-500">请先在侧边栏选择一只猫咪</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">化验报告</h2>

      {/* Upload Zone */}
      <div className="mb-8">
        <UploadZone onUpload={handleUpload} uploading={uploading} />
      </div>

      {/* Reports List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reports.map(report => (
          <div key={report.id} className="bg-white rounded-lg p-4 shadow-sm border">
            <div className="flex items-start gap-3">
              <FileText className="text-gray-400" size={24} />
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{report.file_name}</p>
                <p className="text-sm text-gray-500">
                  {new Date(report.created_at).toLocaleDateString('zh-CN')}
                </p>
              </div>
            </div>
            
            <button
              onClick={() => handleAnalyze(report.id)}
              disabled={analyzing === report.id}
              className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {analyzing === reportId ? (
                <Loader2 className="animate-spin" size={16} />
              ) : (
                <Sparkles size={16} />
              )}
              {analyzing === reportId ? '分析中...' : 'AI 解读'}
            </button>
          </div>
        ))}
      </div>

      {reports.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          还没有上传化验单
        </div>
      )}
    </div>
  );
}
```

### Step 4.2: 更新路由

**文件：** `frontend/src/App.tsx`

```tsx
import Reports from './pages/Reports';

<Route path="reports" element={<Reports />} />
```

**验收：**
- [ ] 显示上传区域
- [ ] 显示化验单列表
- [ ] 点击 AI 解读按钮调用分析

---

## Task 5: 悬浮对话助手

### Step 5.1: 创建 Chat 组件

**文件：** `frontend/src/components/ChatAssistant.tsx`

```tsx
import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '你好！我是 MeowHealth AI 助手，有什么可以帮助你的吗？' }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    
    // TODO: 调用后端 API
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '这是一个示例回复。实际功能需要接入后端 API。' 
      }]);
    }, 1000);
  };

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 p-4 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors z-50"
        >
          <MessageCircle size={24} />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 border">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b bg-blue-600 text-white rounded-t-2xl">
            <h3 className="font-semibold">AI 助手</h3>
            <button onClick={() => setIsOpen(false)} className="hover:bg-blue-700 p-1 rounded">
              <X size={20} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] p-3 rounded-lg ${
                  msg.role === 'user' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="输入消息..."
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSend}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
```

### Step 5.2: 添加到 Layout

**文件：** `frontend/src/components/Layout.tsx`

```tsx
import ChatAssistant from './ChatAssistant';

// ... 在 return 中添加
<ChatAssistant />
```

**验收：**
- [ ] 右下角悬浮按钮
- [ ] 点击展开对话窗口
- [ ] 支持发送消息

---

## Task 6: 联调测试

### 测试清单

- [ ] 上传 PDF 文件成功
- [ ] 上传图片文件成功
- [ ] AI 分析返回结果
- [ ] 结果保存到数据库
- [ ] 前端显示分析结果
- [ ] 悬浮助手正常交互

### 环境变量

```bash
# backend/.env
GEMINI_API_KEY=your_api_key_here
```

---

## 依赖安装

```bash
# 后端
cd backend
pip install google-generativeai

# 前端
cd frontend
npm install react-dropzone
```

---

## 文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/app/core/config.py` | 新建 | 配置管理 |
| `backend/app/services/ai_service.py` | 新建 | Gemini 服务 |
| `backend/app/routers/reports.py` | 新建 | 报告路由 |
| `frontend/src/components/UploadZone.tsx` | 新建 | 上传组件 |
| `frontend/src/components/ChatAssistant.tsx` | 新建 | 对话助手 |
| `frontend/src/pages/Reports.tsx` | 新建 | 报告页面 |
| `frontend/src/App.tsx` | 修改 | 添加路由 |
| `frontend/src/Layout.tsx` | 修改 | 添加助手 |
| `frontend/src/lib/api.ts` | 修改 | 添加 API |
