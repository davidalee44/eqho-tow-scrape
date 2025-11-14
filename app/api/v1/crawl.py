"""Crawl API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.services.crawl_service import CrawlService

router = APIRouter()


@router.post("/zone/{zone_id}")
async def crawl_zone(
    zone_id: UUID,
    search_query: str = "towing company",
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Trigger crawl for a zone"""
    crawl_service = CrawlService()
    try:
        result = await crawl_service.crawl_zone(db, zone_id, search_query)
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
    db: AsyncSession = Depends(get_db)
):
    """Re-crawl a specific company"""
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

