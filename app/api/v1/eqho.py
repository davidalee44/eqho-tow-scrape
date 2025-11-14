"""Eqho.ai integration API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID
from app.database import get_db
from app.services.eqho_service import EqhoService
from app.services.company_service import CompanyService
from app.auth.dependencies import get_current_user
from app.config import settings

router = APIRouter()


@router.post("/upload-leads")
async def upload_leads_to_campaign(
    campaign_id: str,
    company_ids: List[UUID],
    list_id: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload companies as leads to an Eqho campaign
    
    Args:
        campaign_id: Eqho campaign ID
        company_ids: List of company UUIDs to upload
        list_id: Optional existing lead list ID
    """
    if not settings.eqho_api_token:
        raise HTTPException(status_code=400, detail="Eqho API token not configured")
    
    eqho_service = EqhoService()
    
    # Get companies
    companies = []
    for company_id in company_ids:
        company = await CompanyService.get_company(db, company_id)
        if not company:
            continue
        
        companies.append({
            'first_name': company.name.split()[0] if company.name else 'Business',
            'last_name': ' '.join(company.name.split()[1:]) if company.name and len(company.name.split()) > 1 else '',
            'phone': company.phone_primary,
            'email': company.email,
            'custom_fields': {
                'company_name': company.name,
                'address_city': company.address_city,
                'address_state': company.address_state,
                'zone_id': str(company.zone_id) if company.zone_id else None,
            }
        })
    
    if not companies:
        raise HTTPException(status_code=404, detail="No valid companies found")
    
    # Upload to Eqho
    result = await eqho_service.upload_leads_to_campaign(
        campaign_id=campaign_id,
        leads=companies,
        list_id=list_id
    )
    
    await eqho_service.close()
    return result


@router.post("/trigger-call")
async def trigger_call(
    campaign_id: str,
    company_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger an immediate call to a company via Eqho"""
    if not settings.eqho_api_token:
        raise HTTPException(status_code=400, detail="Eqho API token not configured")
    
    company = await CompanyService.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if not company.phone_primary:
        raise HTTPException(status_code=400, detail="Company has no phone number")
    
    eqho_service = EqhoService()
    
    # Prepare lead
    lead_data = {
        'first_name': company.name.split()[0] if company.name else 'Business',
        'last_name': ' '.join(company.name.split()[1:]) if company.name and len(company.name.split()) > 1 else '',
        'phone': company.phone_primary,
        'email': company.email,
        'custom_fields': {
            'company_name': company.name,
            'address_city': company.address_city,
            'address_state': company.address_state,
        }
    }
    
    # Upload and trigger call
    upload_result = await eqho_service.upload_leads_to_campaign(
        campaign_id=campaign_id,
        leads=[lead_data]
    )
    
    call_result = await eqho_service.trigger_call_now(
        campaign_id=campaign_id,
        lead_id=upload_result.get('list_id')
    )
    
    await eqho_service.close()
    return {
        'company_id': str(company_id),
        'call_result': call_result,
        'upload_result': upload_result
    }


@router.get("/campaign/{campaign_id}/calls")
async def get_campaign_calls(
    campaign_id: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get recent calls for an Eqho campaign"""
    if not settings.eqho_api_token:
        raise HTTPException(status_code=400, detail="Eqho API token not configured")
    
    eqho_service = EqhoService()
    calls = await eqho_service.get_campaign_calls(campaign_id, limit)
    await eqho_service.close()
    
    return {'calls': calls}

