"""Company service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyService:
    """Service for company operations"""
    
    @staticmethod
    async def create_or_update_company(
        db: AsyncSession, 
        company_data: Dict[str, Any], 
        zone_id: UUID
    ) -> Company:
        """Create or update company based on Google Business URL"""
        # Try to find existing company by google_business_url
        google_url = company_data.get("google_business_url")
        if google_url:
            result = await db.execute(
                select(Company).where(Company.google_business_url == google_url)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing company
                for key, value in company_data.items():
                    if value is not None:
                        setattr(existing, key, value)
                existing.zone_id = zone_id
                await db.commit()
                await db.refresh(existing)
                return existing
        
        # Create new company
        company_data["zone_id"] = zone_id
        company = Company(**company_data)
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company
    
    @staticmethod
    async def get_company(db: AsyncSession, company_id: UUID) -> Optional[Company]:
        """Get company by ID"""
        result = await db.execute(select(Company).where(Company.id == company_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search_companies(
        db: AsyncSession,
        zone_id: Optional[UUID] = None,
        services: Optional[List[str]] = None,
        fleet_size: Optional[str] = None,
        has_impound_service: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Company]:
        """Search companies with filters"""
        query = select(Company)
        
        conditions = []
        if zone_id:
            conditions.append(Company.zone_id == zone_id)
        if fleet_size:
            conditions.append(Company.fleet_size == fleet_size)
        if has_impound_service is not None:
            conditions.append(Company.has_impound_service == has_impound_service)
        if services:
            # Filter by services array containing any of the specified services
            for service in services:
                conditions.append(Company.services.contains([service]))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_company(
        db: AsyncSession, 
        company_id: UUID, 
        company_data: CompanyUpdate
    ) -> Optional[Company]:
        """Update company"""
        company = await CompanyService.get_company(db, company_id)
        if not company:
            return None
        
        update_data = company_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)
        
        await db.commit()
        await db.refresh(company)
        return company
    
    @staticmethod
    async def bulk_import_companies(
        db: AsyncSession,
        companies_data: List[Dict[str, Any]],
        zone_id: UUID
    ) -> List[Company]:
        """Bulk import companies"""
        companies = []
        for company_data in companies_data:
            company = await CompanyService.create_or_update_company(
                db, company_data, zone_id
            )
            companies.append(company)
        return companies

