#!/usr/bin/env python3
"""
Script to analyze imported company data

Usage:
    python scripts/analyze_imported_data.py [--state STATE] [--has-impound]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.models.company import Company
from app.models.zone import Zone
from sqlalchemy import select, func, and_


async def analyze_data(state: str = None, has_impound: bool = None):
    """Analyze imported company data"""
    
    async for db in get_db():
        # Build query
        query = select(Company)
        conditions = []
        
        if state:
            conditions.append(Company.address_state == state)
        if has_impound is not None:
            conditions.append(Company.has_impound_service == has_impound)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get companies
        result = await db.execute(query)
        companies = result.scalars().all()
        
        print('='*60)
        print('COMPANY DATA ANALYSIS')
        print('='*60)
        print(f'\nTotal companies: {len(companies):,}')
        
        if not companies:
            print('No companies found matching criteria')
            return
        
        # State breakdown
        states = Counter(c.address_state for c in companies if c.address_state)
        print(f'\n📍 State Breakdown:')
        for state_name, count in states.most_common(10):
            print(f'  {state_name}: {count:,}')
        
        # City breakdown (top 10)
        cities = Counter(c.address_city for c in companies if c.address_city)
        print(f'\n🏙️  Top Cities:')
        for city, count in cities.most_common(10):
            print(f'  {city}: {count:,}')
        
        # Companies with websites
        with_website = sum(1 for c in companies if c.website)
        print(f'\n🌐 Companies with websites: {with_website:,} ({with_website/len(companies)*100:.1f}%)')
        
        # Companies with ratings
        with_rating = sum(1 for c in companies if c.rating)
        if with_rating > 0:
            avg_rating = sum(c.rating for c in companies if c.rating) / with_rating
            print(f'⭐ Companies with ratings: {with_rating:,} ({with_rating/len(companies)*100:.1f}%)')
            print(f'   Average rating: {avg_rating:.2f}')
        
        # Total reviews
        total_reviews = sum(c.review_count or 0 for c in companies)
        print(f'📝 Total reviews: {total_reviews:,}')
        
        # Impound services
        with_impound = sum(1 for c in companies if c.has_impound_service)
        print(f'\n🚗 Companies with impound service: {with_impound:,} ({with_impound/len(companies)*100:.1f}%)')
        
        # Scraping stage breakdown
        stages = Counter(c.scraping_stage for c in companies if c.scraping_stage)
        print(f'\n📊 Scraping Stage Breakdown:')
        for stage, count in stages.most_common():
            print(f'  {stage}: {count:,}')
        
        # Sample companies
        print(f'\n📋 Sample Companies:')
        for i, c in enumerate(companies[:10], 1):
            print(f'  {i}. {c.name}')
            print(f'     📍 {c.address_city}, {c.address_state} | 📞 {c.phone_primary}')
            if c.rating:
                print(f'     ⭐ {c.rating:.1f} ({c.review_count or 0} reviews)')
            if c.has_impound_service:
                print(f'     🚗 Impound service available')
        
        break


async def main():
    parser = argparse.ArgumentParser(description='Analyze imported company data')
    parser.add_argument('--state', help='Filter by state (e.g., MD, UT)')
    parser.add_argument('--has-impound', action='store_true', help='Only show companies with impound service')
    
    args = parser.parse_args()
    
    await analyze_data(state=args.state, has_impound=args.has_impound if args.has_impound else None)


if __name__ == '__main__':
    asyncio.run(main())

