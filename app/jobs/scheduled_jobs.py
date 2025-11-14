"""Scheduled background jobs"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.database import AsyncSessionLocal
from app.services.crawl_service import CrawlService
from app.services.enrichment_service import EnrichmentService
from app.services.outreach_service import OutreachService
from app.services.zone_service import ZoneService
from app.models.zone import Zone
from sqlalchemy import select
from datetime import datetime, timedelta


scheduler = AsyncIOScheduler()


async def daily_zone_crawl():
    """Crawl all active zones daily"""
    async with AsyncSessionLocal() as db:
        # Get all active zones
        result = await db.execute(select(Zone).where(Zone.is_active == True))
        zones = result.scalars().all()
        
        crawl_service = CrawlService()
        try:
            for zone in zones:
                try:
                    await crawl_service.crawl_zone(db, zone.id)
                    print(f"Crawled zone: {zone.name}")
                except Exception as e:
                    print(f"Error crawling zone {zone.id}: {e}")
        finally:
            await crawl_service.close()


async def weekly_enrichment_refresh():
    """Re-enrich companies older than 7 days"""
    async with AsyncSessionLocal() as db:
        from app.models.company import Company
        
        # Get companies that haven't been enriched in 7+ days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        result = await db.execute(
            select(Company).where(
                Company.website_scraped_at < cutoff_date
            ).limit(100)  # Process in batches
        )
        companies = result.scalars().all()
        
        enrichment_service = EnrichmentService()
        try:
            for company in companies:
                try:
                    await enrichment_service.enrich_company(db, company.id)
                    print(f"Refreshed enrichment for company: {company.name}")
                except Exception as e:
                    print(f"Error enriching company {company.id}: {e}")
        finally:
            await enrichment_service.close()


async def daily_website_scraping():
    """Scrape websites for companies that haven't been scraped or are stale"""
    async with AsyncSessionLocal() as db:
        from app.models.company import Company
        
        # Get companies that need website scraping
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(Company).where(
                (
                    (Company.website_scraped_at == None) |
                    (Company.website_scraped_at < cutoff_date)
                ) &
                (Company.website != None)
            ).limit(50)  # Process in batches
        )
        companies = result.scalars().all()
        
        enrichment_service = EnrichmentService()
        try:
            for company in companies:
                try:
                    await enrichment_service.enrich_company(db, company.id)
                    print(f"Scraped website for company: {company.name}")
                except Exception as e:
                    print(f"Error scraping website for company {company.id}: {e}")
        finally:
            await enrichment_service.close()


async def process_outreach_queue():
    """Process pending outreach every 15 minutes"""
    async with AsyncSessionLocal() as db:
        outreach_service = OutreachService()
        try:
            result = await outreach_service.process_outreach_queue(db)
            print(f"Processed outreach queue: {result}")
        except Exception as e:
            print(f"Error processing outreach queue: {e}")


def start_scheduler():
    """Start the scheduler with all jobs"""
    # Daily zone crawl at 2 AM
    scheduler.add_job(
        daily_zone_crawl,
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_zone_crawl'
    )
    
    # Weekly enrichment refresh on Sundays at 3 AM
    scheduler.add_job(
        weekly_enrichment_refresh,
        trigger=CronTrigger(day_of_week=6, hour=3, minute=0),
        id='weekly_enrichment_refresh'
    )
    
    # Daily website scraping at 4 AM
    scheduler.add_job(
        daily_website_scraping,
        trigger=CronTrigger(hour=4, minute=0),
        id='daily_website_scraping'
    )
    
    # Process outreach queue every 15 minutes
    scheduler.add_job(
        process_outreach_queue,
        trigger=IntervalTrigger(minutes=15),
        id='process_outreach_queue'
    )
    
    scheduler.start()
    print("Scheduler started")


def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    print("Scheduler stopped")

