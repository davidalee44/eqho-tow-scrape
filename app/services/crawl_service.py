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
        # Use new orchestrator for comprehensive scraping
        from app.services.scraping_orchestrator import ScrapingOrchestrator
        self.orchestrator = ScrapingOrchestrator()
    
    async def crawl_zone(
        self,
        db: AsyncSession,
        zone_id: UUID,
        search_query: str = "towing company",
        scrape_websites: bool = True,
        scrape_profiles: bool = False,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Crawl a zone for companies using the comprehensive orchestrator
        
        Returns:
            {
                'companies_found': int,
                'companies_new': int,
                'companies_updated': int,
                'websites_scraped': int,
                'websites_failed': int,
                'profiles_scraped': int,
                'stage_breakdown': dict
            }
        """
        # Use orchestrator for comprehensive scraping
        return await self.orchestrator.crawl_and_enrich_zone(
            db,
            zone_id,
            search_query=search_query,
            scrape_websites=scrape_websites,
            scrape_profiles=scrape_profiles,
            max_results=max_results
        )
    
    async def scrape_websites_for_zone(
        self,
        db: AsyncSession,
        zone_id: UUID
    ) -> Dict[str, Any]:
        """Batch scrape websites for all companies in a zone"""
        companies = await ZoneService.get_companies_by_zone(db, zone_id)
        
        # Filter companies with websites
        companies_with_websites = [c for c in companies if c.website]
        
        if not companies_with_websites:
            return {
                'companies_processed': len(companies),
                'websites_scraped': 0,
                'websites_failed': 0
            }
        
        # Use orchestrator's batch scraping
        results = await self.orchestrator._scrape_websites_batch(db, companies_with_websites)
        
        return {
            'companies_processed': len(companies),
            'websites_scraped': results['success'],
            'websites_failed': results['failed']
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
        await self.orchestrator.close()

