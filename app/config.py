"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Supabase/Database
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: Optional[str] = None
    database_url: str = "sqlite+aiosqlite:///:memory:"
    
    # Apify
    apify_token: str = ""
    
    # Outreach Providers
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


settings = Settings()

