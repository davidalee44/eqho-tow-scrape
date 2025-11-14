"""Enrichment service"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from app.models.company import Company
from app.models.enrichment import EnrichmentSnapshot
from app.services.company_service import CompanyService
from app.services.website_scraper_service import WebsiteScraperService


class EnrichmentService:
    """Service for enriching company data"""
    
    def __init__(self):
        self.website_scraper = WebsiteScraperService()
    
    async def enrich_company(self, db: AsyncSession, company_id: UUID) -> Company:
        """Main enrichment orchestrator"""
        company = await CompanyService.get_company(db, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        enrichment_data = {}
        
        # Enrich from website
        if company.website:
            website_data = await self.website_scraper.scrape_website(company.website)
            if website_data['status'] == 'success':
                enrichment_data['hours_website'] = website_data['hours']
                enrichment_data['has_impound_service'] = website_data['has_impound']
                enrichment_data['impound_confidence'] = website_data['impound_confidence']
                enrichment_data['website_scraped_at'] = datetime.utcnow()
                enrichment_data['website_scrape_status'] = 'success'
            else:
                enrichment_data['website_scrape_status'] = website_data['status']
        
        # Detect fleet size (heuristic)
        fleet_size = self.detect_fleet_size(company)
        if fleet_size:
            enrichment_data['fleet_size'] = fleet_size
        
        # Detect dispatch line
        has_dispatch = self.detect_dispatch_line(company)
        if has_dispatch:
            enrichment_data['phone_dispatch'] = company.phone_dispatch
        
        # Update company
        for key, value in enrichment_data.items():
            setattr(company, key, value)
        
        await db.commit()
        await db.refresh(company)
        
        # Store snapshot
        await self._store_snapshot(db, company_id, enrichment_data, 'website')
        
        return company
    
    def detect_fleet_size(self, company: Company) -> Optional[str]:
        """Detect fleet size based on heuristics"""
        # Simple heuristic based on review count and rating
        if company.review_count:
            if company.review_count > 500:
                return 'large'
            elif company.review_count > 100:
                return 'medium'
            else:
                return 'small'
        return None
    
    def detect_dispatch_line(self, company: Company) -> bool:
        """Detect if company has separate dispatch line"""
        # Check if phone_dispatch is already set
        return bool(company.phone_dispatch)
    
    async def _store_snapshot(
        self,
        db: AsyncSession,
        company_id: UUID,
        snapshot_data: Dict[str, Any],
        source: str
    ):
        """Store enrichment snapshot"""
        snapshot = EnrichmentSnapshot(
            company_id=company_id,
            snapshot_data=snapshot_data,
            enrichment_source=source
        )
        db.add(snapshot)
        await db.commit()
    
    async def enrich_from_facebook(self, db: AsyncSession, company: Company) -> Dict[str, Any]:
        """Enrich from Facebook (placeholder for future implementation)"""
        # TODO: Implement Facebook scraping
        return {}
    
    async def enrich_from_google(self, db: AsyncSession, company: Company) -> Dict[str, Any]:
        """Enrich from Google Business (placeholder for future implementation)"""
        # TODO: Implement Google Business scraping
        return {}
    
    async def close(self):
        """Close resources"""
        await self.website_scraper.close()

