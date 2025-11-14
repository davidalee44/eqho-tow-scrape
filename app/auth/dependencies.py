"""FastAPI dependencies for authentication"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.auth.service import AuthService
from app.config import settings


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User dictionary from Supabase Auth
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    auth_service = AuthService()
    
    try:
        access_token = credentials.credentials
        user_data = await auth_service.get_user(access_token)
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Active user dictionary
        
    Raises:
        HTTPException: If user is not active
    """
    # Check if user is active (Supabase Auth doesn't have is_active by default,
    # but we can check user metadata or email confirmation status)
    user = current_user.get("user", {})
    
    # Check email confirmation if required
    if not user.get("email_confirmed_at") and settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not confirmed"
        )
    
    return current_user


async def get_current_admin_user(
    current_user: dict = Depends(get_current_active_user)
) -> dict:
    """
    Dependency to get current admin user
    
    Args:
        current_user: Current active user
        
    Returns:
        Admin user dictionary
        
    Raises:
        HTTPException: If user is not admin
    """
    user = current_user.get("user", {})
    user_metadata = user.get("user_metadata", {})
    role = user_metadata.get("role", "user")
    
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """
    Optional dependency to get current user if token is provided
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        User dictionary if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        auth_service = AuthService()
        access_token = credentials.credentials
        user_data = await auth_service.get_user(access_token)
        return user_data
    except Exception:
        return None

