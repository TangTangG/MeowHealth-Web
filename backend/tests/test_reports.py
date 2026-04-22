import pytest
from unittest.mock import patch

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
                "/api/v1/api/reports/analyze",
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
                "/api/v1/api/reports/analyze",
                params={
                    "cat_id": sample_cat["id"],
                    "file_path": "/tmp/test.pdf",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024
                }
            )
        
        response = client.get(f"/api/v1/api/reports/?cat_id={sample_cat['id']}")
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
                "/api/v1/api/reports/analyze",
                params={
                    "cat_id": sample_cat["id"],
                    "file_path": "/tmp/test.pdf",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024
                }
            )
        
        report_id = create_res.json()["id"]
        response = client.get(f"/api/v1/api/reports/{report_id}")
        
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
                "/api/v1/api/reports/analyze",
                params={
                    "cat_id": sample_cat["id"],
                    "file_path": "/tmp/test.pdf",
                    "file_name": "test.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 1024
                }
            )
        
        report_id = create_res.json()["id"]
        response = client.delete(f"/api/v1/api/reports/{report_id}")
        
        assert response.status_code == 200
        
        # 确认已删除
        get_res = client.get(f"/api/v1/api/reports/{report_id}")
        assert get_res.status_code == 404
