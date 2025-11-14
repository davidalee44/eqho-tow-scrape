#!/usr/bin/env python3
"""
Script to run Apify crawls for Jacksonville NC and Florida only
"""
import asyncio
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.apify_service import ApifyService
from app.config import settings
from datetime import datetime
import json

# Target locations for Jacksonville NC and Florida only
TARGET_LOCATIONS = [
    {
        "location": "Jacksonville, NC",
        "search_queries": [
            "impound lot",
            "towing impound",
            "vehicle impound",
            "car impound",
            "impound service",
            "towing company impound",
            "auto impound"
        ],
        "max_results": 3000
    },
    {
        "location": "Florida, USA",
        "search_queries": [
            "impound lot",
            "towing impound",
            "vehicle impound",
            "car impound",
            "impound service",
            "towing company impound",
            "auto impound",
            "towing company"
        ],
        "max_results": 5000
    }
]


async def run_crawls():
    """Run crawls for Jacksonville NC and Florida"""
    
    if not settings.apify_token:
        print("ERROR: APIFY_TOKEN not set")
        sys.exit(1)
    
    apify_service = ApifyService()
    
    try:
        print("="*80)
        print("JACKSONVILLE NC & FLORIDA CRAWL CAMPAIGN")
        print("="*80)
        print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        all_runs = []
        total_targeted = 0
        
        for location_config in TARGET_LOCATIONS:
            location = location_config["location"]
            search_queries = location_config["search_queries"]
            max_results = location_config["max_results"]
            
            print(f"\n{'='*80}")
            print(f"📍 Location: {location}")
            print(f"{'='*80}")
            print(f"Search queries: {len(search_queries)}")
            print(f"Max results per query: {max_results:,}")
            print(f"Total targeted: {max_results * len(search_queries):,} results\n")
            
            location_runs = []
            
            for i, query in enumerate(search_queries, 1):
                print(f"  [{i}/{len(search_queries)}] Running: '{query}' in {location}...")
                
                try:
                    input_data = {
                        "searchStringsArray": [f"{query} {location}"],
                        "maxCrawledPlacesPerSearch": max_results,
                        "maxReviewsPerPlace": 10,
                        "includeImages": True,
                        "includeOpeningHours": True,
                        "language": "en",
                        "includeWebResults": True
                    }
                    
                    actor_id = "compass/crawler-google-places"
                    encoded_actor_id = quote(actor_id, safe='')
                    
                    run_response = await apify_service.client.post(
                        f"{apify_service.base_url}/acts/{encoded_actor_id}/runs?token={apify_service.api_token}",
                        json=input_data
                    )
                    run_response.raise_for_status()
                    run_data = run_response.json()
                    run_id = run_data["data"]["id"]
                    
                    location_runs.append({
                        "run_id": run_id,
                        "location": location,
                        "query": query,
                        "max_results": max_results,
                        "status": "RUNNING",
                        "started_at": datetime.now().isoformat(),
                        "console_url": f"https://console.apify.com/view/runs/{run_id}"
                    })
                    
                    total_targeted += max_results
                    
                    print(f"    ✓ Started run: {run_id}")
                    print(f"      Console: https://console.apify.com/view/runs/{run_id}")
                    
                except Exception as e:
                    print(f"    ✗ Error: {e}")
                    continue
            
            all_runs.extend(location_runs)
            print(f"\n  ✓ Started {len(location_runs)} crawls for {location}")
        
        print(f"\n{'='*80}")
        print("CRAWL SUMMARY")
        print(f"{'='*80}")
        print(f"Total runs started: {len(all_runs)}")
        print(f"Total results targeted: {total_targeted:,}")
        
        # Load existing runs and merge
        runs_file = Path("impound_crawl_runs.json")
        existing_runs = []
        if runs_file.exists():
            with open(runs_file, 'r') as f:
                existing_data = json.load(f)
                existing_runs = existing_data.get('runs', [])
        
        # Merge runs
        all_runs_combined = existing_runs + all_runs
        
        # Save updated runs
        with open(runs_file, 'w') as f:
            json.dump({
                "started_at": datetime.now().isoformat(),
                "total_runs": len(all_runs_combined),
                "total_targeted": sum(r.get('max_results', 0) for r in all_runs_combined),
                "target_locations": ["Baltimore, MD", "Jacksonville, NC", "Florida, USA"],
                "runs": all_runs_combined
            }, f, indent=2)
        
        print(f"\n✓ Run IDs saved to: {runs_file}")
        print(f"\n💡 Monitor at: https://console.apify.com/organization/csuekOO8cSY3WDp3c/actors/runs")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await apify_service.close()


if __name__ == "__main__":
    asyncio.run(run_crawls())

