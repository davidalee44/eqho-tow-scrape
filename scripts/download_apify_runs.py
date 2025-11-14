#!/usr/bin/env python3
# Note: Run with: source venv/bin/activate && python scripts/download_apify_runs.py
# Or use: python3 scripts/download_apify_runs.py (if venv is activated)
"""
Script to download previous Apify towing data runs

Usage:
    source venv/bin/activate
    python scripts/download_apify_runs.py [--limit-runs N] [--limit-items N] [--output FILE]
"""
import asyncio
import json
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.apify_service import ApifyService
from app.config import settings


async def main():
    parser = argparse.ArgumentParser(description="Download previous Apify towing data runs")
    parser.add_argument(
        "--limit-runs",
        type=int,
        default=10,
        help="Maximum number of runs to process (default: 10)",
    )
    parser.add_argument(
        "--limit-items",
        type=int,
        default=None,
        help="Maximum items per run (default: all)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="apify_towing_data.json",
        help="Output file path (default: apify_towing_data.json)",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list runs, don't download data",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Download specific run by ID",
    )
    
    args = parser.parse_args()
    
    # Check for API token
    if not settings.apify_token:
        print("ERROR: APIFY_TOKEN not set in environment variables")
        print("Please set APIFY_TOKEN in your .env file or environment")
        print("\nTo set it:")
        print("1. Get your token from: https://console.apify.com/account/integrations")
        print("2. Add to .env file: APIFY_TOKEN=your_token_here")
        sys.exit(1)
    
    apify_service = ApifyService()
    
    try:
        if args.run_id:
            # Download specific run
            print(f"Downloading data from run: {args.run_id}")
            companies = await apify_service.download_run_data(
                run_id=args.run_id,
                limit=args.limit_items
            )
            
            output_data = {
                "run_id": args.run_id,
                "companies_count": len(companies),
                "companies": companies,
            }
            
            print(f"Downloaded {len(companies)} companies from run {args.run_id}")
            
        elif args.list_only:
            # List runs only
            print("Listing previous towing runs...")
            print("(This may take a moment to fetch from Apify API)\n")
            runs = await apify_service.list_all_towing_runs(limit=args.limit_runs)
            
            if not runs:
                print("No towing runs found.")
                print("\nPossible reasons:")
                print("- No completed runs in your Apify account")
                print("- Runs don't contain 'towing' in search query")
                print("- Token doesn't have access to runs")
                return
            
            print(f"Found {len(runs)} towing runs:\n")
            for i, run in enumerate(runs, 1):
                print(f"{i}. Run ID: {run['run_id']}")
                print(f"   Status: {run['status']}")
                print(f"   Actor: {run.get('actor_id', 'Unknown')}")
                print(f"   Search: {run['search_query']}")
                print(f"   Started: {run.get('started_at', 'N/A')}")
                print(f"   Finished: {run.get('finished_at', 'N/A')}")
                if run.get('stats'):
                    stats = run['stats']
                    print(f"   Stats: {stats}")
                print()
            
            output_data = {
                "total_runs": len(runs),
                "runs": runs,
            }
            
        else:
            # Download all runs
            print(f"Downloading data from up to {args.limit_runs} previous towing runs...")
            print("(This may take a moment)\n")
            result = await apify_service.download_all_towing_data(
                limit_runs=args.limit_runs,
                limit_items_per_run=args.limit_items
            )
            
            print(f"\nDownload Summary:")
            print(f"  Total runs processed: {result['total_runs']}")
            print(f"  Total companies downloaded: {result['total_companies']}")
            print(f"\nRun details:")
            for run in result['runs']:
                status_icon = "✓" if run.get('downloaded') else "✗"
                print(f"  {status_icon} {run['run_id']}: {run.get('companies_count', 0)} companies")
                if run.get('error'):
                    print(f"    Error: {run['error']}")
            
            output_data = result
        
        # Save to file
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"\nData saved to: {output_path}")
        print(f"Total size: {output_path.stat().st_size / 1024:.2f} KB")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await apify_service.close()


if __name__ == "__main__":
    asyncio.run(main())
