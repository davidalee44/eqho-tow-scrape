"""Company schemas"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class CompanyBase(BaseModel):
    name: str
    phone_primary: str
    phone_dispatch: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    facebook_page: Optional[str] = None
    google_business_url: str
    address_street: str
    address_city: str
    address_state: str
    address_zip: str


class CompanyCreate(CompanyBase):
    zone_id: UUID
    is_24_7: Optional[bool] = None
    service_radius: Optional[str] = None
    fleet_size: Optional[str] = None
    review_count: Optional[int] = None
    rating: Optional[float] = None
    hours: Optional[Dict[str, Any]] = None
    services: Optional[List[str]] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    phone_primary: Optional[str] = None
    phone_dispatch: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    facebook_page: Optional[str] = None
    google_business_url: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    is_24_7: Optional[bool] = None
    service_radius: Optional[str] = None
    fleet_size: Optional[str] = None
    review_count: Optional[int] = None
    rating: Optional[float] = None
    hours: Optional[Dict[str, Any]] = None
    hours_website: Optional[Dict[str, Any]] = None
    services: Optional[List[str]] = None
    has_impound_service: Optional[bool] = None
    impound_confidence: Optional[float] = None
    website_scrape_status: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: UUID
    zone_id: UUID
    is_24_7: Optional[bool] = None
    service_radius: Optional[str] = None
    fleet_size: Optional[str] = None
    review_count: Optional[int] = None
    rating: Optional[float] = None
    hours: Optional[Dict[str, Any]] = None
    hours_website: Optional[Dict[str, Any]] = None
    services: Optional[List[str]] = None
    has_impound_service: Optional[bool] = None
    impound_confidence: Optional[float] = None
    website_scraped_at: Optional[datetime] = None
    website_scrape_status: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

