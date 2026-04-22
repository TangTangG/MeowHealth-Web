import io
import pytest

class TestUploads:
    def test_upload_image(self, client, sample_cat, tmp_path):
        """测试上传图片文件"""
        # 创建临时图片文件（模拟 PNG 头）
        image_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        
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
        
        assert response.status_code == 400
