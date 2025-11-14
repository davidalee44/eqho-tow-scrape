"""Authentication service layer"""
from supabase import Client
from typing import Optional, Dict, Any
from app.auth.client import get_supabase_client, get_supabase_anon_client
from app.auth.schemas import UserSignup, UserLogin, TokenResponse
from app.config import settings
from fastapi import HTTPException, status


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self):
        self.client: Client = get_supabase_client()
        self.anon_client: Client = get_supabase_anon_client()
    
    async def signup(self, signup_data: UserSignup) -> Dict[str, Any]:
        """Sign up a new user"""
        try:
            # Create user in Supabase Auth
            response = self.client.auth.sign_up({
                "email": signup_data.email,
                "password": signup_data.password,
                "options": {
                    "data": {
                        "full_name": signup_data.full_name or ""
                    }
                }
            })
            
            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user"
                )
            
            return {
                "user": response.user,
                "session": response.session
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signup failed: {str(e)}"
            )
    
    async def login(self, login_data: UserLogin) -> Dict[str, Any]:
        """Login user with email and password"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if not response.user or not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            return {
                "user": response.user,
                "session": response.session
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed: {str(e)}"
            )
    
    async def logout(self, access_token: str) -> None:
        """Logout user"""
        try:
            # Set the session for the client
            self.client.auth.set_session(access_token, "")
            self.client.auth.sign_out()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Logout failed: {str(e)}"
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            response = self.client.auth.refresh_session(refresh_token)
            
            if not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            return {
                "session": response.session
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token refresh failed: {str(e)}"
            )
    
    async def get_user(self, access_token: str) -> Dict[str, Any]:
        """Get user from access token"""
        try:
            # Set the session to validate the token
            self.client.auth.set_session(access_token, "")
            user = self.client.auth.get_user(access_token)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )
    
    async def get_oauth_url(self, provider: str, redirect_url: Optional[str] = None) -> str:
        """Get OAuth provider URL"""
        try:
            response = self.client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "redirect_to": redirect_url or f"{settings.supabase_url}/auth/callback"
                }
            })
            return response.url
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth URL generation failed: {str(e)}"
            )

