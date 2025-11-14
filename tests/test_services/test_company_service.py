"""Tests for CompanyService"""
import pytest
from uuid import uuid4
from app.services.company_service import CompanyService
from app.schemas.company import CompanyUpdate


@pytest.mark.asyncio
async def test_create_or_update_company_new(db_session, test_zone):
    """Test creating a new company"""
    company_data = {
        "name": "New Towing Company",
        "phone_primary": "555-0200",
        "google_business_url": "https://maps.google.com/new",
        "address_street": "456 Oak Ave",
        "address_city": "Salt Lake City",
        "address_state": "UT",
        "address_zip": "84102",
        "source": "test"
    }
    
    company = await CompanyService.create_or_update_company(
        db_session,
        company_data,
        test_zone.id
    )
    
    assert company.name == "New Towing Company"
    assert company.zone_id == test_zone.id
    assert company.id is not None


@pytest.mark.asyncio
async def test_create_or_update_company_existing(db_session, test_zone, test_company):
    """Test updating existing company by Google Business URL"""
    company_data = {
        "name": "Updated Company Name",
        "phone_primary": "555-0300",
        "google_business_url": test_company.google_business_url,
        "address_street": test_company.address_street,
        "address_city": test_company.address_city,
        "address_state": test_company.address_state,
        "address_zip": test_company.address_zip,
        "source": "test"
    }
    
    company = await CompanyService.create_or_update_company(
        db_session,
        company_data,
        test_zone.id
    )
    
    assert company.id == test_company.id
    assert company.name == "Updated Company Name"
    assert company.phone_primary == "555-0300"


@pytest.mark.asyncio
async def test_get_company_success(db_session, test_company):
    """Test getting company by ID"""
    company = await CompanyService.get_company(db_session, test_company.id)
    
    assert company is not None
    assert company.id == test_company.id
    assert company.name == test_company.name


@pytest.mark.asyncio
async def test_search_companies_by_zone(db_session, test_zone, test_company):
    """Test searching companies by zone"""
    companies = await CompanyService.search_companies(
        db_session,
        zone_id=test_zone.id
    )
    
    assert len(companies) == 1
    assert companies[0].id == test_company.id


@pytest.mark.asyncio
async def test_search_companies_by_fleet_size(db_session, test_company):
    """Test searching companies by fleet size"""
    # Update company with fleet size
    update_data = CompanyUpdate(fleet_size="large")
    await CompanyService.update_company(db_session, test_company.id, update_data)
    
    companies = await CompanyService.search_companies(
        db_session,
        fleet_size="large"
    )
    
    assert len(companies) == 1
    assert companies[0].fleet_size == "large"


@pytest.mark.asyncio
async def test_search_companies_by_impound_service(db_session, test_company):
    """Test searching companies by impound service"""
    # Update company with impound service
    update_data = CompanyUpdate(has_impound_service=True)
    await CompanyService.update_company(db_session, test_company.id, update_data)
    
    companies = await CompanyService.search_companies(
        db_session,
        has_impound_service=True
    )
    
    assert len(companies) == 1
    assert companies[0].has_impound_service is True


@pytest.mark.asyncio
async def test_update_company_success(db_session, test_company):
    """Test updating company"""
    update_data = CompanyUpdate(
        name="Updated Name",
        email="test@example.com"
    )
    updated = await CompanyService.update_company(
        db_session,
        test_company.id,
        update_data
    )
    
    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.email == "test@example.com"


@pytest.mark.asyncio
async def test_bulk_import_companies(db_session, test_zone):
    """Test bulk importing companies"""
    companies_data = [
        {
            "name": "Company 1",
            "phone_primary": "555-1001",
            "google_business_url": "https://maps.google.com/1",
            "address_street": "123 St",
            "address_city": "City",
            "address_state": "UT",
            "address_zip": "84101",
            "source": "test"
        },
        {
            "name": "Company 2",
            "phone_primary": "555-1002",
            "google_business_url": "https://maps.google.com/2",
            "address_street": "456 St",
            "address_city": "City",
            "address_state": "UT",
            "address_zip": "84101",
            "source": "test"
        }
    ]
    
    companies = await CompanyService.bulk_import_companies(
        db_session,
        companies_data,
        test_zone.id
    )
    
    assert len(companies) == 2
    assert all(c.zone_id == test_zone.id for c in companies)

