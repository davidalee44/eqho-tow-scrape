#!/usr/bin/env python3
"""
Script to run Apify Google Maps crawls targeting impound services
in specific cities/regions to generate 15-20k leads

Targets:
- Baltimore, MD
- Jacksonville, NC  
- Florida (statewide)

Focus: Companies that do impounds

Usage:
    make run-impound-crawls [MAX_RESULTS_PER_LOCATION=N]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import quote

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.apify_service import ApifyService
from app.config import settings


# Target locations for impound-focused crawls
TARGET_LOCATIONS = [
    {
        "location": "Baltimore, MD",
        "search_queries": [
            "impound lot",
            "towing impound",
            "vehicle impound",
            "car impound",
            "impound service",
            "towing company impound",
            "auto impound"
        ],
        "max_results": 3000  # Target ~3k per location for 15-20k total
    },
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
            "towing company"  # Broader search for Florida
        ],
        "max_results": 5000  # Larger for statewide
    }
]


async def run_impound_crawls(max_results_per_location: int = None):
    """Run Apify crawls targeting impound services in specific locations"""
    
    if not settings.apify_token:
        print("ERROR: APIFY_TOKEN not set in environment variables")
        sys.exit(1)
    
    apify_service = ApifyService()
    
    try:
        print("="*80)
        print("IMPOUND-FOCUSED CRAWL CAMPAIGN")
        print("="*80)
        print(f"\nTarget: 15,000-20,000 leads with impound services")
        print(f"Locations: Baltimore MD, Jacksonville NC, Florida")
        print(f"Data Collection: Ratings, Photos, Map Locations")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        all_runs = []
        total_targeted = 0
        
        for location_config in TARGET_LOCATIONS:
            location = location_config["location"]
            search_queries = location_config["search_queries"]
            max_results = max_results_per_location or location_config["max_results"]
            
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
                    # Prepare comprehensive input for Google Maps Scraper
                    # Use searchStringsArray format (works with apify/google-maps-scraper)
                    input_data = {
                        "searchStringsArray": [f"{query} {location}"],
                        "maxCrawledPlacesPerSearch": max_results,
                        "maxReviewsPerPlace": 10,  # Get reviews for ratings/stars
                        "includeImages": True,  # Get photos of offices
                        "includeOpeningHours": True,
                        "language": "en",
                        "includeWebResults": True
                    }
                    
                    # Start the crawl - use compass/crawler-google-places (verified working)
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
                    print(f"    ✗ Error starting crawl: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            all_runs.extend(location_runs)
            print(f"\n  ✓ Started {len(location_runs)} crawls for {location}")
        
        print(f"\n{'='*80}")
        print("CRAWL SUMMARY")
        print(f"{'='*80}")
        print(f"Total runs started: {len(all_runs)}")
        print(f"Total results targeted: {total_targeted:,}")
        print(f"Estimated completion: 10-30 minutes per run")
        print(f"\nRun IDs:")
        for run in all_runs:
            print(f"  • {run['run_id']}: {run['query']} in {run['location']}")
            print(f"    {run['console_url']}")
        
        # Save run IDs for tracking
        import json
        runs_file = Path("impound_crawl_runs.json")
        with open(runs_file, 'w') as f:
            json.dump({
                "started_at": datetime.now().isoformat(),
                "total_runs": len(all_runs),
                "total_targeted": total_targeted,
                "target_locations": [loc["location"] for loc in TARGET_LOCATIONS],
                "runs": all_runs
            }, f, indent=2)
        
        print(f"\n✓ Run IDs saved to: {runs_file}")
        print(f"\n💡 Next steps:")
        print(f"  1. Monitor runs: https://console.apify.com/organization/csuekOO8cSY3WDp3c/actors/runs")
        print(f"  2. Check status: make apify-list")
        print(f"  3. Download when complete: make apify-download LIMIT_RUNS={len(all_runs)}")
        print(f"  4. Import to Supabase: make apify-import-to-supabase ZONE_ID=<uuid>")
        print(f"  5. Filter for impound: make query-companies HAS_IMPOUND=true")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await apify_service.close()


async def main():
    parser = argparse.ArgumentParser(description="Run impound-focused Apify crawls")
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Max results per search query (default: 3000 for cities, 5000 for states)",
    )
    
    args = parser.parse_args()
    
    await run_impound_crawls(max_results_per_location=args.max_results)


if __name__ == "__main__":
    asyncio.run(main())
