"""Company model"""
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Company(Base):
    """Company model for towing companies"""
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=False)
    
    # Contact information
    phone_primary = Column(String, nullable=False)
    phone_dispatch = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    facebook_page = Column(String, nullable=True)
    google_business_url = Column(String, nullable=False)
    
    # Address
    address_street = Column(String, nullable=False)
    address_city = Column(String, nullable=False)
    address_state = Column(String, nullable=False)
    address_zip = Column(String, nullable=False)
    
    # Business details
    is_24_7 = Column(Boolean, nullable=True)
    service_radius = Column(String, nullable=True)
    fleet_size = Column(String, nullable=True)  # 'small', 'medium', 'large'
    review_count = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    
    # Hours and services
    hours = Column(JSON, nullable=True)  # From Google/Facebook
    hours_website = Column(JSON, nullable=True)  # From website scraping
    services = Column(JSON, nullable=True)  # Array of service types
    
    # Website scraping
    has_impound_service = Column(Boolean, nullable=True)
    impound_confidence = Column(Float, nullable=True)  # 0.0-1.0
    website_scraped_at = Column(DateTime, nullable=True)
    website_scrape_status = Column(String, nullable=True)  # 'pending', 'success', 'failed', 'no_website'
    
    # Metadata
    source = Column(String, default="apify_google_maps", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    zone = relationship("Zone", back_populates="companies")
    enrichment_snapshots = relationship("EnrichmentSnapshot", back_populates="company")
    outreach_history = relationship("OutreachHistory", back_populates="company")
    outreach_assignments = relationship("OutreachAssignment", back_populates="company")

