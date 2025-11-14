"""Tests for user service"""
import pytest
from uuid import uuid4
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(db_session):
    """Test creating a new user"""
    auth_user_id = uuid4()
    user_data = UserCreate(
        auth_user_id=auth_user_id,
        email="test@example.com",
        full_name="Test User",
        role="user"
    )
    
    user = await UserService.create_user(db_session, user_data)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.auth_user_id == auth_user_id
    assert user.role == "user"


@pytest.mark.asyncio
async def test_get_user_by_id(db_session):
    """Test getting user by ID"""
    auth_user_id = uuid4()
    user_data = UserCreate(
        auth_user_id=auth_user_id,
        email="test@example.com",
        full_name="Test User"
    )
    
    created_user = await UserService.create_user(db_session, user_data)
    retrieved_user = await UserService.get_user_by_id(db_session, created_user.id)
    
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_auth_id(db_session):
    """Test getting user by Supabase auth user ID"""
    auth_user_id = uuid4()
    user_data = UserCreate(
        auth_user_id=auth_user_id,
        email="test@example.com",
        full_name="Test User"
    )
    
    created_user = await UserService.create_user(db_session, user_data)
    retrieved_user = await UserService.get_user_by_auth_id(db_session, auth_user_id)
    
    assert retrieved_user is not None
    assert retrieved_user.auth_user_id == auth_user_id


@pytest.mark.asyncio
async def test_update_user(db_session):
    """Test updating user"""
    auth_user_id = uuid4()
    user_data = UserCreate(
        auth_user_id=auth_user_id,
        email="test@example.com",
        full_name="Test User"
    )
    
    created_user = await UserService.create_user(db_session, user_data)
    
    update_data = UserUpdate(
        full_name="Updated Name",
        role="admin"
    )
    
    updated_user = await UserService.update_user(db_session, created_user.id, update_data)
    
    assert updated_user is not None
    assert updated_user.full_name == "Updated Name"
    assert updated_user.role == "admin"


@pytest.mark.asyncio
async def test_delete_user(db_session):
    """Test soft deleting user"""
    auth_user_id = uuid4()
    user_data = UserCreate(
        auth_user_id=auth_user_id,
        email="test@example.com",
        full_name="Test User"
    )
    
    created_user = await UserService.create_user(db_session, user_data)
    success = await UserService.delete_user(db_session, created_user.id)
    
    assert success is True
    
    deleted_user = await UserService.get_user_by_id(db_session, created_user.id)
    assert deleted_user.is_active is False

