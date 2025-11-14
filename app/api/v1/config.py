"""Environment configuration API endpoints (admin only)"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_admin_user
from app.database import get_db
from app.services.env_service import EnvService

router = APIRouter()


class EnvVarCreate(BaseModel):
    """Environment variable creation schema"""

    key: str
    value: str
    is_encrypted: bool = False
    description: Optional[str] = None
    environment: Optional[str] = None


class EnvVarResponse(BaseModel):
    """Environment variable response schema"""

    id: UUID
    key: str
    value: str  # In production, might want to mask sensitive values
    is_encrypted: bool
    description: Optional[str]
    environment: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EnvVarListResponse(BaseModel):
    """Environment variable list response"""

    configs: List[EnvVarResponse]
    total: int
    limit: int
    offset: int


@router.get("/env", response_model=EnvVarListResponse)
async def list_env_vars(
    limit: int = Query(100, le=1000, ge=1),
    offset: int = Query(0, ge=0),
    environment: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> EnvVarListResponse:
    """
    List environment variables (admin only)

    Returns paginated list of environment variables
    """
    configs, total = await EnvService.list_env_vars(
        db, environment=environment, limit=limit, offset=offset
    )

    return EnvVarListResponse(
        configs=[EnvVarResponse.model_validate(config) for config in configs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/env", response_model=EnvVarResponse, status_code=201)
async def set_env_var(
    env_data: EnvVarCreate,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> EnvVarResponse:
    """
    Set environment variable (admin only)

    Creates or updates an environment variable
    """
    auth_user = current_user.get("user", {})
    created_by = UUID(auth_user.get("id"))

    config = await EnvService.set_env_var(
        db,
        key=env_data.key,
        value=env_data.value,
        is_encrypted=env_data.is_encrypted,
        description=env_data.description,
        environment=env_data.environment,
        created_by=created_by,
    )

    return EnvVarResponse.model_validate(config)


@router.delete("/env/{key}", status_code=204)
async def delete_env_var(
    key: str,
    environment: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete environment variable (admin only)

    Removes an environment variable
    """
    success = await EnvService.delete_env_var(db, key, environment)
    if not success:
        raise HTTPException(status_code=404, detail="Environment variable not found")
