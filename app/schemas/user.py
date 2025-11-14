"""User schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"


class UserCreate(UserBase):
    """User creation schema"""
    auth_user_id: UUID
    user_metadata: Optional[Dict[str, Any]] = None


class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    user_metadata: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """User response schema"""
    id: UUID
    auth_user_id: UUID
    is_active: bool
    user_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response with pagination"""
    users: list[UserResponse]
    total: int
    limit: int
    offset: int

