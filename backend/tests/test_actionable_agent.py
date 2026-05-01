import pytest
from unittest.mock import patch, MagicMock
from app.ai.subagents.actionable_agent import ActionableAgent


class TestActionableAgent:
    def setup_method(self):
        with patch("app.ai.subagents.actionable_agent.genai"):
            self.agent = ActionableAgent("test-api-key")

    def test_no_abnormals_returns_empty(self):
        """无异常指标时应返回空结果"""
        result = self.agent.generate_actions(
            summary="一切正常",
            abnormals=[],
            recommendations=["保持良好饮食"],
            cat_profile={"breed": "中华田园猫"}
        )
        
        assert result["reminders"] == []
        assert result["shopping_list"] == []

    def test_generate_reminders_and_shopping_list(self):
        """有异常指标时应生成提醒和购物清单"""
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "reminders": [
                {"title": "复查肾功能", "description": "需复查 CREA、BUN", "days_from_now": 30, "reminder_type": "vet_visit"}
            ],
            "shopping_list": [
                {"item": "肾脏处方粮", "reason": "CREA 偏高", "priority": "high"}
            ]
        }
        '''
        with patch.object(self.agent.model, "generate_content", return_value=mock_response):
            result = self.agent.generate_actions(
                summary="肾功能异常",
                abnormals=[{"name": "CREA", "display_name": "肌酐", "value": 200, "unit": "umol/L"}],
                recommendations=["建议换肾脏处方粮"],
                cat_profile={"breed": "布偶猫", "name": "小花"}
            )
        
        assert len(result["reminders"]) > 0
        assert "复查" in result["reminders"][0]["title"]
        assert len(result["shopping_list"]) > 0
        assert "处方粮" in result["shopping_list"][0]["item"]

    def test_api_failure_graceful_degradation(self):
        """API 调用失败时应降级处理"""
        with patch.object(self.agent.model, "generate_content", side_effect=Exception("API Error")):
            result = self.agent.generate_actions(
                summary="测试",
                abnormals=[{"name": "TEST", "value": 100}],
                recommendations=["测试"],
                cat_profile={"breed": "测试"}
            )
        
        assert result["reminders"] == []
        assert result["shopping_list"] == []
