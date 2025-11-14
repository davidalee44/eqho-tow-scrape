"""Crawl API endpoints"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.services.crawl_service import CrawlService
from app.services.scraping_orchestrator import ScrapingOrchestrator

router = APIRouter()


@router.post("/zone/{zone_id}")
async def crawl_zone(
    zone_id: UUID,
    search_query: str = Query(
        "towing company", description="Search query for Google Maps"
    ),
    scrape_websites: bool = Query(
        True, description="Whether to scrape company websites"
    ),
    scrape_profiles: bool = Query(
        False, description="Whether to scrape social profiles"
    ),
    max_results: int = Query(
        100, ge=1, le=500, description="Maximum companies to discover"
    ),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger comprehensive crawl for a zone

    This endpoint:
    1. Discovers companies via Google Maps (Apify)
    2. Creates/updates company records
    3. Optionally scrapes company websites
    4. Optionally scrapes social profiles (Facebook, Google Business)
    5. Returns detailed statistics
    """
    crawl_service = CrawlService()
    try:
        result = await crawl_service.crawl_zone(
            db,
            zone_id,
            search_query=search_query,
            scrape_websites=scrape_websites,
            scrape_profiles=scrape_profiles,
            max_results=max_results,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await crawl_service.close()


@router.post("/company/{company_id}")
async def crawl_company(
    company_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-crawl a specific company website"""
    crawl_service = CrawlService()
    try:
        result = await crawl_service.scrape_company_website(db, company_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await crawl_service.close()


@router.get("/status/{zone_id}")
async def get_scraping_status(
    zone_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scraping status breakdown for a zone"""
    orchestrator = ScrapingOrchestrator()
    try:
        status = await orchestrator.get_scraping_status(db, zone_id=zone_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await orchestrator.close()


@router.post("/refresh-stale")
async def refresh_stale_companies(
    zone_id: UUID = Query(None, description="Optional zone filter"),
    days_stale: int = Query(30, ge=1, le=365, description="Days since last scrape"),
    limit: int = Query(50, ge=1, le=500, description="Maximum companies to process"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Refresh companies that haven't been scraped recently"""
    orchestrator = ScrapingOrchestrator()
    try:
        result = await orchestrator.refresh_stale_companies(
            db, zone_id=zone_id, days_stale=days_stale, limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await orchestrator.close()
