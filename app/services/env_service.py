"""Environment configuration service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict
from uuid import UUID
from app.models.environment_config import EnvironmentConfig
from app.config import settings


class EnvService:
    """Service for environment variable management"""
    
    @staticmethod
    async def get_env_var(
        db: AsyncSession,
        key: str,
        environment: Optional[str] = None
    ) -> Optional[str]:
        """Get environment variable value"""
        env = environment or settings.environment
        
        result = await db.execute(
            select(EnvironmentConfig)
            .where(
                EnvironmentConfig.key == key,
                EnvironmentConfig.environment == env
            )
        )
        config = result.scalar_one_or_none()
        
        if config:
            # In production, decrypt if encrypted
            return config.value
        return None
    
    @staticmethod
    async def set_env_var(
        db: AsyncSession,
        key: str,
        value: str,
        is_encrypted: bool = False,
        description: Optional[str] = None,
        environment: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> EnvironmentConfig:
        """Set environment variable"""
        env = environment or settings.environment
        
        # Check if exists
        result = await db.execute(
            select(EnvironmentConfig)
            .where(
                EnvironmentConfig.key == key,
                EnvironmentConfig.environment == env
            )
        )
        config = result.scalar_one_or_none()
        
        if config:
            # Update existing
            config.value = value
            config.is_encrypted = is_encrypted
            if description:
                config.description = description
            if created_by:
                config.created_by = created_by
        else:
            # Create new
            config = EnvironmentConfig(
                key=key,
                value=value,
                is_encrypted=is_encrypted,
                description=description,
                environment=env,
                created_by=created_by
            )
            db.add(config)
        
        await db.commit()
        await db.refresh(config)
        return config
    
    @staticmethod
    async def delete_env_var(
        db: AsyncSession,
        key: str,
        environment: Optional[str] = None
    ) -> bool:
        """Delete environment variable"""
        env = environment or settings.environment
        
        result = await db.execute(
            select(EnvironmentConfig)
            .where(
                EnvironmentConfig.key == key,
                EnvironmentConfig.environment == env
            )
        )
        config = result.scalar_one_or_none()
        
        if config:
            await db.delete(config)
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def list_env_vars(
        db: AsyncSession,
        environment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[EnvironmentConfig], int]:
        """List environment variables"""
        env = environment or settings.environment
        
        query = select(EnvironmentConfig).where(
            EnvironmentConfig.environment == env
        )
        
        # Get total count
        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count()).select_from(
                select(EnvironmentConfig).where(
                    EnvironmentConfig.environment == env
                ).subquery()
            )
        )
        total = count_result.scalar() or 0
        
        # Get paginated results
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        configs = list(result.scalars().all())
        
        return configs, total
    
    @staticmethod
    async def load_all_env_vars(
        db: AsyncSession,
        environment: Optional[str] = None
    ) -> Dict[str, str]:
        """Load all environment variables as dictionary"""
        env = environment or settings.environment
        
        result = await db.execute(
            select(EnvironmentConfig).where(
                EnvironmentConfig.environment == env
            )
        )
        configs = result.scalars().all()
        
        return {config.key: config.value for config in configs}

