#!/usr/bin/env python3
"""
Script to import companies from the all_towing_leads.json file

Usage:
    python scripts/import_from_json.py [--json-file path/to/file.json]
"""
import asyncio
import argparse
import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.services.company_service import CompanyService
from app.services.zone_service import ZoneService
from app.models.zone import Zone
from app.models.company import Company
from sqlalchemy import select


async def import_from_json(json_file: str = "all_towing_leads.json"):
    """Import companies from JSON file"""
    
    json_path = Path(json_file)
    if not json_path.exists():
        print(f"ERROR: JSON file not found: {json_file}")
        sys.exit(1)
    
    print(f"Loading companies from {json_file}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    companies_data = data.get('companies', [])
    print(f"Found {len(companies_data)} companies in JSON file")
    
    async for db in get_db():
        # Group companies by state
        by_state = defaultdict(list)
        
        for company_data in companies_data:
            state = company_data.get('address_state', 'Unknown')
            if state and state != 'Unknown' and state != '21060' and len(state) == 2:
                by_state[state].append(company_data)
        
        print(f'\nCompanies by state:')
        for state, companies in sorted(by_state.items()):
            print(f'  {state}: {len(companies)}')
        
        # Create or get zones for each state
        zones = {}
        for state in by_state.keys():
            result = await db.execute(
                select(Zone).where(Zone.state == state).where(Zone.zone_type == 'state')
            )
            zone = result.scalar_one_or_none()
            
            if not zone:
                zone = Zone(
                    name=f'{state} State',
                    zone_type='state',
                    state=state
                )
                db.add(zone)
                await db.commit()
                await db.refresh(zone)
                print(f'✓ Created zone: {zone.id} - {zone.name}')
            else:
                print(f'✓ Using existing zone: {zone.id} - {zone.name}')
            
            zones[state] = zone
        
        # Import companies
        print(f'\nImporting companies...')
        imported = 0
        updated = 0
        errors = 0
        
        for state, companies in by_state.items():
            zone = zones[state]
            print(f'\nImporting {len(companies)} companies for {state}...')
            
            for i, company_data in enumerate(companies, 1):
                try:
                    # Ensure required fields
                    if not company_data.get('name') or not company_data.get('google_business_url'):
                        errors += 1
                        if errors <= 5:
                            print(f'  ⚠ Skipping company {i}: missing name or google_business_url')
                        continue
                    
                    # Check if company already exists
                    google_url = company_data.get('google_business_url')
                    result_check = await db.execute(
                        select(Company).where(Company.google_business_url == google_url)
                    )
                    existing = result_check.scalar_one_or_none()
                    
                    if existing:
                        # Update existing company
                        for key, value in company_data.items():
                            if hasattr(existing, key) and key not in ['id', 'zone_id', 'created_at', 'updated_at']:
                                setattr(existing, key, value)
                        if not existing.scraping_stage:
                            existing.scraping_stage = 'google_maps'
                        updated += 1
                    else:
                        # Create new company
                        # Remove fields that don't exist in Company model
                        clean_data = {k: v for k, v in company_data.items() 
                                     if k not in ['latitude', 'longitude', 'photos', 'category', 'description', 'reviews']}
                        
                        company = await CompanyService.create_or_update_company(
                            db,
                            clean_data,
                            zone.id
                        )
                        
                        if not company.scraping_stage:
                            company.scraping_stage = 'google_maps'
                        
                        imported += 1
                    
                    # Commit every 100 companies
                    if (imported + updated) % 100 == 0:
                        await db.commit()
                        print(f'  Progress: {imported + updated}/{len(companies)}...')
                        
                except Exception as e:
                    errors += 1
                    if errors <= 10:
                        print(f'  ⚠ Error importing company {i}: {e}')
                    continue
            
            # Final commit for this state
            await db.commit()
            print(f'  ✓ Completed {state}: {imported} new, {updated} updated, {errors} errors')
        
        print(f'\n' + '='*60)
        print(f'IMPORT COMPLETE')
        print(f'='*60)
        print(f'  ✓ New companies imported: {imported}')
        print(f'  ✓ Companies updated: {updated}')
        print(f'  ✗ Errors: {errors}')
        print(f'  Total processed: {imported + updated}')
        
        break


async def main():
    parser = argparse.ArgumentParser(description='Import companies from JSON file')
    parser.add_argument('--json-file', default='all_towing_leads.json', help='Path to JSON file')
    
    args = parser.parse_args()
    
    await import_from_json(args.json_file)


if __name__ == '__main__':
    asyncio.run(main())

