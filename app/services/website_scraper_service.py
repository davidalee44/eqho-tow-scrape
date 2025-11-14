"""Website scraper service using Playwright"""
from playwright.async_api import async_playwright, Browser, Page
from typing import Dict, Any, Optional
import re
from app.config import settings


class WebsiteScraperService:
    """Service for scraping company websites"""
    
    def __init__(self):
        self.headless = settings.playwright_headless
        self.timeout = settings.playwright_timeout
        self.browser: Optional[Browser] = None
    
    async def initialize(self):
        """Initialize Playwright browser"""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
    
    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """
        Scrape a company website for hours and impound service
        
        Returns:
            {
                'hours': dict,
                'has_impound': bool,
                'impound_confidence': float,
                'status': 'success' | 'failed' | 'no_website'
            }
        """
        if not url or not url.startswith(('http://', 'https://')):
            return {
                'hours': None,
                'has_impound': None,
                'impound_confidence': 0.0,
                'status': 'no_website'
            }
        
        try:
            await self.initialize()
            page = await self.browser.new_page()
            await page.goto(url, timeout=self.timeout, wait_until='networkidle')
            
            # Get page content
            html_content = await page.content()
            text_content = await page.inner_text('body')
            
            # Extract hours
            hours = self.extract_hours_of_operation(html_content, text_content)
            
            # Check for impound service
            impound_result = self.check_impound_service(html_content, text_content)
            
            await page.close()
            
            return {
                'hours': hours,
                'has_impound': impound_result['has_impound'],
                'impound_confidence': impound_result['confidence'],
                'status': 'success'
            }
        except Exception as e:
            print(f"Error scraping website {url}: {e}")
            return {
                'hours': None,
                'has_impound': None,
                'impound_confidence': 0.0,
                'status': 'failed'
            }
    
    def extract_hours_of_operation(self, html: str, text: str) -> Optional[Dict[str, Any]]:
        """Extract hours of operation from website content"""
        hours_patterns = [
            r'(?:hours?|open|business hours?)[\s:]*([^\n]+)',
            r'(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)[\s:]*([^\n]+)',
            r'(\d{1,2}:\d{2}\s*(?:am|pm)?\s*[-–—]\s*\d{1,2}:\d{2}\s*(?:am|pm)?)',
        ]
        
        hours_data = {}
        
        # Look for common hours formats
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            pattern = rf'{day}[\s:]*([^\n]+)'
            match = re.search(pattern, text.lower())
            if match:
                hours_data[day] = match.group(1).strip()
        
        # Look for 24/7 indicators
        if re.search(r'24/7|24 hours|always open|open 24', text.lower()):
            hours_data['24_7'] = True
        
        return hours_data if hours_data else None
    
    def check_impound_service(self, html: str, text: str) -> Dict[str, Any]:
        """
        Check if company offers impound service
        
        Returns:
            {
                'has_impound': bool,
                'confidence': float (0.0-1.0)
            }
        """
        # Keywords that indicate impound service
        impound_keywords = [
            'impound',
            'impound lot',
            'impound yard',
            'vehicle impound',
            'car impound',
            'towing impound',
            'impoundment',
            'impounded vehicles',
            'impound storage',
            'police impound',
        ]
        
        # Negative keywords (indicates they DON'T do impound)
        negative_keywords = [
            'we do not impound',
            'no impound',
            'not an impound',
        ]
        
        text_lower = text.lower()
        html_lower = html.lower()
        
        # Check for negative keywords first
        for keyword in negative_keywords:
            if keyword in text_lower or keyword in html_lower:
                return {'has_impound': False, 'confidence': 0.9}
        
        # Count matches
        matches = 0
        for keyword in impound_keywords:
            if keyword in text_lower:
                matches += 1
            if keyword in html_lower:
                matches += 1
        
        # Calculate confidence
        if matches == 0:
            return {'has_impound': False, 'confidence': 0.3}
        elif matches == 1:
            return {'has_impound': True, 'confidence': 0.6}
        elif matches == 2:
            return {'has_impound': True, 'confidence': 0.8}
        else:
            return {'has_impound': True, 'confidence': 0.95}

