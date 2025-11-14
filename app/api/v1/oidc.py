"""OpenID Connect endpoints for third-party integrations"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from app.config import settings
from app.auth.dependencies import get_current_user, get_optional_user

router = APIRouter()


@router.get("/.well-known/openid-configuration")
async def openid_configuration() -> Dict[str, Any]:
    """
    OpenID Connect Discovery endpoint
    
    Returns OIDC configuration for third-party integrations
    """
    base_url = settings.supabase_url or "https://your-project.supabase.co"
    auth_url = settings.supabase_auth_url or f"{base_url}/auth/v1"
    
    return {
        "issuer": auth_url,
        "authorization_endpoint": f"{auth_url}/authorize",
        "token_endpoint": f"{auth_url}/token",
        "userinfo_endpoint": f"{auth_url}/userinfo",
        "jwks_uri": f"{auth_url}/.well-known/jwks.json",
        "response_types_supported": [
            "code",
            "token",
            "id_token",
            "code token",
            "code id_token",
            "token id_token",
            "code token id_token"
        ],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": [
            "openid",
            "profile",
            "email",
            "offline_access"
        ],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post"
        ],
        "claims_supported": [
            "sub",
            "iss",
            "aud",
            "exp",
            "iat",
            "auth_time",
            "email",
            "email_verified",
            "name",
            "preferred_username",
            "picture"
        ]
    }


@router.get("/userinfo")
async def userinfo(
    current_user: Optional[dict] = Depends(get_optional_user)
) -> Dict[str, Any]:
    """
    OpenID Connect UserInfo endpoint
    
    Returns user information for authenticated users
    """
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = current_user.get("user", {})
    user_metadata = user.get("user_metadata", {})
    
    return {
        "sub": user.get("id"),  # Subject identifier
        "email": user.get("email"),
        "email_verified": user.get("email_confirmed_at") is not None,
        "name": user_metadata.get("full_name") or user.get("email"),
        "preferred_username": user.get("email"),
        "picture": user_metadata.get("avatar_url"),
        "updated_at": user.get("updated_at")
    }


@router.post("/token")
async def token(
    grant_type: str = Query(...),
    code: Optional[str] = Query(None),
    redirect_uri: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    client_secret: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    OpenID Connect Token endpoint
    
    Exchanges authorization code for tokens
    Note: This delegates to Supabase Auth token endpoint
    """
    # Redirect to Supabase Auth token endpoint
    # In practice, you might want to proxy this or handle it directly
    auth_url = settings.supabase_auth_url or f"{settings.supabase_url}/auth/v1"
    
    return {
        "message": "Token endpoint - use Supabase Auth directly",
        "token_endpoint": f"{auth_url}/token",
        "note": "For OIDC token exchange, use Supabase Auth token endpoint directly"
    }


@router.get("/authorize")
async def authorize(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query("code"),
    scope: str = Query("openid profile email"),
    state: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    OpenID Connect Authorization endpoint
    
    Initiates OAuth/OIDC authorization flow
    """
    auth_url = settings.supabase_auth_url or f"{settings.supabase_url}/auth/v1"
    
    return {
        "message": "Authorization endpoint - use Supabase Auth directly",
        "authorization_endpoint": f"{auth_url}/authorize",
        "parameters": {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "scope": scope,
            "state": state
        },
        "note": "For OIDC authorization, use Supabase Auth authorize endpoint directly"
    }


@router.get("/jwks.json")
async def jwks() -> Dict[str, Any]:
    """
    JSON Web Key Set endpoint
    
    Returns public keys for token verification
    """
    auth_url = settings.supabase_auth_url or f"{settings.supabase_url}/auth/v1"
    
    # Redirect to Supabase JWKS endpoint
    return {
        "message": "JWKS endpoint - use Supabase Auth directly",
        "jwks_uri": f"{auth_url}/.well-known/jwks.json",
        "note": "For JWKS, use Supabase Auth JWKS endpoint directly"
    }

