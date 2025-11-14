"""Authentication-related Pydantic schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserSignup(BaseModel):
    """User signup request"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class OAuthProviderRequest(BaseModel):
    """OAuth provider login request"""
    provider: str
    redirect_url: Optional[str] = None

