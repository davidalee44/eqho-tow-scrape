"""Tests for zone API endpoints"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from uuid import uuid4


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.mark.asyncio
async def test_create_zone_endpoint(client, db_session, override_get_db):
    """Test POST /api/v1/zones"""
    app.dependency_overrides[get_db] = override_get_db
    
    zone_data = {
        "name": "Test Zone",
        "state": "UT",
        "zone_type": "city",
        "is_active": True
    }
    
    response = client.post("/api/v1/zones", json=zone_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Zone"
    assert data["state"] == "UT"
    assert "id" in data
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_zones_endpoint(client, db_session, test_zone, override_get_db):
    """Test GET /api/v1/zones"""
    app.dependency_overrides[get_db] = override_get_db
    
    response = client.get("/api/v1/zones?active_only=true")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_zone_endpoint(client, db_session, test_zone, override_get_db):
    """Test GET /api/v1/zones/{zone_id}"""
    app.dependency_overrides[get_db] = override_get_db
    
    response = client.get(f"/api/v1/zones/{test_zone.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_zone.id)
    assert data["name"] == test_zone.name
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_zone_not_found(client, db_session, override_get_db):
    """Test GET /api/v1/zones/{zone_id} with non-existent zone"""
    app.dependency_overrides[get_db] = override_get_db
    
    response = client.get(f"/api/v1/zones/{uuid4()}")
    
    assert response.status_code == 404
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_zone_endpoint(client, db_session, test_zone, override_get_db):
    """Test PUT /api/v1/zones/{zone_id}"""
    app.dependency_overrides[get_db] = override_get_db
    
    update_data = {"name": "Updated Zone Name"}
    response = client.put(f"/api/v1/zones/{test_zone.id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Zone Name"
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_zone_endpoint(client, db_session, test_zone, override_get_db):
    """Test DELETE /api/v1/zones/{zone_id}"""
    app.dependency_overrides[get_db] = override_get_db
    
    response = client.delete(f"/api/v1/zones/{test_zone.id}")
    
    assert response.status_code == 204
    
    app.dependency_overrides.clear()

