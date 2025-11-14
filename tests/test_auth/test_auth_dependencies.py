"""Tests for authentication dependencies"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException
from app.auth.dependencies import get_current_user, get_current_active_user, get_current_admin_user


@pytest.mark.asyncio
async def test_get_current_user_success():
    """Test successful user authentication"""
    mock_credentials = MagicMock()
    mock_credentials.credentials = "valid-token"
    
    mock_user_data = {
        "user": {
            "id": "test-user-id",
            "email": "test@example.com",
            "email_confirmed_at": "2024-01-01T00:00:00Z"
        }
    }
    
    with patch('app.auth.dependencies.AuthService') as mock_auth_service_class:
        mock_auth_service = MagicMock()
        mock_auth_service.get_user = AsyncMock(return_value=mock_user_data)
        mock_auth_service_class.return_value = mock_auth_service
        
        result = await get_current_user(mock_credentials)
        assert result == mock_user_data


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test authentication with invalid token"""
    mock_credentials = MagicMock()
    mock_credentials.credentials = "invalid-token"
    
    with patch('app.auth.dependencies.AuthService') as mock_auth_service_class:
        mock_auth_service = MagicMock()
        mock_auth_service.get_user = AsyncMock(side_effect=Exception("Invalid token"))
        mock_auth_service_class.return_value = mock_auth_service
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)
        
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_admin_user_success():
    """Test admin user access"""
    mock_user_data = {
        "user": {
            "id": "admin-user-id",
            "email": "admin@example.com",
            "user_metadata": {"role": "admin"}
        }
    }
    
    result = await get_current_admin_user(mock_user_data)
    assert result == mock_user_data


@pytest.mark.asyncio
async def test_get_current_admin_user_non_admin():
    """Test non-admin user trying to access admin endpoint"""
    mock_user_data = {
        "user": {
            "id": "user-id",
            "email": "user@example.com",
            "user_metadata": {"role": "user"}
        }
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_admin_user(mock_user_data)
    
    assert exc_info.value.status_code == 403

