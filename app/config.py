"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional, Dict
import os
import asyncio
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Supabase/Database
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: Optional[str] = None
    database_url: str = "sqlite+aiosqlite:///:memory:"
    
    # Supabase Auth
    supabase_auth_enabled: bool = True
    supabase_jwt_secret: Optional[str] = None  # JWT secret for token validation
    supabase_auth_url: Optional[str] = None  # Auth URL (usually {supabase_url}/auth/v1)
    
    # Environment variable management
    use_supabase_env_vars: bool = False  # Enable to fetch env vars from Supabase
    env_cache_ttl: int = 300  # Cache TTL in seconds for env vars
    
    # Apify
    apify_token: str = ""
    
    # Eqho.ai Integration
    eqho_api_token: str = ""
    eqho_api_url: Optional[str] = None  # Defaults to https://api.eqho.ai/v1
    eqho_default_campaign_id: Optional[str] = None  # Default campaign for TowPilot outreach
    eqho_admin_username: Optional[str] = None  # Admin username for admin endpoints
    eqho_admin_password: Optional[str] = None  # Admin password for admin endpoints
    
    # Outreach Providers (Legacy - prefer Eqho.ai)
    email_provider_api_key: Optional[str] = None
    sms_provider_api_key: Optional[str] = None
    phone_provider_api_key: Optional[str] = None
    outreach_webhook_url: Optional[str] = None
    
    # Playwright Configuration
    playwright_headless: bool = True
    playwright_timeout: int = 30000
    website_scrape_concurrent: int = 5
    
    # Application
    log_level: str = "INFO"
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set auth URL if not provided
        if not self.supabase_auth_url and self.supabase_url:
            self.supabase_auth_url = f"{self.supabase_url}/auth/v1"
        
        # Load env vars from Supabase if enabled
        if self.use_supabase_env_vars and self.database_url:
            self._load_env_from_supabase()
    
    def _load_env_from_supabase(self):
        """
        Load environment variables from Supabase
        
        This is called during initialization. For async loading,
        use load_env_from_supabase_async() instead.
        """
        try:
            # Try to load synchronously (fallback to .env if fails)
            # In practice, this should be called async after app startup
            pass
        except Exception:
            # Fallback to .env file
            pass
    
    async def load_env_from_supabase_async(self) -> Dict[str, str]:
        """
        Async method to load environment variables from Supabase
        
        Call this after database connection is established
        """
        if not self.use_supabase_env_vars:
            return {}
        
        try:
            from app.database import AsyncSessionLocal
            from app.services.env_service import EnvService
            
            async with AsyncSessionLocal() as session:
                env_vars = await EnvService.load_all_env_vars(session, self.environment)
                
                # Update settings with loaded env vars
                for key, value in env_vars.items():
                    if hasattr(self, key.lower()):
                        setattr(self, key.lower(), value)
                    # Also set as environment variable
                    os.environ[key] = value
                
                return env_vars
        except Exception as e:
            # Log error but don't fail - fallback to .env
            print(f"Warning: Failed to load env vars from Supabase: {e}")
            return {}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

