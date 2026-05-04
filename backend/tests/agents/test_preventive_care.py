def test_vaccination_model_fields():
    from app.models.models import VaccinationRecord
    assert hasattr(VaccinationRecord, 'vaccine_type')
    assert hasattr(VaccinationRecord, 'next_due_at')

def test_deworming_model_fields():
    from app.models.models import DewormingRecord
    assert hasattr(DewormingRecord, 'product_name')
    assert hasattr(DewormingRecord, 'next_due_at')

import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_list_vaccinations(client):
    response = await client.get("/api/v1/preventive-care/vaccinations?cat_id=test-cat-id")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_list_deworming(client):
    response = await client.get("/api/v1/preventive-care/deworming?cat_id=test-cat-id")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
