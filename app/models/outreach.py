"""Outreach models"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class OutreachHistory(Base):
    """Outreach history model"""
    __tablename__ = "outreach_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    channel = Column(String, nullable=False)  # 'email', 'sms', 'phone'
    status = Column(String, nullable=False)  # 'pending', 'sent', 'delivered', 'opened', 'clicked', 'replied', 'failed'
    message_content = Column(Text, nullable=False)
    external_id = Column(String, nullable=True)  # ID from email/SMS provider
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    outreach_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (SQLAlchemy reserved)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="outreach_history")


class OutreachSequence(Base):
    """Outreach sequence model"""
    __tablename__ = "outreach_sequences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    steps = Column(JSON, nullable=False)  # Array of sequence steps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    assignments = relationship("OutreachAssignment", back_populates="sequence")


class OutreachAssignment(Base):
    """Outreach assignment model"""
    __tablename__ = "outreach_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    sequence_id = Column(UUID(as_uuid=True), ForeignKey("outreach_sequences.id"), nullable=False)
    current_step = Column(Integer, default=0, nullable=False)
    status = Column(String, nullable=False)  # 'pending', 'active', 'paused', 'completed', 'opted_out'
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="outreach_assignments")
    sequence = relationship("OutreachSequence", back_populates="assignments")

