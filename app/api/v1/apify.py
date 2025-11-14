"""Apify API endpoints for managing and downloading previous runs"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.services.apify_service import ApifyService

router = APIRouter()


@router.get("/runs")
async def list_apify_runs(
    actor_id: str = Query("apify/google-maps-scraper", description="Apify actor ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCEEDED, FAILED, RUNNING)"),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List previous Apify actor runs
    
    Returns list of runs with metadata including status, timestamps, and input parameters
    """
    apify_service = ApifyService()
    try:
        runs_data = await apify_service.list_runs(
            actor_id=actor_id,
            limit=limit,
            offset=offset,
            status=status
        )
        return runs_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")
    finally:
        await apify_service.close()


@router.get("/runs/towing")
async def list_towing_runs(
    limit: int = Query(100, ge=1, le=1000, description="Maximum runs to return"),
    status: Optional[str] = Query("SUCCEEDED", description="Filter by status"),
    current_user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    List all previous towing company runs
    
    Filters runs to only include those with "towing" in the search query
    """
    apify_service = ApifyService()
    try:
        runs = await apify_service.list_all_towing_runs(limit=limit, status=status)
        return runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list towing runs: {str(e)}")
    finally:
        await apify_service.close()


@router.get("/runs/{run_id}")
async def get_run_details(
    run_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get details of a specific Apify run
    
    Returns run status, timestamps, input parameters, and statistics
    """
    apify_service = ApifyService()
    try:
        run_details = await apify_service.get_run_details(run_id)
        return run_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get run details: {str(e)}")
    finally:
        await apify_service.close()


@router.get("/runs/{run_id}/data")
async def download_run_data(
    run_id: str,
    limit: Optional[int] = Query(None, ge=1, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Download data from a completed Apify run
    
    Returns company data mapped to our schema
    """
    apify_service = ApifyService()
    try:
        companies = await apify_service.download_run_data(
            run_id=run_id,
            limit=limit,
            offset=offset
        )
        return {
            "run_id": run_id,
            "companies_count": len(companies),
            "companies": companies,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download run data: {str(e)}")
    finally:
        await apify_service.close()


@router.post("/runs/download-all")
async def download_all_towing_data(
    limit_runs: int = Query(10, ge=1, le=100, description="Maximum runs to process"),
    limit_items_per_run: Optional[int] = Query(None, ge=1, description="Maximum items per run"),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Download data from all previous towing runs
    
    Processes multiple runs and returns aggregated company data
    """
    apify_service = ApifyService()
    try:
        result = await apify_service.download_all_towing_data(
            limit_runs=limit_runs,
            limit_items_per_run=limit_items_per_run
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download all data: {str(e)}")
    finally:
        await apify_service.close()

