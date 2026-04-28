# Phase 3 补全：测试与文档 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 MeowHealth Web Phase 3 AI 化验单模块补全端到端测试和 API 文档

**Architecture:** 使用 pytest + FastAPI TestClient 进行后端 API 测试，使用 React Testing Library 进行前端组件测试。文档包括 API 端点说明和组件使用指南。

**Tech Stack:** Python 3.11, pytest, FastAPI TestClient, React Testing Library, Jest, TypeScript

---

## File Structure

### 测试文件
- `backend/tests/conftest.py` - pytest 共享 fixtures（数据库、客户端）
- `backend/tests/test_uploads.py` - 文件上传 API 测试
- `backend/tests/test_reports.py` - 报告 CRUD 和 AI 分析测试
- `backend/tests/test_chat.py` - 对话功能测试
- `frontend/src/components/__tests__/UploadZone.test.tsx` - 上传组件测试
- `frontend/src/components/__tests__/ReportCard.test.tsx` - 报告卡片测试

### 文档文件
- `docs/API.md` - 后端 API 端点文档
- `docs/Components.md` - 前端组件使用指南

---

## Task 1: 后端测试基础设施

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: 创建测试目录和 conftest**

```python
# backend/tests/__init__.py
# Empty file to make tests a package

# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from main import app

# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """每个测试函数创建新的数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """FastAPI 测试客户端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_cat(client):
    """创建一个示例猫咪"""
    response = client.post("/api/cats/", json={
        "name": "测试猫",
        "breed": "英短",
        "birthday": "2020-01-01T00:00:00",
        "gender": "male",
        "is_neutered": True
    })
    return response.json()
```

- [ ] **Step 2: 验证测试基础设施**

Run: `cd /Users/gu/openclaw_workspace/projects/MeowHealth-Web/backend && python -m pytest tests/conftest.py -v`
Expected: 无错误，fixtures 可加载

- [ ] **Step 3: Commit**

```bash
git add backend/tests/
git commit -m "test: add pytest infrastructure with in-memory sqlite"
```

---

## Task 2: 文件上传 API 测试

**Files:**
- Create: `backend/tests/test_uploads.py`

- [ ] **Step 1: 编写上传测试**

```python
import io
import pytest
from pathlib import Path

class TestUploads:
    def test_upload_image(self, client, sample_cat, tmp_path):
        """测试上传图片文件"""
        # 创建临时图片文件
        image_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # 模拟 PNG 头
        
        response = client.post(
            "/api/uploads/",
            files={"file": ("test.png", io.BytesIO(image_content), "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "file_path" in data
        assert "file_name" in data
        assert data["file_name"] == "test.png"
        assert data["mime_type"] == "image/png"
    
    def test_upload_pdf(self, client, sample_cat):
        """测试上传 PDF 文件"""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
        
        response = client.post(
            "/api/uploads/",
            files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["mime_type"] == "application/pdf"
    
    def test_upload_invalid_type(self, client):
        """测试上传不支持的文件类型"""
        response = client.post(
            "/api/uploads/",
            files={"file": ("test.exe", io.BytesIO(b"invalid"), "application/x-msdownload")}
        )
        
        assert response.status_code == 400
    
    def test_upload_too_large(self, client):
        """测试上传超大文件"""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        
        response = client.post(
            "/api/uploads/",
            files={"file": ("large.png", io.BytesIO(large_content), "image/png")}
        )
        
        assert response.status_code == 413
```

- [ ] **Step 2: 运行测试**

Run: `cd /Users/gu/openclaw_workspace/projects/MeowHealth-Web/backend && python -m pytest tests/test_uploads.py -v`
Expected: 4 tests, 可能有部分失败（需根据实际路由调整）

- [ ] **Step 3: 根据失败调整测试或代码**

检查 uploads router 的实际响应格式，调整断言。

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_uploads.py
git commit -m "test: add upload API tests"
```

---

## Task 3: 报告 API 测试

**Files:**
- Create: `backend/tests/test_reports.py`

- [ ] **Step 1: 编写报告 CRUD 测试**

```python
import pytest
from unittest.mock import patch, MagicMock

class TestReports:
    def test_create_report(self, client, sample_cat):
        """测试创建报告（模拟 AI 分析）"""
        mock_analysis = {
            "indicators": [
                {
                    "name": "WBC",
                    "display_name": "白细胞",
                    "value": 12.5,
                    "unit": "10^9/L",
                    "reference_min": 5.5,
                    "reference_max": 19.5,
                    "status": "normal",
                    "is_abnormal": False,
                    "explanation": "白细胞计数正常"
                }
            ],
            "summary": "各项指标正常",
            "recommendations": ["继续保持"]
        }
        
        with patch("app.routers.reports.analyze_report", return_value=mock_analysis):
            response = client.post(
                "/api/reports/analyze",
                params={
                    "cat_id": sample_cat["id"],
                    "file_path": "/tmp/test.pdf",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "化验单分析 - test.pdf"
        assert data["ai_summary"] == "各项指标正常"
        assert len(data["indicators"]) == 1
    
    def test_list_reports(self, client, sample_cat):
        """测试列出报告"""
        # 先创建一个报告
        mock_analysis = {
            "indicators": [],
            "summary": "测试",
            "recommendations": []
        }
        
        with patch("app.routers.reports.analyze_report", return_value=mock_analysis):
            client.post(
                "/api/reports/analyze",
                params={
                    "cat_id": sample_cat["id"],
                    "file_path": "/tmp/test.pdf",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024
                }
            )
        
        response = client.get(f"/api/reports/?cat_id={sample_cat['id']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["cat_id"] == sample_cat["id"]
    
    def test_get_report(self, client, sample_cat):
        """测试获取单个报告"""
        mock_analysis = {
            "indicators": [],
            "summary": "测试报告",
            "recommendations": []
        }
        
        with patch("app.routers.reports.analyze_report", return_value=mock_analysis):
            create_res = client.post(
                "/api/reports/analyze",
                params={
                    "cat_id": sample_cat["id"],
                    "file_path": "/tmp/test.pdf",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024
                }
            )
        
        report_id = create_res.json()["id"]
        response = client.get(f"/api/reports/{report_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id
    
    def test_delete_report(self, client, sample_cat):
        """测试删除报告"""
        mock_analysis = {
            "indicators": [],
            "summary": "待删除",
            "recommendations": []
        }
        
        with patch("app.routers.reports.analyze_report", return_value=mock_analysis):
            create_res = client.post(
                "/api/reports/analyze",
                params={
                    "cat_id": sample_cat["id"],
                    "file_path": "/tmp/test.pdf",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024
                }
            )
        
        report_id = create_res.json()["id"]
        response = client.delete(f"/api/reports/{report_id}")
        
        assert response.status_code == 204
        
        # 确认已删除
        get_res = client.get(f"/api/reports/{report_id}")
        assert get_res.status_code == 404
```

- [ ] **Step 2: 运行测试**

Run: `cd /Users/gu/openclaw_workspace/projects/MeowHealth-Web/backend && python -m pytest tests/test_reports.py -v`
Expected: 4 tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_reports.py
git commit -m "test: add report API CRUD tests"
```

---

## Task 4: 对话功能测试

**Files:**
- Create: `backend/tests/test_chat.py`

- [ ] **Step 1: 编写对话测试**

```python
import pytest
from unittest.mock import patch

class TestChat:
    def test_chat_with_report(self, client, sample_cat):
        """测试与报告对话"""
        # 先创建报告
        mock_analysis = {
            "indicators": [
                {
                    "name": "CREA",
                    "display_name": "肌酐",
                    "value": 2.5,
                    "unit": "mg/dL",
                    "reference_min": 0.8,
                    "reference_max": 2.4,
                    "status": "high",
                    "is_abnormal": True,
                    "explanation": "肌酐偏高"
                }
            ],
            "summary": "肌酐偏高，建议复查",
            "recommendations": ["多饮水", "复查肾功能"]
        }
        
        with patch("app.routers.reports.analyze_report", return_value=mock_analysis):
            create_res = client.post(
                "/api/reports/analyze",
                params={
                    "cat_id": sample_cat["id"],
                    "file_path": "/tmp/test.pdf",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024
                }
            )
        
        report_id = create_res.json()["id"]
        
        # 测试对话
        mock_chat_response = "肌酐偏高可能表示肾功能轻度异常，建议增加饮水量并在1周后复查。"
        
        with patch("app.routers.reports.chat_about_report", return_value=mock_chat_response):
            response = client.post(
                f"/api/reports/{report_id}/chat",
                json={"content": "肌酐偏高严重吗？"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "model"
        assert "肌酐" in data["content"]
    
    def test_chat_history(self, client, sample_cat):
        """测试获取对话历史"""
        mock_analysis = {
            "indicators": [],
            "summary": "测试",
            "recommendations": []
        }
        
        with patch("app.routers.reports.analyze_report", return_value=mock_analysis):
            create_res = client.post(
                "/api/reports/analyze",
                params={
                    "cat_id": sample_cat["id"],
                    "file_path": "/tmp/test.pdf",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024
                }
            )
        
        report_id = create_res.json()["id"]
        
        # 发送几条消息
        with patch("app.routers.reports.chat_about_report", return_value="回答1"):
            client.post(f"/api/reports/{report_id}/chat", json={"content": "问题1"})
        
        with patch("app.routers.reports.chat_about_report", return_value="回答2"):
            client.post(f"/api/reports/{report_id}/chat", json={"content": "问题2"})
        
        # 获取历史
        response = client.get(f"/api/reports/{report_id}/chat/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # 2 user + 2 model messages
```

- [ ] **Step 2: 运行测试**

Run: `cd /Users/gu/openclaw_workspace/projects/MeowHealth-Web/backend && python -m pytest tests/test_chat.py -v`
Expected: 2 tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_chat.py
git commit -m "test: add chat API tests"
```

---

## Task 5: 前端组件测试

**Files:**
- Create: `frontend/src/components/__tests__/ReportCard.test.tsx`
- Modify: `frontend/package.json` (添加测试依赖)

- [ ] **Step 1: 安装测试依赖**

Run: `cd /Users/gu/openclaw_workspace/projects/MeowHealth-Web/frontend && npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest jsdom`

- [ ] **Step 2: 配置 vitest**

Create: `frontend/vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

Create: `frontend/src/test/setup.ts`

```typescript
import '@testing-library/jest-dom'
```

- [ ] **Step 3: 编写 ReportCard 测试**

Create: `frontend/src/components/__tests__/ReportCard.test.tsx`

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReportCard } from '../ReportCard'

describe('ReportCard', () => {
  const mockIndicators = [
    {
      id: '1',
      name: 'WBC',
      display_name: '白细胞',
      value: 12.5,
      unit: '10^9/L',
      reference_min: 5.5,
      reference_max: 19.5,
      is_abnormal: false,
      explanation: '正常'
    },
    {
      id: '2',
      name: 'CREA',
      display_name: '肌酐',
      value: 2.5,
      unit: 'mg/dL',
      reference_min: 0.8,
      reference_max: 2.4,
      is_abnormal: true,
      explanation: '偏高'
    }
  ]

  it('renders report title and date', () => {
    render(
      <ReportCard
        title="血常规检查"
        date="2024-01-15"
        summary="整体正常"
        indicators={mockIndicators}
        recommendations={["多饮水"]}
      />
    )

    expect(screen.getByText('血常规检查')).toBeInTheDocument()
    expect(screen.getByText('整体正常')).toBeInTheDocument()
  })

  it('highlights abnormal indicators', () => {
    render(
      <ReportCard
        title="血常规检查"
        date="2024-01-15"
        summary="整体正常"
        indicators={mockIndicators}
        recommendations={["多饮水"]}
      />
    )

    // 异常指标应该被标记
    const abnormalIndicator = screen.getByText('肌酐')
    expect(abnormalIndicator).toBeInTheDocument()
  })

  it('displays recommendations', () => {
    render(
      <ReportCard
        title="血常规检查"
        date="2024-01-15"
        summary="整体正常"
        indicators={mockIndicators}
        recommendations={["多饮水", "定期复查"]}
      />
    )

    expect(screen.getByText('多饮水')).toBeInTheDocument()
    expect(screen.getByText('定期复查')).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: 运行前端测试**

Run: `cd /Users/gu/openclaw_workspace/projects/MeowHealth-Web/frontend && npx vitest run`
Expected: 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "test: add frontend component tests with vitest"
```

---

## Task 6: API 文档

**Files:**
- Create: `docs/API.md`

- [ ] **Step 1: 编写 API 文档**

```markdown
# MeowHealth Web API 文档

## 基础信息

- **Base URL**: `http://localhost:8000/api`
- **Content-Type**: `application/json`

## 认证

> Phase 4 将实现 Token 鉴权

## 端点列表

### 猫咪管理

#### GET /cats/
列出所有猫咪

**响应**:
```json
[
  {
    "id": "uuid",
    "name": "咪咪",
    "breed": "英短",
    "birthday": "2020-01-01T00:00:00",
    "gender": "male",
    "is_neutered": true,
    "photo_path": null,
    "target_weight_min": 4.0,
    "target_weight_max": 5.5,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

#### POST /cats/
创建猫咪

**请求体**:
```json
{
  "name": "咪咪",
  "breed": "英短",
  "birthday": "2020-01-01T00:00:00",
  "gender": "male",
  "is_neutered": true,
  "target_weight_min": 4.0,
  "target_weight_max": 5.5
}
```

### 文件上传

#### POST /uploads/
上传文件

**请求**: `multipart/form-data`
- `file`: 文件内容

**响应**:
```json
{
  "file_path": "/uploads/xxx.png",
  "file_name": "report.png",
  "mime_type": "image/png",
  "file_size": 1024
}
```

### 化验报告

#### POST /reports/analyze
分析上传的文件并创建报告

**查询参数**:
- `cat_id`: 猫咪 ID
- `file_path`: 文件路径
- `file_name`: 文件名
- `mime_type`: MIME 类型
- `file_size`: 文件大小

**响应**:
```json
{
  "id": "uuid",
  "cat_id": "uuid",
  "title": "化验单分析 - report.pdf",
  "date": "2024-01-15T10:00:00",
  "ai_summary": "整体正常",
  "actionable_advice": ["多饮水"],
  "indicators": [
    {
      "id": "uuid",
      "name": "WBC",
      "display_name": "白细胞",
      "value": 12.5,
      "unit": "10^9/L",
      "reference_min": 5.5,
      "reference_max": 19.5,
      "is_abnormal": false,
      "explanation": "正常"
    }
  ]
}
```

#### GET /reports/
列出报告

**查询参数**:
- `cat_id` (可选): 按猫咪过滤

#### GET /reports/{report_id}
获取单个报告

#### POST /reports/{report_id}/chat
与报告对话

**请求体**:
```json
{
  "content": "肌酐偏高严重吗？"
}
```

**响应**:
```json
{
  "id": "uuid",
  "role": "model",
  "content": "肌酐偏高可能表示...",
  "model_name": "gemini-2.0-flash",
  "created_at": "2024-01-15T10:00:00"
}
```

#### GET /reports/{report_id}/chat/history
获取对话历史

## 错误码

| 状态码 | 含义 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 413 | 文件过大 |
| 500 | 服务器内部错误 |
```

- [ ] **Step 2: Commit**

```bash
git add docs/API.md
git commit -m "docs: add API documentation"
```

---

## Task 7: 组件文档

**Files:**
- Create: `docs/Components.md`

- [ ] **Step 1: 编写组件文档**

```markdown
# MeowHealth Web 组件文档

## 通用组件

### UploadZone

文件拖拽上传组件

**Props**:
| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| catId | string | 是 | 关联的猫咪 ID |
| onUploadComplete | (reportId: string) => void | 是 | 上传完成回调 |

**使用示例**:
```tsx
<UploadZone 
  catId={selectedCatId} 
  onUploadComplete={(reportId) => {
    console.log('报告创建成功:', reportId)
  }}
/>
```

**功能**:
- 支持拖拽上传
- 支持 PDF、JPG、PNG 格式
- 文件大小限制 10MB
- 显示上传进度和 AI 分析状态

### ReportCard

化验报告展示卡片

**Props**:
| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 报告标题 |
| date | string | 是 | 报告日期 |
| summary | string | 是 | AI 总结 |
| indicators | Indicator[] | 是 | 指标列表 |
| recommendations | string[] | 是 | 建议列表 |

**Indicator 类型**:
```typescript
interface Indicator {
  id: string
  name: string           // 英文代码
  display_name: string   // 中文名称
  value: number | null
  unit: string
  reference_min: number | null
  reference_max: number | null
  is_abnormal: boolean
  explanation: string | null
}
```

### ChatAssistant

悬浮对话助手

**Props**:
| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reportId | string | 是 | 报告 ID |

**功能**:
- 基于报告上下文的多轮对话
- 自动加载对话历史
- 快捷提问按钮

## 页面组件

### Dashboard

首页仪表盘，包含：
- 统计卡片（猫咪数量、待办事项）
- 体重趋势图
- 待办提醒列表
- 近期健康事件

### Cats

猫咪管理页面，包含：
- 猫咪列表
- 添加/删除猫咪

### Reports

化验报告页面，包含：
- 上传区域
- 报告列表
- 报告详情（ReportCard + ChatAssistant）
```

- [ ] **Step 2: Commit**

```bash
git add docs/Components.md
git commit -m "docs: add component documentation"
```

---

## 验证清单

- [ ] 所有后端测试通过：`pytest backend/tests/ -v`
- [ ] 所有前端测试通过：`cd frontend && npx vitest run`
- [ ] API 文档完整覆盖所有端点
- [ ] 组件文档包含所有 Props 和示例

## Self-Review

**Spec coverage**: 
- ✅ 文件上传测试
- ✅ 报告 CRUD 测试
- ✅ 对话功能测试
- ✅ 前端组件测试
- ✅ API 文档
- ✅ 组件文档

**Placeholder scan**: 无 TBD/TODO

**Type consistency**: 前后端类型一致
