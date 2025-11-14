"""Authentication middleware"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Optional
from app.auth.dependencies import get_current_user


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate authentication for protected routes
    
    Note: This is optional if using dependencies. Dependencies are preferred
    for more granular control.
    """
    
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/auth/signup",
            "/api/v1/auth/login",
            "/api/v1/auth/oauth",
            "/.well-known/openid-configuration",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Check authentication for non-excluded paths"""
        path = request.url.path
        
        # Skip auth check for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Continue with request
        response = await call_next(request)
        return response

