"""Unified scraping orchestrator for comprehensive company data collection"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from app.services.apify_service import ApifyService
from app.services.company_service import CompanyService
from app.services.enrichment_service import EnrichmentService
from app.services.website_scraper_service import WebsiteScraperService
from app.services.zone_service import ZoneService
from app.models.company import Company
from app.config import settings
from sqlalchemy import select, and_


class ScrapingStage(str, Enum):
    """Stages of the scraping pipeline"""
    INITIAL = "initial"  # Just discovered, no scraping done
    GOOGLE_MAPS = "google_maps"  # Google Maps data collected
    WEBSITE_SCRAPED = "website_scraped"  # Website scraped
    FACEBOOK_SCRAPED = "facebook_scraped"  # Facebook profile scraped
    FULLY_ENRICHED = "fully_enriched"  # All sources scraped
    FAILED = "failed"  # Scraping failed


class ScrapingOrchestrator:
    """
    Unified orchestrator for comprehensive company data collection
    
    Flow:
    1. Zone Crawl (Google Maps via Apify) → Discover companies
    2. Website Scraping → Extract hours, services, impound info
    3. Profile Enrichment → Facebook, Google Business profiles
    4. Data Validation → Ensure completeness
    5. Status Tracking → Track progress through pipeline
    """
    
    def __init__(self):
        self.apify_service = ApifyService()
        self.enrichment_service = EnrichmentService()
        self.website_scraper = WebsiteScraperService()
        self.max_concurrent = settings.website_scrape_concurrent
    
    async def crawl_and_enrich_zone(
        self,
        db: AsyncSession,
        zone_id: UUID,
        search_query: str = "towing company",
        scrape_websites: bool = True,
        scrape_profiles: bool = False,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Complete zone crawl and enrichment pipeline
        
        Args:
            zone_id: Zone to crawl
            search_query: Search query for Google Maps
            scrape_websites: Whether to scrape company websites
            scrape_profiles: Whether to scrape Facebook/Google profiles
            max_results: Maximum companies to discover
            
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
        # Stage 1: Discover companies via Google Maps
        zone = await ZoneService.get_zone(db, zone_id)
        if not zone:
            raise ValueError(f"Zone {zone_id} not found")
        
        location = f"{zone.name}, {zone.state}" if zone.state else zone.name
        
        companies_data = await self.apify_service.crawl_google_maps(
            location=location,
            search_query=search_query,
            max_results=max_results
        )
        
        stats = {
            'companies_found': len(companies_data),
            'companies_new': 0,
            'companies_updated': 0,
            'websites_scraped': 0,
            'websites_failed': 0,
            'profiles_scraped': 0,
            'stage_breakdown': {
                ScrapingStage.INITIAL: 0,
                ScrapingStage.GOOGLE_MAPS: 0,
                ScrapingStage.WEBSITE_SCRAPED: 0,
                ScrapingStage.FULLY_ENRICHED: 0,
            }
        }
        
        # Stage 2: Process and store companies
        companies_to_scrape = []
        
        for company_data in companies_data:
            # Check if company exists
            google_url = company_data.get('google_business_url', '')
            existing = None
            
            if google_url:
                result = await db.execute(
                    select(Company).where(Company.google_business_url == google_url)
                )
                existing = result.scalar_one_or_none()
            
            # Create or update company
            company = await CompanyService.create_or_update_company(
                db,
                company_data,
                zone_id
            )
            
            # Update scraping stage
            if existing:
                stats['companies_updated'] += 1
                # Update to GOOGLE_MAPS if was INITIAL or None
                if not company.scraping_stage or company.scraping_stage == ScrapingStage.INITIAL.value:
                    company.scraping_stage = ScrapingStage.GOOGLE_MAPS.value
                    stats['stage_breakdown'][ScrapingStage.GOOGLE_MAPS] += 1
                else:
                    # Count existing stage
                    try:
                        existing_stage = ScrapingStage(company.scraping_stage)
                        stats['stage_breakdown'][existing_stage] = stats['stage_breakdown'].get(existing_stage, 0) + 1
                    except ValueError:
                        # Invalid stage, reset to GOOGLE_MAPS
                        company.scraping_stage = ScrapingStage.GOOGLE_MAPS.value
                        stats['stage_breakdown'][ScrapingStage.GOOGLE_MAPS] += 1
            else:
                stats['companies_new'] += 1
                company.scraping_stage = ScrapingStage.INITIAL.value
                stats['stage_breakdown'][ScrapingStage.INITIAL] += 1
            
            await db.commit()
            await db.refresh(company)
            
            # Queue for website scraping if enabled
            if scrape_websites and company.website:
                companies_to_scrape.append(company)
        
        # Stage 3: Scrape websites (with concurrency control)
        if scrape_websites and companies_to_scrape:
            website_results = await self._scrape_websites_batch(
                db,
                companies_to_scrape
            )
            stats['websites_scraped'] = website_results['success']
            stats['websites_failed'] = website_results['failed']
            stats['stage_breakdown'][ScrapingStage.WEBSITE_SCRAPED] = website_results['success']
        
        # Stage 4: Scrape profiles (Facebook, Google Business)
        if scrape_profiles:
            profile_results = await self._scrape_profiles_batch(
                db,
                companies_to_scrape
            )
            stats['profiles_scraped'] = profile_results['success']
            stats['stage_breakdown'][ScrapingStage.FULLY_ENRICHED] = profile_results['success']
        
        return stats
    
    async def _scrape_websites_batch(
        self,
        db: AsyncSession,
        companies: List[Company]
    ) -> Dict[str, int]:
        """Scrape websites for multiple companies with concurrency control"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = {'success': 0, 'failed': 0}
        
        async def scrape_with_limit(company: Company):
            async with semaphore:
                try:
                    await self.enrichment_service.enrich_company(db, company.id)
                    
                    # Update scraping stage
                    company.scraping_stage = ScrapingStage.WEBSITE_SCRAPED.value
                    company.website_scraped_at = datetime.utcnow()
                    company.website_scrape_status = 'success'
                    await db.commit()
                    
                    results['success'] += 1
                except Exception as e:
                    company.website_scrape_status = 'failed'
                    company.scraping_stage = ScrapingStage.FAILED.value
                    await db.commit()
                    results['failed'] += 1
                    print(f"Error scraping website for company {company.id}: {e}")
        
        # Process in batches
        tasks = [scrape_with_limit(company) for company in companies]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    async def _scrape_profiles_batch(
        self,
        db: AsyncSession,
        companies: List[Company]
    ) -> Dict[str, int]:
        """Scrape social media profiles for multiple companies"""
        results = {'success': 0, 'failed': 0}
        
        for company in companies:
            try:
                # Scrape Facebook if available
                if company.facebook_page:
                    facebook_data = await self.enrichment_service.enrich_from_facebook(
                        db,
                        company
                    )
                    if facebook_data:
                        results['success'] += 1
                
                # Scrape Google Business if available
                if company.google_business_url:
                    google_data = await self.enrichment_service.enrich_from_google(
                        db,
                        company
                    )
                    if google_data:
                        results['success'] += 1
                
                # Update stage if all sources scraped
                if company.website_scrape_status == 'success':
                    company.scraping_stage = ScrapingStage.FULLY_ENRICHED.value
                    await db.commit()
                    
            except Exception as e:
                results['failed'] += 1
                print(f"Error scraping profiles for company {company.id}: {e}")
        
        return results
    
    async def refresh_stale_companies(
        self,
        db: AsyncSession,
        zone_id: Optional[UUID] = None,
        days_stale: int = 30,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Refresh companies that haven't been scraped recently
        
        Args:
            zone_id: Optional zone filter
            days_stale: Number of days since last scrape to consider stale
            limit: Maximum companies to process
            
        Returns:
            Statistics about refresh operation
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_stale)
        
        query = select(Company).where(
            and_(
                (Company.website_scraped_at == None) |
                (Company.website_scraped_at < cutoff_date),
                Company.website != None,
                Company.website_scrape_status != 'no_website'
            )
        )
        
        if zone_id:
            query = query.where(Company.zone_id == zone_id)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        stale_companies = result.scalars().all()
        
        if not stale_companies:
            return {
                'companies_processed': 0,
                'websites_scraped': 0,
                'websites_failed': 0
            }
        
        website_results = await self._scrape_websites_batch(db, stale_companies)
        
        return {
            'companies_processed': len(stale_companies),
            'websites_scraped': website_results['success'],
            'websites_failed': website_results['failed']
        }
    
    async def get_scraping_status(
        self,
        db: AsyncSession,
        zone_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get scraping status breakdown for a zone or all zones"""
        query = select(Company)
        
        if zone_id:
            query = query.where(Company.zone_id == zone_id)
        
        result = await db.execute(query)
        companies = result.scalars().all()
        
        status_breakdown = {}
        for stage in ScrapingStage:
            status_breakdown[stage.value] = sum(
                1 for c in companies
                if (c.scraping_stage == stage.value) or
                   (c.scraping_stage is None and stage == ScrapingStage.INITIAL)
            )
        
        return {
            'total_companies': len(companies),
            'status_breakdown': status_breakdown,
            'with_websites': sum(1 for c in companies if c.website),
            'websites_scraped': sum(
                1 for c in companies
                if c.website_scrape_status == 'success'
            ),
            'websites_failed': sum(
                1 for c in companies
                if c.website_scrape_status == 'failed'
            ),
        }
    
    async def close(self):
        """Close all resources"""
        await self.apify_service.close()
        await self.enrichment_service.close()
        await self.website_scraper.close()

