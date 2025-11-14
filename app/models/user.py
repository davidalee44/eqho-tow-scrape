"""User model"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base


class User(Base):
    """User profile model linked to Supabase auth.users"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Link to Supabase auth.users UUID
    auth_user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False)  # 'admin', 'user', 'readonly'
    is_active = Column(Boolean, default=True, nullable=False)
    # Store additional metadata from Supabase
    user_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

