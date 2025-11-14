"""Environment configuration model"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base


class EnvironmentConfig(Base):
    """Model for storing environment variables in Supabase"""
    __tablename__ = "environment_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)  # Encrypted or plain text value
    is_encrypted = Column(Boolean, default=False, nullable=False)
    description = Column(String, nullable=True)
    environment = Column(String, nullable=False, default="production")  # 'production', 'staging', 'development'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)  # User who created/updated this config

