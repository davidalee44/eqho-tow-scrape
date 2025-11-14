"""User management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate, UserListResponse
from app.services.user_service import UserService
from app.auth.dependencies import get_current_admin_user, get_current_user

router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    limit: int = Query(100, le=1000, ge=1),
    offset: int = Query(0, ge=0),
    is_active: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> UserListResponse:
    """
    List users (admin only)
    
    Returns paginated list of users
    """
    users, total = await UserService.list_users(
        db,
        limit=limit,
        offset=offset,
        is_active=is_active
    )
    
    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Get user details (admin only)
    
    Returns user information by ID
    """
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.get("/me/profile", response_model=UserResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Get current user's profile
    
    Returns the authenticated user's profile
    """
    auth_user = current_user.get("user", {})
    auth_user_id = UUID(auth_user.get("id"))
    
    user = await UserService.get_user_by_auth_id(db, auth_user_id)
    if not user:
        # Sync user from auth if profile doesn't exist
        user = await UserService.sync_user_from_auth(
            db,
            auth_user_id=auth_user_id,
            email=auth_user.get("email"),
            full_name=auth_user.get("user_metadata", {}).get("full_name"),
            metadata=auth_user.get("user_metadata")
        )
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update user (admin only)
    
    Updates user information
    """
    user = await UserService.update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/me/profile", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update current user's profile
    
    Users can update their own profile (limited fields)
    """
    auth_user = current_user.get("user", {})
    auth_user_id = UUID(auth_user.get("id"))
    
    user = await UserService.get_user_by_auth_id(db, auth_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Users can only update their own name, not role or active status
    update_data = user_data.model_dump(exclude_unset=True)
    if "role" in update_data:
        del update_data["role"]
    if "is_active" in update_data:
        del update_data["is_active"]
    
    limited_update = UserUpdate(**update_data)
    user = await UserService.update_user(db, user.id, limited_update)
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate user (admin only)
    
    Soft deletes a user by setting is_active to False
    """
    success = await UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

