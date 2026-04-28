import pytest
from unittest.mock import patch, MagicMock
from app.ai.orchestrator import MedicalOrchestrator

@pytest.fixture
def mock_cat_profile_maine_coon_overweight():
    return {
        "breed": "Maine Coon",
        "weight_status": "overweight",
        "current_weight": 8.5
    }

@patch("app.ai.orchestrator.MedicalOrchestrator._load_skill")
@patch("app.ai.orchestrator.get_gemini_api_key")
@patch("app.ai.subagents.vision_agent.VisionAgent.extract")
@patch("app.ai.subagents.lab_analyzer.LabAnalyzer.analyze")
@patch("app.ai.subagents.dietitian_agent.DietitianAgent.prescribe")
@patch("builtins.open")
def test_orchestrator_pipeline_maine_coon(mock_open, mock_diet, mock_analyze, mock_extract, mock_get_api_key, mock_load_skill, mock_cat_profile_maine_coon_overweight):
    mock_get_api_key.return_value = "fake_key"
    
    # Mock specific skill loading
    def fake_load_skill(category, name):
        if category == "breeds" and "maine" in name.lower():
            return "缅因猫易感 HCM"
        if category == "weights" and name == "overweight":
            return "肥胖易感脂肪肝，绝对禁止断食"
        return "通用知识"
    mock_load_skill.side_effect = fake_load_skill

    # Mock file reading
    mock_file = MagicMock()
    mock_file.read.return_value = b"fake_image_data"
    mock_open.return_value.__enter__.return_value = mock_file

    # Mock Vision output
    mock_extract.return_value = {
        "indicators": [
            {"name": "ALT", "display_name": "谷丙转氨酶", "value": 150.0, "unit": "U/L", "reference_range": "20-100"},
            {"name": "ProBNP", "display_name": "心脏标志物", "value": 250.0, "unit": "pmol/L", "reference_range": "<100"}
        ]
    }

    # Mock Lab output (应该受到 Maine Coon 易感心脏病，以及肥胖易感脂肪肝的提示影响)
    mock_analyze.return_value = {
        "summary": "肝部指标异常升高（警惕脂肪肝），心脏指标异常（缅因猫HCM警报）。",
        "indicators": [
            {"name": "ALT", "value": 150.0, "status": "high", "reference_range": "20-100"},
            {"name": "ProBNP", "value": 250.0, "status": "high", "reference_range": "<100"}
        ]
    }

    # Mock Diet output
    mock_diet.return_value = [
        "绝对禁止断食，需换用低脂肝脏处方粮",
        "补充辅酶Q10保护心脏"
    ]

    orchestrator = MedicalOrchestrator()
    
    result = orchestrator.process_report("fake/path.jpg", "image/jpeg", mock_cat_profile_maine_coon_overweight)

    # 验证提取到的参考范围
    assert result["indicators"][0]["reference_min"] == 20.0
    assert result["indicators"][0]["reference_max"] == 100.0
    assert result["indicators"][1]["reference_min"] is None
    assert result["indicators"][1]["reference_max"] == 100.0

    # 验证最终组装结构
    assert "肝部指标异常升高" in result["summary"]
    assert len(result["recommendations"]) == 2
    assert "断食" in result["recommendations"][0]

    # 验证是否正确传递了特殊的 context 给 analyzer
    # args 形式: analyze(vision_data, general_lab, breed_skill)
    analyze_args = mock_analyze.call_args[0]
    assert "Maine Coon" in analyze_args[2] or "缅因" in analyze_args[2]

    # args 形式: prescribe(lab_result, general_diet, weight_skill)
    diet_args = mock_diet.call_args[0]
    assert "断食" in diet_args[2] or "肥胖" in diet_args[2]
