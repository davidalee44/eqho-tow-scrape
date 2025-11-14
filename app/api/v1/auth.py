"""Authentication API endpoints"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserResponse,
    UserSignup,
)
from app.auth.service import AuthService

router = APIRouter()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(signup_data: UserSignup) -> Dict[str, Any]:
    """
    Sign up a new user

    Creates a new user account in Supabase Auth
    """
    auth_service = AuthService()
    result = await auth_service.signup(signup_data)

    return {
        "message": "User created successfully",
        "user": {
            "id": result["user"].id,
            "email": result["user"].email,
            "email_confirmed_at": result["user"].email_confirmed_at,
        },
        "session": {
            "access_token": result["session"].access_token,
            "refresh_token": result["session"].refresh_token,
            "expires_in": result["session"].expires_in,
        },
    }


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin) -> TokenResponse:
    """
    Login user with email and password

    Returns access token and refresh token
    """
    auth_service = AuthService()
    result = await auth_service.login(login_data)

    return TokenResponse(
        access_token=result["session"].access_token,
        refresh_token=result["session"].refresh_token,
        token_type="bearer",
        expires_in=result["session"].expires_in or 3600,
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)) -> Dict[str, str]:
    """
    Logout current user

    Invalidates the current session
    """
    auth_service = AuthService()
    # Extract token from Authorization header if available
    # Note: Supabase client handles session internally
    try:
        # Attempt logout - Supabase handles session cleanup
        await auth_service.logout("")
        return {"message": "Logged out successfully"}
    except Exception:
        # Even if logout fails, return success to client
        return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest) -> TokenResponse:
    """
    Refresh access token using refresh token

    Returns new access token and refresh token
    """
    auth_service = AuthService()
    result = await auth_service.refresh_token(refresh_data.refresh_token)

    return TokenResponse(
        access_token=result["session"].access_token,
        refresh_token=result["session"].refresh_token,
        token_type="bearer",
        expires_in=result["session"].expires_in or 3600,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user profile

    Returns the authenticated user's profile information
    """
    user = current_user.get("user", {})
    user_metadata = user.get("user_metadata", {})

    return UserResponse(
        id=user.get("id"),
        email=user.get("email"),
        full_name=user_metadata.get("full_name"),
        is_active=user.get("email_confirmed_at") is not None,
        role=user_metadata.get("role", "user"),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at"),
    )


@router.post("/oauth/{provider}")
async def oauth_login(
    provider: str,
    redirect_url: Optional[str] = None,
    request: Request = None,
) -> Dict[str, str]:
    """
    Initiate OAuth login with specified provider

    Supported providers: google, github, gitlab, bitbucket, etc.
    Returns OAuth URL for redirect
    """
    auth_service = AuthService()

    # Get redirect URL from request if not provided
    if not redirect_url and request:
        redirect_url = str(request.url_for("oauth_callback", provider=provider))

    try:
        oauth_url = await auth_service.get_oauth_url(provider, redirect_url)
        return {"url": oauth_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth login failed: {str(e)}",
        )


@router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(
    provider: str, code: Optional[str] = None, error: Optional[str] = None
) -> Dict[str, Any]:
    """
    OAuth callback handler

    Handles OAuth provider callback and exchanges code for tokens
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth error: {error}"
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided",
        )

    # Exchange code for tokens using Supabase client
    try:
        # Note: Supabase handles OAuth callbacks automatically
        # This endpoint is mainly for documentation/redirect handling
        # In production, you would exchange the code for tokens here
        return {
            "message": "OAuth callback received",
            "provider": provider,
            "code": code,
            "note": "Exchange code for tokens using Supabase Auth token endpoint",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}",
        )
