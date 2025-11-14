"""Zone service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from app.models.zone import Zone
from app.schemas.zone import ZoneCreate, ZoneUpdate


class ZoneService:
    """Service for zone operations"""
    
    @staticmethod
    async def create_zone(db: AsyncSession, zone_data: ZoneCreate) -> Zone:
        """Create a new zone"""
        zone = Zone(**zone_data.model_dump())
        db.add(zone)
        await db.commit()
        await db.refresh(zone)
        return zone
    
    @staticmethod
    async def get_zone(db: AsyncSession, zone_id: UUID) -> Optional[Zone]:
        """Get zone by ID"""
        result = await db.execute(select(Zone).where(Zone.id == zone_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_zones(db: AsyncSession, active_only: bool = True) -> List[Zone]:
        """List zones"""
        query = select(Zone)
        if active_only:
            query = query.where(Zone.is_active == True)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_zone(db: AsyncSession, zone_id: UUID, zone_data: ZoneUpdate) -> Optional[Zone]:
        """Update zone"""
        zone = await ZoneService.get_zone(db, zone_id)
        if not zone:
            return None
        
        update_data = zone_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(zone, field, value)
        
        await db.commit()
        await db.refresh(zone)
        return zone
    
    @staticmethod
    async def delete_zone(db: AsyncSession, zone_id: UUID) -> bool:
        """Deactivate zone (soft delete)"""
        zone = await ZoneService.get_zone(db, zone_id)
        if not zone:
            return False
        
        zone.is_active = False
        await db.commit()
        return True
    
    @staticmethod
    async def get_companies_by_zone(db: AsyncSession, zone_id: UUID) -> List:
        """Get companies for a zone"""
        zone = await ZoneService.get_zone(db, zone_id)
        if not zone:
            return []
        return zone.companies

