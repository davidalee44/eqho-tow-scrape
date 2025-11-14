"""ApifyRun model"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base


class ApifyRun(Base):
    """Model for tracking Apify crawl runs"""
    __tablename__ = "apify_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(String, nullable=False, unique=True)  # Apify run ID
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    
    # Crawl metadata
    location = Column(String, nullable=True)
    query = Column(String, nullable=True)
    status = Column(String, nullable=True)  # Apify status: RUNNING, SUCCEEDED, FAILED, etc.
    items_count = Column(Integer, nullable=True)
    
    # Processing status
    processing_status = Column(String, nullable=True, default='pending')  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    webhook_received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

