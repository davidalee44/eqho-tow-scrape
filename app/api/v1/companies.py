"""Company API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.services.company_service import CompanyService

router = APIRouter()


@router.get("", response_model=List[CompanyResponse])
async def list_companies(
    zone_id: Optional[UUID] = Query(None),
    services: Optional[str] = Query(None),  # Comma-separated list
    fleet_size: Optional[str] = Query(None),
    has_impound_service: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List/search companies"""
    services_list = services.split(",") if services else None
    return await CompanyService.search_companies(
        db,
        zone_id=zone_id,
        services=services_list,
        fleet_size=fleet_size,
        has_impound_service=has_impound_service,
        limit=limit,
        offset=offset
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get company details"""
    company = await CompanyService.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update company"""
    company = await CompanyService.update_company(db, company_id, company_data)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/bulk-import", response_model=List[CompanyResponse], status_code=201)
async def bulk_import_companies(
    companies_data: List[dict],
    zone_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Bulk import companies"""
    return await CompanyService.bulk_import_companies(db, companies_data, zone_id)

