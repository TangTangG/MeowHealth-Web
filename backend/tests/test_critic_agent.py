import pytest
from unittest.mock import patch, MagicMock
from app.ai.subagents.critic_agent import CriticAgent


class TestCriticAgent:
    def setup_method(self):
        with patch("app.ai.subagents.critic_agent.genai"):
            self.agent = CriticAgent("test-api-key")

    def test_approved_no_conflicts(self):
        """无冲突时应返回 approved=True"""
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "approved": true,
            "flags": [],
            "revised_summary": "肝功能正常",
            "revised_recommendations": ["保持当前饮食"]
        }
        '''
        with patch.object(self.agent.model, "generate_content", return_value=mock_response):
            result = self.agent.review(
                lab_result={"summary": "肝功能正常", "indicators": []},
                recommendations=["保持当前饮食"],
                cat_profile={"breed": "中华田园猫", "weight_status": "normal"}
            )
        
        assert result["approved"] is True
        assert result["flags"] == []

    def test_not_approved_with_conflicts(self):
        """发现冲突时应返回 approved=False 和修正建议"""
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "approved": false,
            "flags": ["肝指标 ALT 偏高，但建议中未限制蛋白质摄入"],
            "revised_summary": "肝功能异常，建议调整饮食",
            "revised_recommendations": ["降低蛋白质摄入", "30天后复查肝功能"]
        }
        '''
        with patch.object(self.agent.model, "generate_content", return_value=mock_response):
            result = self.agent.review(
                lab_result={"summary": "肝功能异常", "indicators": [{"name": "ALT", "status": "high"}]},
                recommendations=["增加蛋白质摄入"],
                cat_profile={"breed": "布偶猫", "weight_status": "normal"}
            )
        
        assert result["approved"] is False
        assert len(result["flags"]) > 0
        assert "降低蛋白质" in result["revised_recommendations"][0]

    def test_api_failure_graceful_degradation(self):
        """API 调用失败时应默认通过，不阻塞流水线"""
        with patch.object(self.agent.model, "generate_content", side_effect=Exception("API Error")):
            result = self.agent.review(
                lab_result={"summary": "测试"},
                recommendations=["测试"],
                cat_profile={"breed": "测试"}
            )
        
        assert result["approved"] is True
        assert result["flags"] == []
