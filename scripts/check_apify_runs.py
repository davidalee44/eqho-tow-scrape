#!/usr/bin/env python3
"""
Quick script to check status of recent Apify runs

Usage:
    python scripts/check_apify_runs.py [--limit N]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.apify_service import ApifyService
from app.config import settings


async def check_runs(limit: int = 10):
    """Check status of recent Apify runs"""
    
    if not settings.apify_token:
        print("ERROR: APIFY_TOKEN not set")
        sys.exit(1)
    
    apify_service = ApifyService()
    
    try:
        # Get recent runs
        async with apify_service.client as client:
            response = await client.get(
                f"{apify_service.base_url}/actor-runs",
                params={
                    "token": apify_service.api_token,
                    "limit": limit,
                    "desc": True
                }
            )
            response.raise_for_status()
            data = response.json()
            runs = data.get("data", {}).get("items", [])
        
        if not runs:
            print("No runs found")
            return
        
        print("="*80)
        print(f"RECENT APIFY RUNS (last {len(runs)})")
        print("="*80)
        
        for i, run in enumerate(runs, 1):
            run_id = run.get("id", "N/A")
            status = run.get("status", "UNKNOWN")
            actor_id = run.get("actorId", "N/A")
            started = run.get("startedAt", "")
            finished = run.get("finishedAt", "")
            
            # Format dates
            if started:
                try:
                    dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    started_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    started_str = started[:19] if len(started) > 19 else started
            else:
                started_str = "N/A"
            
            if finished:
                try:
                    dt = datetime.fromisoformat(finished.replace('Z', '+00:00'))
                    finished_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    finished_str = finished[:19] if len(finished) > 19 else finished
            else:
                finished_str = "Running..."
            
            # Status emoji
            status_emoji = {
                "SUCCEEDED": "✅",
                "FAILED": "❌",
                "RUNNING": "🔄",
                "ABORTED": "⏹️",
                "TIMED-OUT": "⏱️"
            }.get(status, "❓")
            
            print(f"\n{i}. {status_emoji} {run_id}")
            print(f"   Status: {status}")
            print(f"   Actor: {actor_id}")
            print(f"   Started: {started_str}")
            print(f"   Finished: {finished_str}")
            print(f"   Console: https://console.apify.com/view/runs/{run_id}")
            
            # Get dataset info if succeeded
            if status == "SUCCEEDED":
                dataset_id = run.get("defaultDatasetId")
                if dataset_id:
                    try:
                        dataset_resp = await apify_service.client.get(
                            f"{apify_service.base_url}/datasets/{dataset_id}",
                            params={"token": apify_service.api_token}
                        )
                        if dataset_resp.status_code == 200:
                            dataset_data = dataset_resp.json().get("data", {})
                            item_count = dataset_data.get("itemCount", 0)
                            print(f"   📊 Items: {item_count:,}")
                    except:
                        pass
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await apify_service.close()


async def main():
    parser = argparse.ArgumentParser(description="Check status of recent Apify runs")
    parser.add_argument("--limit", type=int, default=10, help="Number of runs to check")
    
    args = parser.parse_args()
    
    await check_runs(args.limit)


if __name__ == "__main__":
    asyncio.run(main())

