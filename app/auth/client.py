"""Supabase Auth client initialization"""
from supabase import create_client, Client
from app.config import settings
from typing import Optional

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client instance"""
    global _supabase_client
    
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError("Supabase URL and service role key must be configured")
        
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
    
    return _supabase_client


def get_supabase_anon_client() -> Client:
    """Get Supabase client with anon key (for client-side operations)"""
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Supabase URL and anon key must be configured")
    
    return create_client(
        settings.supabase_url,
        settings.supabase_key
    )

