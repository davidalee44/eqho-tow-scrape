"""Apify service for Google Maps scraping"""
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings


class ApifyService:
    """Service for interacting with Apify API"""
    
    def __init__(self):
        self.api_token = settings.apify_token
        self.base_url = "https://api.apify.com/v2"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            timeout=300.0
        )
    
    async def crawl_google_maps(
        self,
        location: str,
        search_query: str = "towing company",
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Crawl Google Maps for towing companies
        
        Args:
            location: Location string (e.g., "Utah, USA" or "Dallas, TX")
            search_query: Search query (default: "towing company")
            max_results: Maximum number of results to return
        
        Returns:
            List of company data dictionaries
        """
        # Use Apify's Google Maps Scraper actor
        actor_id = "apify/google-maps-scraper"
        
        # Prepare input for the actor
        input_data = {
            "searchStringsArray": [f"{search_query} {location}"],
            "maxCrawledPlacesPerSearch": max_results,
            "language": "en",
            "includeWebResults": True,
        }
        
        # Start the actor run
        run_response = await self.client.post(
            f"{self.base_url}/acts/{actor_id}/runs",
            json=input_data
        )
        run_response.raise_for_status()
        run_data = run_response.json()
        run_id = run_data["data"]["id"]
        
        # Wait for the run to complete
        await self._wait_for_run_completion(run_id)
        
        # Get the results
        results_response = await self.client.get(
            f"{self.base_url}/actor-runs/{run_id}/dataset/items"
        )
        results_response.raise_for_status()
        results = results_response.json()
        
        # Map Apify results to our company schema
        companies = []
        # Results can be a list directly or wrapped in items
        items = results if isinstance(results, list) else results.get("items", [])
        for item in items:
            company = self._map_apify_result(item)
            if company:
                companies.append(company)
        
        return companies
    
    async def _wait_for_run_completion(self, run_id: str, max_wait: int = 600):
        """Wait for Apify run to complete"""
        import asyncio
        
        elapsed = 0
        while elapsed < max_wait:
            status_response = await self.client.get(
                f"{self.base_url}/actor-runs/{run_id}"
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            
            status = status_data["data"]["status"]
            if status == "SUCCEEDED":
                return
            elif status == "FAILED":
                raise Exception(f"Apify run failed: {status_data.get('data', {}).get('statusMessage', 'Unknown error')}")
            
            await asyncio.sleep(5)
            elapsed += 5
        
        raise TimeoutError(f"Apify run timed out after {max_wait} seconds")
    
    def _map_apify_result(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map Apify Google Maps result to our company schema"""
        try:
            # Extract basic information
            title = item.get("title", "")
            address = item.get("address", "")
            phone = item.get("phone", "")
            website = item.get("website", "")
            google_maps_url = item.get("url", "")
            
            # Parse address components
            address_parts = address.split(",") if address else []
            street = address_parts[0].strip() if address_parts else ""
            city = address_parts[1].strip() if len(address_parts) > 1 else ""
            state_zip = address_parts[2].strip() if len(address_parts) > 2 else ""
            
            # Try to extract state and zip
            state = ""
            zip_code = ""
            if state_zip:
                parts = state_zip.split()
                if len(parts) >= 2:
                    state = parts[0]
                    zip_code = parts[-1]
            
            # Extract rating and reviews
            rating = item.get("rating")
            review_count = item.get("reviewsCount", 0)
            
            # Extract hours
            hours = item.get("openingHours", {})
            
            return {
                "name": title,
                "phone_primary": phone or "",
                "website": website,
                "google_business_url": google_maps_url,
                "address_street": street,
                "address_city": city,
                "address_state": state,
                "address_zip": zip_code,
                "rating": float(rating) if rating else None,
                "review_count": int(review_count) if review_count else None,
                "hours": hours if hours else None,
                "source": "apify_google_maps",
            }
        except Exception as e:
            # Log error and skip this item
            print(f"Error mapping Apify result: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

