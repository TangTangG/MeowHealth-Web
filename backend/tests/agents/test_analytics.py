import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_weight_trend_api(client):
    response = await client.get("/api/v1/analytics/weight-trend?cat_id=test")
    assert response.status_code == 200
    assert "data" in response.json()

@pytest.mark.asyncio
async def test_indicator_history_api(client):
    response = await client.get("/api/v1/analytics/indicator-history?cat_id=test&indicator_name=WBC")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
