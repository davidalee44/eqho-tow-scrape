"""Enrichment API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.schemas.enrichment import EnrichmentSnapshotResponse
from app.services.enrichment_service import EnrichmentService
from app.services.crawl_service import CrawlService
from app.models.enrichment import EnrichmentSnapshot
from sqlalchemy import select

router = APIRouter()


@router.post("/company/{company_id}")
async def enrich_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Trigger enrichment for a company"""
    enrichment_service = EnrichmentService()
    try:
        company = await enrichment_service.enrich_company(db, company_id)
        return {"status": "success", "company_id": str(company.id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await enrichment_service.close()


@router.post("/bulk")
async def bulk_enrichment(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Bulk enrichment for companies in a zone"""
    crawl_service = CrawlService()
    try:
        result = await crawl_service.scrape_websites_for_zone(db, zone_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await crawl_service.close()


@router.get("/snapshots/{company_id}", response_model=list[EnrichmentSnapshotResponse])
async def get_enrichment_snapshots(
    company_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get enrichment history for a company"""
    result = await db.execute(
        select(EnrichmentSnapshot).where(EnrichmentSnapshot.company_id == company_id)
    )
    snapshots = result.scalars().all()
    return snapshots


@router.post("/scrape-website/{company_id}")
async def scrape_website(
    company_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Trigger website scraping for a company"""
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


@router.post("/scrape-websites/zone/{zone_id}")
async def scrape_websites_for_zone(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Batch website scraping for all companies in a zone"""
    crawl_service = CrawlService()
    try:
        result = await crawl_service.scrape_websites_for_zone(db, zone_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await crawl_service.close()

