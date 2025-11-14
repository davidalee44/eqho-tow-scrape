"""User service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user operations"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user profile"""
        user = User(**user_data.model_dump())
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_auth_id(db: AsyncSession, auth_user_id: UUID) -> Optional[User]:
        """Get user by Supabase auth user ID"""
        result = await db.execute(select(User).where(User.auth_user_id == auth_user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_users(
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """List users with pagination"""
        query = select(User)
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        # Get total count
        count_query = select(User)
        if is_active is not None:
            count_query = count_query.where(User.is_active == is_active)
        total_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        users = list(result.scalars().all())
        
        return users, total
    
    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: UUID,
        user_data: UserUpdate
    ) -> Optional[User]:
        """Update user"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
        """Deactivate user (soft delete)"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.is_active = False
        await db.commit()
        return True
    
    @staticmethod
    async def sync_user_from_auth(
        db: AsyncSession,
        auth_user_id: UUID,
        email: str,
        full_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> User:
        """
        Sync user profile from Supabase Auth
        
        Creates user profile if it doesn't exist, updates if it does
        """
        user = await UserService.get_user_by_auth_id(db, auth_user_id)
        
        if user:
            # Update existing user
            update_data = {
                "email": email,
                "full_name": full_name,
                "user_metadata": metadata
            }
            for field, value in update_data.items():
                if value is not None:
                    setattr(user, field, value)
            await db.commit()
            await db.refresh(user)
            return user
        else:
            # Create new user profile
            user_data = UserCreate(
                auth_user_id=auth_user_id,
                email=email,
                full_name=full_name,
                metadata=metadata,
                role="user"
            )
            return await UserService.create_user(db, user_data)

