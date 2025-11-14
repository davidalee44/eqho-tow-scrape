#!/usr/bin/env python3
"""
Monitor import progress in real-time

Usage:
    python scripts/monitor_import.py [--log-file /tmp/import_log.txt]
"""
import asyncio
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.models.company import Company
from sqlalchemy import select, func


async def check_progress():
    """Check current import progress"""
    async for db in get_db():
        # Count companies
        result = await db.execute(select(func.count(Company.id)))
        company_count = result.scalar()
        
        # Count by state
        result2 = await db.execute(
            select(Company.address_state, func.count(Company.id))
            .group_by(Company.address_state)
        )
        by_state = {row[0]: row[1] for row in result2.fetchall()}
        
        # Count by scraping stage
        result3 = await db.execute(
            select(Company.scraping_stage, func.count(Company.id))
            .group_by(Company.scraping_stage)
        )
        by_stage = {row[0] or 'None': row[1] for row in result3.fetchall()}
        
        print('\r' + '='*60)
        print(f'📊 IMPORT PROGRESS')
        print('='*60)
        print(f'Total companies: {company_count:,}')
        
        if by_state:
            print(f'\nBy State:')
            for state, count in sorted(by_state.items()):
                print(f'  {state}: {count:,}')
        
        if by_stage:
            print(f'\nBy Stage:')
            for stage, count in sorted(by_stage.items()):
                print(f'  {stage}: {count:,}')
        
        print('='*60 + '\r', end='', flush=True)
        
        break


async def monitor_loop(interval: int = 5):
    """Monitor progress every N seconds"""
    print("Monitoring import progress (Ctrl+C to stop)...\n")
    
    try:
        while True:
            await check_progress()
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


async def main():
    parser = argparse.ArgumentParser(description='Monitor import progress')
    parser.add_argument('--interval', type=int, default=5, help='Update interval in seconds')
    
    args = parser.parse_args()
    
    await monitor_loop(args.interval)


if __name__ == '__main__':
    asyncio.run(main())

