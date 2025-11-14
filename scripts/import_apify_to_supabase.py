#!/usr/bin/env python3
"""
Script to download Apify datasets and import them into Supabase

Usage:
    make apify-import-to-supabase ZONE_ID=<uuid> [LIMIT_RUNS=N] [LIMIT_ITEMS=N]
    Or: python scripts/import_apify_to_supabase.py --zone-id <uuid> [--limit-runs N] [--limit-items N]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.apify_service import ApifyService
from app.services.company_service import CompanyService
from app.services.zone_service import ZoneService
from app.database import get_db
from app.config import settings


async def import_apify_data_to_supabase(
    zone_id: UUID,
    limit_runs: int = 10,
    limit_items_per_run: int = None
):
    """Download Apify data and import into Supabase"""
    
    # Check for API token
    if not settings.apify_token:
        print("ERROR: APIFY_TOKEN not set in environment variables")
        print("Please set APIFY_TOKEN in your .env file")
        sys.exit(1)
    
    # Check database connection
    if not settings.database_url:
        print("ERROR: DATABASE_URL not set in environment variables")
        print("Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    apify_service = ApifyService()
    
    try:
        # Verify zone exists
        async for db in get_db():
            zone = await ZoneService.get_zone(db, zone_id)
            if not zone:
                print(f"ERROR: Zone {zone_id} not found")
                print("Available zones:")
                zones = await ZoneService.list_zones(db, active_only=False)
                for z in zones:
                    print(f"  - {z.id}: {z.name} ({z.state})")
                sys.exit(1)
            
            print(f"✓ Found zone: {zone.name} ({zone.state})")
            print(f"\nDownloading Apify data and importing to Supabase...")
            print(f"  Zone ID: {zone_id}")
            print(f"  Max runs: {limit_runs}")
            if limit_items_per_run:
                print(f"  Max items per run: {limit_items_per_run}")
            print()
            
            # Download all towing data
            result = await apify_service.download_all_towing_data(
                limit_runs=limit_runs,
                limit_items_per_run=limit_items_per_run
            )
            
            print(f"\nDownload Summary:")
            print(f"  Total runs processed: {result['total_runs']}")
            print(f"  Total companies downloaded: {result['total_companies']}")
            
            # Import companies
            imported_count = 0
            updated_count = 0
            error_count = 0
            
            for run in result['runs']:
                if not run.get('downloaded'):
                    print(f"\n⚠ Skipping run {run['run_id']}: {run.get('error', 'Not downloaded')}")
                    continue
                
                # Download companies from this run
                run_id = run['run_id']
                companies_count = run.get('companies_count', 0)
                
                if companies_count == 0:
                    print(f"\n⚠ Run {run_id} has no companies")
                    continue
                
                print(f"\n📦 Downloading {companies_count} companies from run {run_id}...")
                
                try:
                    companies_data = await apify_service.download_run_data(
                        run_id=run_id,
                        limit=limit_items_per_run
                    )
                except Exception as e:
                    print(f"  ⚠ Error downloading run {run_id}: {e}")
                    error_count += companies_count
                    continue
                
                if not companies_data:
                    print(f"  ⚠ No companies returned from run {run_id}")
                    continue
                
                print(f"  ✓ Downloaded {len(companies_data)} companies, importing...")
                
                batch_imported = 0
                batch_updated = 0
                batch_errors = 0
                
                for company_data in companies_data:
                    try:
                        # Map Apify data to our schema
                        mapped_data = apify_service._map_apify_result(company_data)
                        if not mapped_data:
                            batch_errors += 1
                            continue
                        
                        # Check if company exists (for stats)
                        google_url = mapped_data.get('google_business_url')
                        if google_url:
                            from sqlalchemy import select
                            from app.models.company import Company
                            result_check = await db.execute(
                                select(Company).where(Company.google_business_url == google_url)
                            )
                            existing = result_check.scalar_one_or_none()
                            
                            if existing:
                                batch_updated += 1
                            else:
                                batch_imported += 1
                        
                        # Create or update company
                        company = await CompanyService.create_or_update_company(
                            db,
                            mapped_data,
                            zone_id
                        )
                        
                        # Set scraping stage
                        if not company.scraping_stage:
                            company.scraping_stage = 'google_maps'
                            await db.commit()
                            await db.refresh(company)
                        
                    except Exception as e:
                        batch_errors += 1
                        print(f"    ⚠ Error importing company: {e}")
                        continue
                
                await db.commit()
                imported_count += batch_imported
                updated_count += batch_updated
                error_count += batch_errors
                
                print(f"  ✓ Imported: {batch_imported} new, {batch_updated} updated, {batch_errors} errors")
            
            print(f"\n{'='*60}")
            print(f"Import Complete!")
            print(f"{'='*60}")
            print(f"  ✓ New companies imported: {imported_count}")
            print(f"  ✓ Companies updated: {updated_count}")
            print(f"  ✗ Errors: {error_count}")
            print(f"  Total processed: {imported_count + updated_count}")
            
            # Get final counts
            from sqlalchemy import select, func
            from app.models.company import Company
            total_result = await db.execute(
                select(func.count(Company.id)).where(Company.zone_id == zone_id)
            )
            total_companies = total_result.scalar_one()
            print(f"\n  Total companies in zone '{zone.name}': {total_companies}")
            
            break  # Exit the async generator
    
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await apify_service.close()


async def main():
    parser = argparse.ArgumentParser(description="Import Apify datasets into Supabase")
    parser.add_argument(
        "--zone-id",
        type=str,
        required=True,
        help="Zone UUID to import companies into",
    )
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
    
    args = parser.parse_args()
    
    try:
        zone_id = UUID(args.zone_id)
    except ValueError:
        print(f"ERROR: Invalid zone ID format: {args.zone_id}")
        print("Zone ID must be a valid UUID")
        sys.exit(1)
    
    await import_apify_data_to_supabase(
        zone_id=zone_id,
        limit_runs=args.limit_runs,
        limit_items_per_run=args.limit_items
    )


if __name__ == "__main__":
    asyncio.run(main())

