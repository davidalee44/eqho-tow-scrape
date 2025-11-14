#!/usr/bin/env python3
"""
Script to list zones in the database

Usage:
    make list-zones
    Or: python scripts/list_zones.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db
from app.services.zone_service import ZoneService


async def list_zones():
    """List all zones"""
    async for db in get_db():
        zones = await ZoneService.list_zones(db, active_only=False)
        
        if not zones:
            print("No zones found in database.")
            print("\nTo create a zone, use the API:")
            print("  POST /api/v1/zones")
            print("  Body: {\"name\": \"Zone Name\", \"state\": \"UT\", \"zone_type\": \"city\"}")
            return
        
        print("="*80)
        print("ZONES")
        print("="*80)
        print()
        
        for zone in zones:
            status = "✓ Active" if zone.is_active else "✗ Inactive"
            print(f"ID: {zone.id}")
            print(f"  Name: {zone.name}")
            print(f"  State: {zone.state or 'N/A'}")
            print(f"  Type: {zone.zone_type}")
            print(f"  Status: {status}")
            print(f"  Created: {zone.created_at}")
            print()
        
        print(f"Total zones: {len(zones)}")
        break  # Exit the async generator


if __name__ == "__main__":
    asyncio.run(list_zones())

