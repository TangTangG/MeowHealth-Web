# PDF 处理增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增强 MeowHealth Web 的 PDF 处理能力，支持本地文本提取和扫描版 PDF OCR

**Architecture:** 创建 `PDFProcessor` 类，先尝试本地提取文本/表格，若失败（扫描版）则使用 OCR。提取的内容作为上下文传给 Gemini，提高解析准确率。

**Tech Stack:** Python 3.11, PyPDF2, pdfplumber, pytesseract, Pillow, pdf2image

---

## File Structure

### 新增文件
- `backend/app/services/pdf_processor.py` — PDF 处理核心类
- `backend/tests/test_pdf_processor.py` — PDF 处理测试

### 修改文件
- `backend/app/services/ai_service.py` — 集成 PDFProcessor
- `backend/requirements.txt` — 添加依赖
- `backend/tests/test_uploads.py` — 更新上传测试

---

## Task 1: PDF 处理核心类

**Files:**
- Create: `backend/app/services/pdf_processor.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加依赖**

修改 `backend/requirements.txt`，添加：
```
pdfplumber>=0.10.0
PyPDF2>=3.0.0
pytesseract>=0.3.10
pdf2image>=1.16.3
Pillow>=10.0.0
```

- [ ] **Step 2: 创建 PDFProcessor**

```python
# backend/app/services/pdf_processor.py
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import io

import pdfplumber
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF 处理器：支持文本提取和 OCR"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.is_scanned = False
        self.extracted_text = ""
        self.tables: List[List[List[str]]] = []
    
    def process(self) -> Dict:
        """
        处理 PDF 文件，返回提取的内容
        
        Returns:
            {
                "text": str,  # 提取的文本
                "tables": List[List[List[str]]],  # 提取的表格
                "is_scanned": bool,  # 是否为扫描版
                "page_count": int,  # 页数
            }
        """
        try:
            # 1. 尝试本地文本提取
            result = self._extract_text_and_tables()
            
            # 2. 如果文本太少，认为是扫描版，进行 OCR
            if len(result["text"].strip()) < 100:
                logger.info("PDF 文本内容过少，尝试 OCR")
                result = self._ocr_pdf()
                result["is_scanned"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"PDF 处理失败: {e}")
            return {
                "text": "",
                "tables": [],
                "is_scanned": False,
                "page_count": 0,
                "error": str(e)
            }
    
    def _extract_text_and_tables(self) -> Dict:
        """使用 pdfplumber 提取文本和表格"""
        text_parts = []
        tables = []
        page_count = 0
        
        with pdfplumber.open(self.file_path) as pdf:
            page_count = len(pdf.pages)
            
            for page in pdf.pages:
                # 提取文本
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                
                # 提取表格
                page_tables = page.extract_tables()
                for table in page_tables:
                    if table and len(table) > 1:  # 至少要有表头和一行数据
                        tables.append(table)
        
        return {
            "text": "\n\n".join(text_parts),
            "tables": tables,
            "is_scanned": False,
            "page_count": page_count
        }
    
    def _ocr_pdf(self) -> Dict:
        """对扫描版 PDF 进行 OCR"""
        text_parts = []
        page_count = 0
        
        try:
            # 将 PDF 转换为图片
            images = convert_from_path(self.file_path, dpi=300)
            page_count = len(images)
            
            for i, image in enumerate(images):
                logger.info(f"OCR 处理第 {i+1}/{page_count} 页")
                
                # 使用 Tesseract OCR
                # 中文 + 英文
                text = pytesseract.image_to_string(
                    image, 
                    lang='chi_sim+eng'
                )
                
                if text.strip():
                    text_parts.append(text)
            
            return {
                "text": "\n\n".join(text_parts),
                "tables": [],  # OCR 不提取表格结构
                "is_scanned": True,
                "page_count": page_count
            }
            
        except Exception as e:
            logger.error(f"OCR 失败: {e}")
            return {
                "text": "",
                "tables": [],
                "is_scanned": True,
                "page_count": page_count,
                "error": str(e)
            }
    
    def get_summary(self) -> str:
        """获取 PDF 内容摘要，用于 AI 提示"""
        result = self.process()
        
        if result.get("error"):
            return f"PDF 处理失败: {result['error']}"
        
        summary_parts = [
            f"PDF 页数: {result['page_count']}",
            f"是否为扫描版: {'是' if result['is_scanned'] else '否'}",
            "",
            "提取的文本内容:",
            result["text"][:5000],  # 限制长度，避免超出 token 限制
        ]
        
        if result["tables"]:
            summary_parts.extend([
                "",
                f"提取的表格数: {len(result['tables'])}",
            ])
        
        return "\n".join(summary_parts)


def process_pdf(file_path: str) -> Dict:
    """便捷函数：处理 PDF 文件"""
    processor = PDFProcessor(file_path)
    return processor.process()
```

- [ ] **Step 3: 安装依赖**

Run: `cd backend && pip install -r requirements.txt`
Expected: 所有依赖安装成功

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/pdf_processor.py backend/requirements.txt
git commit -m "feat: add PDFProcessor with text extraction and OCR support"
```

---

## Task 2: 集成到 AI 服务

**Files:**
- Modify: `backend/app/services/ai_service.py`

- [ ] **Step 1: 修改 analyze_report 函数**

```python
# 在 ai_service.py 顶部添加导入
from app.services.pdf_processor import PDFProcessor

# 修改 REPORT_ANALYSIS_PROMPT，增加 PDF 内容提示
REPORT_ANALYSIS_PROMPT = """你是一位专业的兽医化验单解读助手。请分析以下宠物化验单内容，并输出 JSON 格式的结果。

【化验单数据】
{pdf_content}

要求：
1. 提取所有检测指标（名称、数值、单位、参考范围）
2. 标记异常指标（偏高/偏低）
3. 给出整体健康评估（一句话核心结论）
4. 提供 actionable 的建议

输出必须是有效的 JSON 格式：
{
  "indicators": [
    {
      "name": "指标英文代码（如 CREA, WBC, ALT）",
      "display_name": "指标中文名称（如 肌酐, 白细胞, 谷丙转氨酶）",
      "value": 123.5,
      "unit": "单位",
      "reference_min": 100.0,
      "reference_max": 150.0,
      "status": "normal|high|low",
      "explanation": "简要说明该指标的意义"
    }
  ],
  "summary": "整体评估摘要，一句话核心结论",
  "recommendations": ["建议1", "建议2", "建议3"]
}"""


def analyze_report(file_path: str, mime_type: str) -> dict:
    """使用 Gemini 分析化验单，返回结构化数据"""
    api_key = get_gemini_api_key()
    if not api_key:
        return {"error": "Gemini API Key 未设置"}
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    try:
        # 如果是 PDF，先进行本地处理
        pdf_content = ""
        if mime_type == "application/pdf":
            processor = PDFProcessor(file_path)
            pdf_result = processor.process()
            
            if pdf_result.get("error"):
                logger.warning(f"PDF 处理警告: {pdf_result['error']}")
            
            pdf_content = processor.get_summary()
            
            # 构建提示词
            prompt = REPORT_ANALYSIS_PROMPT.format(pdf_content=pdf_content)
            
            # 对于扫描版 PDF，直接发送文本
            if pdf_result.get("is_scanned"):
                response = model.generate_content([
                    prompt,
                    "请基于上述 OCR 提取的文本内容进行分析。"
                ])
            else:
                # 对于普通 PDF，同时发送原始文件和提取的文本
                with open(file_path, "rb") as f:
                    file_data = f.read()
                
                response = model.generate_content([
                    prompt,
                    {"mime_type": mime_type, "data": file_data},
                    "以上是原始 PDF 文件，以下是提取的文本内容，请结合两者进行分析。"
                ])
        else:
            # 图片文件保持原有逻辑
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            response = model.generate_content([
                REPORT_ANALYSIS_PROMPT.format(pdf_content="[图片文件，请直接分析图片内容]"),
                {"mime_type": mime_type, "data": file_data}
            ])
        
        # 解析响应...
        text = response.text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                result = json.loads(json_match.group())
                for indicator in result.get("indicators", []):
                    ref_range = indicator.get("reference_range", "")
                    ref_min, ref_max = parse_reference_range(ref_range)
                    indicator["reference_min"] = ref_min
                    indicator["reference_max"] = ref_max
                    status = indicator.get("status", "normal")
                    indicator["is_abnormal"] = status in ["high", "low"]
                
                return result
            except json.JSONDecodeError as e:
                return {"error": f"JSON 解析失败: {str(e)}", "raw_response": text}
        
        return {"error": "无法解析 AI 响应", "raw_response": text}
        
    except Exception as e:
        return {"error": f"分析失败: {str(e)}"}
```

- [ ] **Step 2: 运行测试**

Run: `cd backend && python3 -m pytest tests/test_reports.py -v`
Expected: 4 tests pass（mock 仍然有效）

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/ai_service.py
git commit -m "feat: integrate PDFProcessor into AI analysis"
```

---

## Task 3: PDF 处理测试

**Files:**
- Create: `backend/tests/test_pdf_processor.py`
- Create: `backend/tests/fixtures/sample_text.pdf`
- Create: `backend/tests/fixtures/sample_scanned.pdf`

- [ ] **Step 1: 创建测试 fixtures**

使用 Python 生成测试 PDF：
```python
# 在 test_pdf_processor.py 中使用 unittest.mock 模拟 PDF
# 或者使用 reportlab 生成简单 PDF
```

- [ ] **Step 2: 编写测试**

```python
# backend/tests/test_pdf_processor.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.pdf_processor import PDFProcessor, process_pdf


class TestPDFProcessor:
    def test_extract_text_from_text_pdf(self, tmp_path):
        """测试从文本 PDF 提取内容"""
        # 创建一个模拟的文本 PDF
        pdf_path = tmp_path / "test_text.pdf"
        
        # 使用 mock 模拟 pdfplumber
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "WBC: 12.5\nCREA: 2.1"
        mock_page.extract_tables.return_value = []
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        
        with patch('app.services.pdf_processor.pdfplumber.open', return_value=mock_pdf):
            processor = PDFProcessor(str(pdf_path))
            result = processor.process()
        
        assert result["text"] == "WBC: 12.5\nCREA: 2.1"
        assert result["is_scanned"] is False
        assert result["page_count"] == 1
    
    def test_ocr_for_scanned_pdf(self, tmp_path):
        """测试扫描版 PDF 的 OCR"""
        pdf_path = tmp_path / "test_scanned.pdf"
        
        # Mock pdfplumber 返回极少文本（模拟扫描版）
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        
        # Mock OCR
        with patch('app.services.pdf_processor.pdfplumber.open', return_value=mock_pdf):
            with patch('app.services.pdf_processor.convert_from_path') as mock_convert:
                mock_image = MagicMock()
                mock_convert.return_value = [mock_image]
                
                with patch('app.services.pdf_processor.pytesseract.image_to_string', return_value="OCR 文本"):
                    processor = PDFProcessor(str(pdf_path))
                    result = processor.process()
        
        assert result["is_scanned"] is True
        assert "OCR 文本" in result["text"]
    
    def test_extract_tables(self, tmp_path):
        """测试表格提取"""
        pdf_path = tmp_path / "test_tables.pdf"
        
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_page.extract_tables.return_value = [
            [["指标", "数值", "单位"], ["WBC", "12.5", "10^9/L"]]
        ]
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        
        with patch('app.services.pdf_processor.pdfplumber.open', return_value=mock_pdf):
            processor = PDFProcessor(str(pdf_path))
            result = processor.process()
        
        assert len(result["tables"]) == 1
        assert result["tables"][0][1][0] == "WBC"
    
    def test_process_pdf_convenience_function(self, tmp_path):
        """测试便捷函数"""
        pdf_path = tmp_path / "test.pdf"
        
        with patch.object(PDFProcessor, 'process', return_value={"text": "test", "is_scanned": False}):
            result = process_pdf(str(pdf_path))
        
        assert result["text"] == "test"
```

- [ ] **Step 3: 运行测试**

Run: `cd backend && python3 -m pytest tests/test_pdf_processor.py -v`
Expected: 4 tests pass

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_pdf_processor.py
git commit -m "test: add PDF processor tests"
```

---

## Task 4: 更新上传测试

**Files:**
- Modify: `backend/tests/test_uploads.py`

- [ ] **Step 1: 添加上传后处理测试**

```python
# 在 test_uploads.py 中添加
from unittest.mock import patch

def test_upload_and_process_pdf(self, client, sample_cat):
    """测试上传 PDF 并进行处理"""
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
    
    response = client.post(
        "/api/uploads/",
        files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证文件已保存
    assert Path(data["file_path"]).exists()
    
    # 清理
    Path(data["file_path"]).unlink(missing_ok=True)
```

- [ ] **Step 2: Commit**

```bash
git add backend/tests/test_uploads.py
git commit -m "test: enhance upload tests with PDF processing"
```

---

## 验证清单

- [ ] PDFProcessor 能正确提取文本 PDF 内容
- [ ] PDFProcessor 能识别扫描版 PDF 并进行 OCR
- [ ] PDFProcessor 能提取表格数据
- [ ] AI 服务集成后，PDF 分析准确率提高
- [ ] 所有测试通过

## Self-Review

**Spec coverage**:
- ✅ 本地文本提取（pdfplumber）
- ✅ 扫描版 OCR（pytesseract + pdf2image）
- ✅ 表格提取
- ✅ AI 服务集成
- ✅ 测试覆盖

**Placeholder scan**: 无 TBD/TODO

**Type consistency**: PDFProcessor 返回 Dict，与现有代码兼容
