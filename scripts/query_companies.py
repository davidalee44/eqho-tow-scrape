#!/usr/bin/env python3
"""
Script to query and analyze company data in Supabase

Usage:
    make query-companies [ZONE_ID=<uuid>] [STATE=<state>] [HAS_IMPOUND=true]
    Or: python scripts/query_companies.py [--zone-id <uuid>] [--state <state>] [--has-impound]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from uuid import UUID
from typing import Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.services.company_service import CompanyService
from app.services.zone_service import ZoneService
from sqlalchemy import select, func, and_
from app.models.company import Company
from app.models.zone import Zone


async def query_companies(
    zone_id: Optional[UUID] = None,
    state: Optional[str] = None,
    has_impound: Optional[bool] = None,
    limit: int = 100
):
    """Query and display company statistics"""
    
    async for db in get_db():
        # Build query
        query = select(Company)
        conditions = []
        
        if zone_id:
            conditions.append(Company.zone_id == zone_id)
        
        if state:
            conditions.append(Company.address_state == state.upper())
        
        if has_impound is not None:
            conditions.append(Company.has_impound_service == has_impound)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.limit(limit)
        
        # Execute query
        result = await db.execute(query)
        companies = result.scalars().all()
        
        # Get statistics
        stats_query = select(
            func.count(Company.id).label('total'),
            func.count(Company.website).label('with_website'),
            func.count(Company.has_impound_service).filter(Company.has_impound_service == True).label('with_impound'),
            func.avg(Company.rating).label('avg_rating'),
            func.sum(Company.review_count).label('total_reviews'),
            func.count(Company.scraping_stage).label('scraped')
        )
        
        if conditions:
            stats_query = stats_query.where(and_(*conditions))
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.first()
        
        # Get zone info if zone_id provided
        zone_name = None
        if zone_id:
            zone = await ZoneService.get_zone(db, zone_id)
            if zone:
                zone_name = f"{zone.name}, {zone.state}"
        
        # Display results
        print("="*80)
        print("COMPANY DATA ANALYSIS")
        print("="*80)
        
        if zone_name:
            print(f"\nZone: {zone_name}")
        if state:
            print(f"State: {state.upper()}")
        if has_impound is not None:
            print(f"Has Impound Service: {has_impound}")
        
        print(f"\n📊 Statistics:")
        print(f"  Total Companies: {stats.total or 0}")
        print(f"  With Website: {stats.with_website or 0} ({stats.with_website / max(stats.total, 1) * 100:.1f}%)")
        print(f"  With Impound Service: {stats.with_impound or 0} ({stats.with_impound / max(stats.total, 1) * 100:.1f}%)")
        print(f"  Average Rating: {stats.avg_rating:.2f}" if stats.avg_rating else "  Average Rating: N/A")
        print(f"  Total Reviews: {stats.total_reviews or 0:,}")
        print(f"  Scraped: {stats.scraped or 0}")
        
        # Scraping stage breakdown
        stage_query = select(
            Company.scraping_stage,
            func.count(Company.id).label('count')
        )
        if conditions:
            stage_query = stage_query.where(and_(*conditions))
        stage_query = stage_query.group_by(Company.scraping_stage)
        
        stage_result = await db.execute(stage_query)
        stages = stage_result.all()
        
        if stages:
            print(f"\n📈 Scraping Stage Breakdown:")
            for stage, count in stages:
                stage_name = stage or 'initial'
                percentage = count / max(stats.total, 1) * 100
                print(f"  {stage_name}: {count} ({percentage:.1f}%)")
        
        # State breakdown (if not filtering by state)
        if not state:
            state_query = select(
                Company.address_state,
                func.count(Company.id).label('count')
            )
            if zone_id:
                state_query = state_query.where(Company.zone_id == zone_id)
            state_query = state_query.group_by(Company.address_state).order_by(func.count(Company.id).desc())
            
            state_result = await db.execute(state_query)
            states = state_result.all()
            
            if states:
                print(f"\n🗺️  State Breakdown:")
                for state_code, count in states[:10]:  # Top 10
                    if state_code:
                        print(f"  {state_code}: {count}")
        
        # Sample companies
        print(f"\n📋 Sample Companies (showing {min(len(companies), 10)}):")
        for i, company in enumerate(companies[:10], 1):
            print(f"\n  {i}. {company.name}")
            print(f"     📍 {company.address_city}, {company.address_state} {company.address_zip}")
            print(f"     📞 {company.phone_primary}")
            if company.website:
                print(f"     🌐 {company.website}")
            if company.rating:
                print(f"     ⭐ {company.rating:.1f} ({company.review_count or 0} reviews)")
            if company.has_impound_service:
                print(f"     🚗 Has Impound Service")
            print(f"     Stage: {company.scraping_stage or 'initial'}")
        
        break  # Exit the async generator


async def main():
    parser = argparse.ArgumentParser(description="Query and analyze company data")
    parser.add_argument(
        "--zone-id",
        type=str,
        default=None,
        help="Filter by zone UUID",
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Filter by state code (e.g., UT, TX)",
    )
    parser.add_argument(
        "--has-impound",
        action="store_true",
        help="Only show companies with impound service",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum companies to return (default: 100)",
    )
    
    args = parser.parse_args()
    
    zone_id = None
    if args.zone_id:
        try:
            zone_id = UUID(args.zone_id)
        except ValueError:
            print(f"ERROR: Invalid zone ID format: {args.zone_id}")
            sys.exit(1)
    
    has_impound = None
    if args.has_impound:
        has_impound = True
    
    await query_companies(
        zone_id=zone_id,
        state=args.state,
        has_impound=has_impound,
        limit=args.limit
    )


if __name__ == "__main__":
    asyncio.run(main())

