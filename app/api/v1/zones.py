"""Zone API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.database import get_db
from app.schemas.zone import ZoneCreate, ZoneUpdate, ZoneResponse
from app.services.zone_service import ZoneService

router = APIRouter()


@router.post("", response_model=ZoneResponse, status_code=201)
async def create_zone(
    zone_data: ZoneCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new zone"""
    return await ZoneService.create_zone(db, zone_data)


@router.get("", response_model=List[ZoneResponse])
async def list_zones(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List zones"""
    return await ZoneService.list_zones(db, active_only=active_only)


@router.get("/{zone_id}", response_model=ZoneResponse)
async def get_zone(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get zone details"""
    zone = await ZoneService.get_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.put("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: UUID,
    zone_data: ZoneUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update zone"""
    zone = await ZoneService.update_zone(db, zone_id, zone_data)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.delete("/{zone_id}", status_code=204)
async def delete_zone(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate zone"""
    success = await ZoneService.delete_zone(db, zone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Zone not found")

