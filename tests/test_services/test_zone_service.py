"""Tests for ZoneService"""
import pytest
from uuid import uuid4
from app.services.zone_service import ZoneService
from app.schemas.zone import ZoneCreate, ZoneUpdate


@pytest.mark.asyncio
async def test_create_zone_success(db_session):
    """Test successful zone creation"""
    zone_data = ZoneCreate(
        name="Dallas-Fort Worth",
        state="TX",
        zone_type="city",
        is_active=True
    )
    zone = await ZoneService.create_zone(db_session, zone_data)
    
    assert zone.name == "Dallas-Fort Worth"
    assert zone.state == "TX"
    assert zone.zone_type == "city"
    assert zone.is_active is True
    assert zone.id is not None


@pytest.mark.asyncio
async def test_get_zone_success(db_session, test_zone):
    """Test getting zone by ID"""
    zone = await ZoneService.get_zone(db_session, test_zone.id)
    
    assert zone is not None
    assert zone.id == test_zone.id
    assert zone.name == test_zone.name


@pytest.mark.asyncio
async def test_get_zone_not_found(db_session):
    """Test getting non-existent zone"""
    zone = await ZoneService.get_zone(db_session, uuid4())
    assert zone is None


@pytest.mark.asyncio
async def test_list_zones(db_session, test_zone):
    """Test listing zones"""
    zones = await ZoneService.list_zones(db_session, active_only=True)
    
    assert len(zones) == 1
    assert zones[0].id == test_zone.id


@pytest.mark.asyncio
async def test_list_zones_inactive_filtered(db_session):
    """Test that inactive zones are filtered out"""
    # Create inactive zone
    zone_data = ZoneCreate(
        name="Inactive Zone",
        zone_type="city",
        is_active=False
    )
    await ZoneService.create_zone(db_session, zone_data)
    
    zones = await ZoneService.list_zones(db_session, active_only=True)
    assert len(zones) == 0


@pytest.mark.asyncio
async def test_update_zone_success(db_session, test_zone):
    """Test updating zone"""
    update_data = ZoneUpdate(name="Updated Zone Name")
    updated_zone = await ZoneService.update_zone(db_session, test_zone.id, update_data)
    
    assert updated_zone is not None
    assert updated_zone.name == "Updated Zone Name"
    assert updated_zone.id == test_zone.id


@pytest.mark.asyncio
async def test_update_zone_not_found(db_session):
    """Test updating non-existent zone"""
    update_data = ZoneUpdate(name="Updated Name")
    result = await ZoneService.update_zone(db_session, uuid4(), update_data)
    assert result is None


@pytest.mark.asyncio
async def test_delete_zone_success(db_session, test_zone):
    """Test deactivating zone"""
    success = await ZoneService.delete_zone(db_session, test_zone.id)
    assert success is True
    
    # Verify zone is deactivated
    zone = await ZoneService.get_zone(db_session, test_zone.id)
    assert zone.is_active is False


@pytest.mark.asyncio
async def test_delete_zone_not_found(db_session):
    """Test deleting non-existent zone"""
    success = await ZoneService.delete_zone(db_session, uuid4())
    assert success is False

