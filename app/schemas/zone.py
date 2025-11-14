"""Zone schemas"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ZoneBase(BaseModel):
    name: str
    state: Optional[str] = None
    zone_type: str  # 'city', 'state', 'custom_geo'
    geo_data: Optional[Dict[str, Any]] = None
    is_active: bool = True


class ZoneCreate(ZoneBase):
    pass


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None
    zone_type: Optional[str] = None
    geo_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ZoneResponse(ZoneBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

