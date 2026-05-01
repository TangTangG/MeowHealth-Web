import pytest
from unittest.mock import patch, MagicMock
from app.ai.subagents.history_agent import HistoryAnalystAgent


class TestHistoryAnalystAgent:
    def setup_method(self):
        with patch("app.ai.subagents.history_agent.genai"):
            self.agent = HistoryAnalystAgent("test-api-key")

    def test_no_history_records(self):
        """无历史记录时应返回首次分析提示"""
        result = self.agent.analyze(
            cat_profile={"breed": "中华田园猫"},
            history_records=[],
            current_data={"indicators": [{"name": "CREA", "value": 150}]}
        )
        
        assert result["trends"] == []
        assert result["warnings"] == []
        assert "首次分析" in result["historical_context"]

    def test_with_history_records(self):
        """有历史记录时应返回趋势分析"""
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "trends": [
                {"indicator": "CREA", "values": [120, 145, 180], "dates": ["2026-02", "2026-03", "2026-04"], "direction": "rising", "concern": "high"}
            ],
            "warnings": ["肌酐持续升高，提示肾功能可能进行性下降"],
            "historical_context": "该猫近3个月肾功能指标呈上升趋势"
        }
        '''
        with patch.object(self.agent.model, "generate_content", return_value=mock_response):
            result = self.agent.analyze(
                cat_profile={"breed": "布偶猫"},
                history_records=[
                    {"date": "2026-02-01", "summary": "正常", "indicators": [{"name": "CREA", "value": 120}]},
                    {"date": "2026-03-01", "summary": "轻度异常", "indicators": [{"name": "CREA", "value": 145}]}
                ],
                current_data={"indicators": [{"name": "CREA", "value": 180}]}
            )
        
        assert len(result["trends"]) > 0
        assert result["trends"][0]["direction"] == "rising"
        assert len(result["warnings"]) > 0

    def test_api_failure_graceful_degradation(self):
        """API 调用失败时应降级处理"""
        with patch.object(self.agent.model, "generate_content", side_effect=Exception("API Error")):
            result = self.agent.analyze(
                cat_profile={"breed": "测试"},
                history_records=[{"date": "2026-01-01", "summary": "测试", "indicators": []}],
                current_data={"indicators": []}
            )
        
        assert result["trends"] == []
        assert "不可用" in result["historical_context"]
