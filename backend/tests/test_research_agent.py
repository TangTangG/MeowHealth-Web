import pytest
from unittest.mock import patch, MagicMock
from app.ai.subagents.research_agent import ResearchAgent


class TestResearchAgent:
    def setup_method(self):
        with patch("app.ai.subagents.research_agent.genai"):
            self.agent = ResearchAgent("test-api-key")

    def test_no_unmatched_indicators(self):
        """无未匹配指标时应返回空结果"""
        result = self.agent.research(unmatched_indicators=[])
        
        assert result["supplementary_findings"] == []
        assert result["literature_notes"] == []

    def test_with_unmatched_indicators(self):
        """有未匹配指标时应返回补充研究"""
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "supplementary_findings": [
                {"indicator": "GGT", "finding": "GGT升高通常提示胆汁淤积或胆管损伤", "follow_up": "建议复查肝功能全套+腹部B超"}
            ],
            "literature_notes": ["GGT是胆管损伤的敏感指标"]
        }
        '''
        with patch.object(self.agent.model, "generate_content", return_value=mock_response):
            result = self.agent.research(
                unmatched_indicators=[
                    {"name": "GGT", "display_name": "谷氨酰转肽酶", "value": 85, "status": "high"}
                ],
                breed_context="布偶猫"
            )
        
        assert len(result["supplementary_findings"]) > 0
        assert result["supplementary_findings"][0]["indicator"] == "GGT"

    def test_api_failure_graceful_degradation(self):
        """API 调用失败时应降级处理"""
        with patch.object(self.agent.model, "generate_content", side_effect=Exception("API Error")):
            result = self.agent.research(
                unmatched_indicators=[{"name": "TEST", "value": 100}]
            )
        
        assert result["supplementary_findings"] == []
        assert result["literature_notes"] == []
