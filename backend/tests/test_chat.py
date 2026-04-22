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
        
        # 测试对话
        mock_chat_response = "肌酐偏高可能表示肾功能轻度异常，建议增加饮水量并在1周后复查。"
        
        with patch("app.routers.reports.chat_about_report", return_value=mock_chat_response):
            response = client.post(
                f"/api/v1/api/reports/{report_id}/chat",
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
        
        # 发送几条消息
        with patch("app.routers.reports.chat_about_report", return_value="回答1"):
            client.post(f"/api/v1/api/reports/{report_id}/chat", json={"content": "问题1"})
        
        with patch("app.routers.reports.chat_about_report", return_value="回答2"):
            client.post(f"/api/v1/api/reports/{report_id}/chat", json={"content": "问题2"})
        
        # 获取历史
        response = client.get(f"/api/v1/api/reports/{report_id}/chat/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # 2 user + 2 model messages
