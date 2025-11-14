"""Zone model"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Zone(Base):
    """Zone model for geographic targeting"""
    __tablename__ = "zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    state = Column(String, nullable=True)
    zone_type = Column(String, nullable=False)  # 'city', 'state', 'custom_geo'
    geo_data = Column(JSON, nullable=True)  # For future coordinates/polygons
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    companies = relationship("Company", back_populates="zone")

