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
        
        # URL encode actor ID if it contains slashes
        from urllib.parse import quote
        encoded_actor_id = quote(actor_id, safe='')
        
        # Start the actor run
        run_response = await self.client.post(
            f"{self.base_url}/acts/{encoded_actor_id}/runs?token={self.api_token}",
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
            
            # Extract images/photos
            images = item.get("images", [])
            photos = []
            if images:
                photos = [img.get("url", "") for img in images if img.get("url")]
            
            # Extract location coordinates
            location = item.get("location", {})
            latitude = location.get("lat") if location else None
            longitude = location.get("lng") if location else None
            
            # Extract rating and reviews
            rating = item.get("rating")
            review_count = item.get("reviewsCount", 0)
            reviews = item.get("reviews", [])
            
            # Validate required fields - need at least title and google_maps_url
            if not title or not google_maps_url:
                return None
            
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
            
            # Extract hours
            hours = item.get("openingHours", {})
            
            # Extract additional data
            category = item.get("category", "")
            description = item.get("description", "")
            
            # Build result with all available data
            result = {
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
            
            # Add optional fields if available
            if latitude and longitude:
                result["latitude"] = latitude
                result["longitude"] = longitude
            
            if photos:
                result["photos"] = photos
            
            if category:
                result["category"] = category
            
            if description:
                result["description"] = description
            
            if reviews:
                result["reviews"] = reviews[:5]  # Store first 5 reviews
            
            return result
        except Exception as e:
            # Log error and skip this item
            print(f"Error mapping Apify result: {e}")
            return None
    
    async def list_runs(
        self,
        actor_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List previous actor runs
        
        Args:
            actor_id: Apify actor ID (e.g., "apify/google-maps-scraper" or None for all user runs)
            limit: Maximum number of runs to return
            offset: Number of runs to skip
            status: Filter by status (SUCCEEDED, FAILED, RUNNING, etc.)
        
        Returns:
            Dictionary with runs list and pagination info
        """
        params = {
            "limit": limit,
            "offset": offset,
            "token": self.api_token,  # Apify uses token as query param
        }
        if status:
            params["status"] = status
        
        if actor_id:
            # List runs for specific actor
            # URL encode actor ID if it contains slashes
            from urllib.parse import quote
            encoded_actor_id = quote(actor_id, safe='')
            url = f"{self.base_url}/acts/{encoded_actor_id}/runs"
        else:
            # List all runs for the user
            url = f"{self.base_url}/actor-runs"
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_run_details(self, run_id: str) -> Dict[str, Any]:
        """
        Get details of a specific run
        
        Args:
            run_id: Apify run ID
        
        Returns:
            Run details dictionary
        """
        response = await self.client.get(
            f"{self.base_url}/actor-runs/{run_id}",
            params={"token": self.api_token}
        )
        response.raise_for_status()
        return response.json()
    
    async def download_run_data(
        self,
        run_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Download data from a completed run
        
        Args:
            run_id: Apify run ID
            limit: Maximum number of items to return (None = all)
            offset: Number of items to skip
        
        Returns:
            List of company data dictionaries
        """
        # First check if run is completed
        run_details = await self.get_run_details(run_id)
        run_status = run_details["data"]["status"]
        
        if run_status != "SUCCEEDED":
            raise ValueError(f"Run {run_id} is not completed. Status: {run_status}")
        
        # Get dataset ID from run
        dataset_id = run_details["data"].get("defaultDatasetId")
        if not dataset_id:
            raise ValueError(f"Run {run_id} has no dataset")
        
        # Download dataset items
        params = {"offset": offset}
        if limit:
            params["limit"] = limit
        
        # Add token to params
        params["token"] = self.api_token
        
        response = await self.client.get(
            f"{self.base_url}/datasets/{dataset_id}/items",
            params=params
        )
        response.raise_for_status()
        results = response.json()
        
        # Map Apify results to our company schema
        items = results if isinstance(results, list) else results.get("items", [])
        companies = []
        for item in items:
            company = self._map_apify_result(item)
            if company:
                companies.append(company)
        
        return companies
    
    async def list_all_towing_runs(
        self,
        limit: int = 100,
        status: Optional[str] = "SUCCEEDED",
    ) -> List[Dict[str, Any]]:
        """
        List all previous towing company runs
        
        Args:
            limit: Maximum number of runs to return
            status: Filter by status (default: SUCCEEDED)
        
        Returns:
            List of run summaries with metadata
        """
        # Try listing all user runs first (more reliable)
        runs_data = await self.list_runs(
            actor_id=None,  # List all user runs
            limit=limit,
            status=status
        )
        
        # Handle different response formats
        if "data" in runs_data:
            runs = runs_data["data"].get("items", [])
        elif "items" in runs_data:
            runs = runs_data["items"]
        else:
            runs = []
        
        # Filter for Google Maps/Places scraper runs
        # Get actor details to check names
        towing_runs = []
        actor_cache = {}  # Cache actor names to avoid repeated API calls
        
        for run in runs:
            actor_id = run.get("actId", "")
            input_data = run.get("input", {})
            search_strings = input_data.get("searchStringsArray", [])
            
            # Get actor name from cache or API
            actor_name = ""
            if actor_id:
                if actor_id not in actor_cache:
                    try:
                        actor_resp = await self.client.get(
                            f"{self.base_url}/acts/{actor_id}",
                            params={"token": self.api_token}
                        )
                        if actor_resp.status_code == 200:
                            actor_data = actor_resp.json()
                            actor_name = actor_data.get("data", {}).get("name", "").lower()
                            actor_cache[actor_id] = actor_name
                        else:
                            actor_cache[actor_id] = ""
                    except Exception:
                        actor_cache[actor_id] = ""
                else:
                    actor_name = actor_cache[actor_id]
            
            # Check if actor is Google Maps/Places scraper
            is_google_maps = any(
                keyword in actor_name
                for keyword in ["google-maps", "google-maps-scraper", "crawler-google-places", "google-places"]
            )
            
            # Check if search contains "towing"
            is_towing = any(
                "towing" in str(search).lower() 
                for search in search_strings
            ) if search_strings else False
            
            # Include Google Maps/Places runs (they're likely towing companies)
            # or runs explicitly searching for "towing"
            if is_google_maps or is_towing:
                run_summary = {
                    "run_id": run["id"],
                    "status": run["status"],
                    "started_at": run.get("startedAt"),
                    "finished_at": run.get("finishedAt"),
                    "actor_id": actor_id,
                    "actor_name": actor_name or "Unknown",
                    "search_query": search_strings[0] if search_strings else input_data.get("queries", ["Unknown"])[0] if input_data.get("queries") else "Unknown",
                    "max_results": input_data.get("maxCrawledPlacesPerSearch", input_data.get("maxResults", 0)),
                    "stats": run.get("stats", {}),
                }
                towing_runs.append(run_summary)
        
        return towing_runs
    
    async def download_all_towing_data(
        self,
        limit_runs: int = 10,
        limit_items_per_run: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Download data from all previous towing runs
        
        Args:
            limit_runs: Maximum number of runs to process
            limit_items_per_run: Maximum items per run (None = all)
        
        Returns:
            Dictionary with all companies and metadata
        """
        # Get all towing runs
        runs = await self.list_all_towing_runs(limit=limit_runs)
        
        all_companies = []
        run_summaries = []
        
        for run_summary in runs:
            run_id = run_summary["run_id"]
            try:
                companies = await self.download_run_data(
                    run_id,
                    limit=limit_items_per_run
                )
                
                all_companies.extend(companies)
                run_summaries.append({
                    **run_summary,
                    "companies_count": len(companies),
                    "downloaded": True,
                })
            except Exception as e:
                run_summaries.append({
                    **run_summary,
                    "companies_count": 0,
                    "downloaded": False,
                    "error": str(e),
                })
        
        return {
            "total_runs": len(runs),
            "total_companies": len(all_companies),
            "runs": run_summaries,
            "companies": all_companies,
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

