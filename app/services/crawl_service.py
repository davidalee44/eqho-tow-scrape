"""Crawl service orchestrator"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from uuid import UUID
from app.services.apify_service import ApifyService
from app.services.company_service import CompanyService
from app.services.enrichment_service import EnrichmentService
from app.services.zone_service import ZoneService
from app.models.company import Company


class CrawlService:
    """Service for orchestrating crawls"""
    
    def __init__(self):
        self.apify_service = ApifyService()
        self.enrichment_service = EnrichmentService()
    
    async def crawl_zone(
        self,
        db: AsyncSession,
        zone_id: UUID,
        search_query: str = "towing company"
    ) -> Dict[str, Any]:
        """
        Crawl a zone for companies
        
        Returns:
            {
                'companies_found': int,
                'companies_new': int,
                'companies_updated': int,
                'websites_scraped': int
            }
        """
        # Get zone
        zone = await ZoneService.get_zone(db, zone_id)
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")
        
        # Build location string
        location = f"{zone.name}, {zone.state}" if zone.state else zone.name
        
        # Crawl with Apify
        companies_data = await self.apify_service.crawl_google_maps(
            location=location,
            search_query=search_query
        )
        
        # Process companies
        companies_new = 0
        companies_updated = 0
        
        for company_data in companies_data:
            # Check if company exists by google_business_url
            from sqlalchemy import select
            google_url = company_data.get('google_business_url', '')
            if google_url:
                result = await db.execute(
                    select(Company).where(Company.google_business_url == google_url)
                )
                existing = result.scalar_one_or_none()
            else:
                existing = None
            
            company = await CompanyService.create_or_update_company(
                db,
                company_data,
                zone_id
            )
            
            if existing:
                companies_updated += 1
            else:
                companies_new += 1
            
            # Enrich company (including website scraping)
            try:
                await self.enrichment_service.enrich_company(db, company.id)
            except Exception as e:
                print(f"Error enriching company {company.id}: {e}")
        
        # Count websites scraped
        websites_scraped = sum(
            1 for c in companies_data
            if c.get('website') and c.get('website_scrape_status') == 'success'
        )
        
        return {
            'companies_found': len(companies_data),
            'companies_new': companies_new,
            'companies_updated': companies_updated,
            'websites_scraped': websites_scraped
        }
    
    async def scrape_websites_for_zone(
        self,
        db: AsyncSession,
        zone_id: UUID
    ) -> Dict[str, Any]:
        """Batch scrape websites for all companies in a zone"""
        companies = await ZoneService.get_companies_by_zone(db, zone_id)
        
        scraped = 0
        failed = 0
        
        for company in companies:
            if company.website:
                try:
                    await self.enrichment_service.enrich_company(db, company.id)
                    scraped += 1
                except Exception as e:
                    print(f"Error scraping website for company {company.id}: {e}")
                    failed += 1
        
        return {
            'companies_processed': len(companies),
            'websites_scraped': scraped,
            'websites_failed': failed
        }
    
    async def scrape_company_website(
        self,
        db: AsyncSession,
        company_id: UUID
    ) -> Dict[str, Any]:
        """Scrape a single company website"""
        company = await CompanyService.get_company(db, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        if not company.website:
            return {
                'status': 'no_website',
                'message': 'Company has no website'
            }
        
        try:
            await self.enrichment_service.enrich_company(db, company_id)
            return {
                'status': 'success',
                'has_impound': company.has_impound_service,
                'impound_confidence': company.impound_confidence
            }
        except Exception as e:
            return {
                'status': 'failed',
                'message': str(e)
            }
    
    async def close(self):
        """Close resources"""
        await self.apify_service.close()
        await self.enrichment_service.close()

