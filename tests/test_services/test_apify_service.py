"""Tests for ApifyService with mocking"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.apify_service import ApifyService


@pytest.fixture
def apify_service():
    """Create ApifyService instance"""
    return ApifyService()


@pytest.mark.asyncio
async def test_crawl_google_maps_success(apify_service):
    """Test successful Google Maps crawl with mocked Apify API"""
    mock_response_data = {
        "data": {
            "id": "test-run-id"
        }
    }
    
    mock_results = [
        {
            "title": "Test Towing Company",
            "address": "123 Main St, Salt Lake City, UT 84101",
            "phone": "555-0100",
            "website": "https://testtowing.com",
            "url": "https://maps.google.com/test",
            "rating": 4.5,
            "reviewsCount": 100,
            "openingHours": {"monday": "8am-5pm"}
        }
    ]
    
    with patch.object(apify_service.client, 'post', new_callable=AsyncMock) as mock_post, \
         patch.object(apify_service.client, 'get', new_callable=AsyncMock) as mock_get:
        
        # Mock run creation
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response_data
        mock_post.return_value.raise_for_status = lambda: None
        
        # Mock run status check (succeeded)
        mock_status_response = AsyncMock()
        mock_status_response.json.return_value = {
            "data": {"status": "SUCCEEDED"}
        }
        mock_status_response.raise_for_status = lambda: None
        
        # Mock results retrieval
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_results
        mock_get.return_value.raise_for_status = lambda: None
        
        # First call is for run creation, subsequent calls are for status checks
        mock_get.side_effect = [
            mock_status_response,  # Status check
            mock_get.return_value  # Results
        ]
        
        companies = await apify_service.crawl_google_maps(
            location="Utah, USA",
            search_query="towing company",
            max_results=10
        )
        
        assert len(companies) == 1
        assert companies[0]["name"] == "Test Towing Company"
        assert companies[0]["phone_primary"] == "555-0100"
        assert companies[0]["address_city"] == "Salt Lake City"
        assert companies[0]["address_state"] == "UT"


@pytest.mark.asyncio
async def test_map_apify_result_complete_data(apify_service):
    """Test mapping Apify result with complete data"""
    apify_item = {
        "title": "Complete Towing",
        "address": "456 Oak St, Dallas, TX 75201",
        "phone": "555-0200",
        "website": "https://completetowing.com",
        "url": "https://maps.google.com/complete",
        "rating": 4.8,
        "reviewsCount": 250,
        "openingHours": {
            "monday": "24 hours",
            "tuesday": "24 hours"
        }
    }
    
    result = apify_service._map_apify_result(apify_item)
    
    assert result is not None
    assert result["name"] == "Complete Towing"
    assert result["phone_primary"] == "555-0200"
    assert result["address_city"] == "Dallas"
    assert result["address_state"] == "TX"
    assert result["rating"] == 4.8
    assert result["review_count"] == 250


@pytest.mark.asyncio
async def test_map_apify_result_minimal_data(apify_service):
    """Test mapping Apify result with minimal data"""
    apify_item = {
        "title": "Minimal Towing",
        "address": "789 Pine St",
        "url": "https://maps.google.com/minimal"
    }
    
    result = apify_service._map_apify_result(apify_item)
    
    assert result is not None
    assert result["name"] == "Minimal Towing"
    assert result["phone_primary"] == ""  # Empty string when missing
    assert result["rating"] is None
    assert result["review_count"] is None


@pytest.mark.asyncio
async def test_map_apify_result_invalid_data(apify_service):
    """Test mapping Apify result with invalid data"""
    apify_item = {}  # Empty dict
    
    result = apify_service._map_apify_result(apify_item)
    
    # Should return None for invalid data
    assert result is None

