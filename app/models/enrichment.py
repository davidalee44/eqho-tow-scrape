"""Enrichment models"""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class EnrichmentSnapshot(Base):
    """Enrichment snapshot model"""
    __tablename__ = "enrichment_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    snapshot_data = Column(JSON, nullable=False)
    enrichment_source = Column(String, nullable=False)  # 'facebook', 'google', 'website', 'manual'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="enrichment_snapshots")

