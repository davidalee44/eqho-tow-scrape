"""Tests for authentication service"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.auth.service import AuthService
from app.auth.schemas import UserSignup, UserLogin


@pytest.mark.asyncio
async def test_signup_success():
    """Test successful user signup"""
    with patch('app.auth.service.get_supabase_client') as mock_client, \
         patch('app.auth.service.get_supabase_anon_client') as mock_anon_client:
        mock_supabase = MagicMock()
        mock_anon_supabase = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.email_confirmed_at = None
        
        mock_session = MagicMock()
        mock_session.access_token = "test-access-token"
        mock_session.refresh_token = "test-refresh-token"
        mock_session.expires_in = 3600
        
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        
        mock_supabase.auth.sign_up.return_value = mock_response
        mock_client.return_value = mock_supabase
        mock_anon_client.return_value = mock_anon_supabase
        
        auth_service = AuthService()
        signup_data = UserSignup(
            email="test@example.com",
            password="testpassword123",
            full_name="Test User"
        )
        
        result = await auth_service.signup(signup_data)
        
        assert result["user"] == mock_user
        assert result["session"] == mock_session
        mock_supabase.auth.sign_up.assert_called_once()


@pytest.mark.asyncio
async def test_login_success():
    """Test successful user login"""
    with patch('app.auth.service.get_supabase_client') as mock_client, \
         patch('app.auth.service.get_supabase_anon_client') as mock_anon_client:
        mock_supabase = MagicMock()
        mock_anon_supabase = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        
        mock_session = MagicMock()
        mock_session.access_token = "test-access-token"
        mock_session.refresh_token = "test-refresh-token"
        mock_session.expires_in = 3600
        
        mock_response = MagicMock()
        mock_response.user = mock_user
        mock_response.session = mock_session
        
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        mock_client.return_value = mock_supabase
        mock_anon_client.return_value = mock_anon_supabase
        
        auth_service = AuthService()
        login_data = UserLogin(
            email="test@example.com",
            password="testpassword123"
        )
        
        result = await auth_service.login(login_data)
        
        assert result["user"] == mock_user
        assert result["session"] == mock_session


@pytest.mark.asyncio
async def test_refresh_token_success():
    """Test successful token refresh"""
    with patch('app.auth.service.get_supabase_client') as mock_client, \
         patch('app.auth.service.get_supabase_anon_client') as mock_anon_client:
        mock_supabase = MagicMock()
        mock_anon_supabase = MagicMock()
        mock_session = MagicMock()
        mock_session.access_token = "new-access-token"
        mock_session.refresh_token = "new-refresh-token"
        mock_session.expires_in = 3600
        
        mock_response = MagicMock()
        mock_response.session = mock_session
        
        mock_supabase.auth.refresh_session.return_value = mock_response
        mock_client.return_value = mock_supabase
        mock_anon_client.return_value = mock_anon_supabase
        
        auth_service = AuthService()
        result = await auth_service.refresh_token("old-refresh-token")
        
        assert result["session"] == mock_session

