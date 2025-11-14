"""Tests for WebsiteScraperService with mocking"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.website_scraper_service import WebsiteScraperService


@pytest.fixture
def scraper_service():
    """Create WebsiteScraperService instance"""
    return WebsiteScraperService()


@pytest.mark.asyncio
async def test_scrape_website_success(scraper_service):
    """Test successful website scraping"""
    mock_page = AsyncMock()
    mock_page.content.return_value = """
    <html>
        <body>
            <h1>Test Towing Company</h1>
            <p>We offer impound services for vehicles.</p>
            <div class="hours">
                <p>Monday: 8am - 5pm</p>
                <p>Tuesday: 8am - 5pm</p>
            </div>
        </body>
    </html>
    """
    mock_page.inner_text.return_value = """
    Test Towing Company
    We offer impound services for vehicles.
    Monday: 8am - 5pm
    Tuesday: 8am - 5pm
    """
    
    mock_browser = AsyncMock()
    mock_browser.new_page.return_value = mock_page
    
    scraper_service.browser = mock_browser
    
    result = await scraper_service.scrape_website("https://testtowing.com")
    
    assert result["status"] == "success"
    assert result["has_impound"] is True
    assert result["impound_confidence"] > 0.5
    assert result["hours"] is not None


@pytest.mark.asyncio
async def test_scrape_website_no_url(scraper_service):
    """Test scraping with no URL"""
    result = await scraper_service.scrape_website("")
    
    assert result["status"] == "no_website"
    assert result["has_impound"] is None
    assert result["hours"] is None


@pytest.mark.asyncio
async def test_scrape_website_failure(scraper_service):
    """Test website scraping failure"""
    mock_browser = AsyncMock()
    mock_browser.new_page.side_effect = Exception("Connection timeout")
    
    scraper_service.browser = mock_browser
    
    result = await scraper_service.scrape_website("https://invalid-url.com")
    
    assert result["status"] == "failed"
    assert result["has_impound"] is None


def test_check_impound_service_positive(scraper_service):
    """Test impound service detection with positive keywords"""
    html = "<html><body>We offer impound lot services and vehicle impoundment</body></html>"
    text = "We offer impound lot services and vehicle impoundment"
    
    result = scraper_service.check_impound_service(html, text)
    
    assert result["has_impound"] is True
    assert result["confidence"] > 0.8


def test_check_impound_service_negative(scraper_service):
    """Test impound service detection with negative keywords"""
    html = "<html><body>We do not impound vehicles. We are not an impound lot.</body></html>"
    text = "We do not impound vehicles. We are not an impound lot."
    
    result = scraper_service.check_impound_service(html, text)
    
    assert result["has_impound"] is False
    assert result["confidence"] > 0.5


def test_check_impound_service_no_mention(scraper_service):
    """Test impound service detection with no mention"""
    html = "<html><body>We offer towing services and roadside assistance.</body></html>"
    text = "We offer towing services and roadside assistance."
    
    result = scraper_service.check_impound_service(html, text)
    
    assert result["has_impound"] is False
    assert result["confidence"] < 0.5


def test_extract_hours_of_operation(scraper_service):
    """Test hours extraction from website"""
    html = """
    <html>
        <body>
            <div class="hours">
                <p>Monday: 8:00 AM - 5:00 PM</p>
                <p>Tuesday: 8:00 AM - 5:00 PM</p>
                <p>Wednesday: 8:00 AM - 5:00 PM</p>
            </div>
        </body>
    </html>
    """
    text = "Monday: 8:00 AM - 5:00 PM Tuesday: 8:00 AM - 5:00 PM"
    
    hours = scraper_service.extract_hours_of_operation(html, text)
    
    assert hours is not None
    assert "monday" in hours or "Monday" in str(hours)


def test_extract_hours_24_7(scraper_service):
    """Test 24/7 hours detection"""
    html = "<html><body>We are open 24/7, 24 hours a day</body></html>"
    text = "We are open 24/7, 24 hours a day"
    
    hours = scraper_service.extract_hours_of_operation(html, text)
    
    assert hours is not None
    assert hours.get("24_7") is True

