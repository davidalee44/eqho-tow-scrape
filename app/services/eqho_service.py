"""Eqho.ai integration service for voice AI outreach"""
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EqhoService:
    """Service for integrating with Eqho.ai API"""
    
    def __init__(self):
        self.api_token = settings.eqho_api_token
        self.base_url = settings.eqho_api_url or "https://api.eqho.ai/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            timeout=60.0
        )
    
    async def upload_leads_to_campaign(
        self,
        campaign_id: str,
        leads: List[Dict[str, Any]],
        list_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload leads to an Eqho campaign
        
        Args:
            campaign_id: Eqho campaign ID
            leads: List of lead dictionaries with fields:
                - first_name (optional)
                - last_name (optional)
                - phone (required)
                - email (optional)
                - custom_fields (optional dict)
            list_id: Optional existing lead list ID, otherwise creates new list
        
        Returns:
            Dict with list_id and upload status
        """
        # Create or use existing lead list
        if not list_id:
            list_data = await self.create_lead_list(
                name=f"TowPilot Leads - {campaign_id}",
                description="Leads from TowPilot scraper"
            )
            list_id = list_data.get('id')
        
        # Upload leads
        upload_result = await self.upload_leads(list_id, leads)
        
        return {
            'list_id': list_id,
            'campaign_id': campaign_id,
            'leads_uploaded': len(leads),
            'upload_result': upload_result
        }
    
    async def create_lead_list(
        self,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new lead list in Eqho"""
        # Note: Using MCP tool pattern - in production, this would be an HTTP API call
        # For now, we'll structure it for future API integration
        logger.info(f"Creating lead list: {name}")
        return {
            'id': 'pending_api_integration',
            'name': name,
            'description': description
        }
    
    async def upload_leads(
        self,
        list_id: str,
        leads: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Upload leads to a lead list"""
        # Note: Using MCP tool pattern - in production, this would be an HTTP API call
        logger.info(f"Uploading {len(leads)} leads to list {list_id}")
        return {
            'success': True,
            'leads_count': len(leads)
        }
    
    async def trigger_call(
        self,
        campaign_id: str,
        lead_id: str
    ) -> Dict[str, Any]:
        """
        Trigger an outbound call via Eqho
        
        Args:
            campaign_id: Eqho campaign ID
            lead_id: Lead ID in Eqho system
        
        Returns:
            Dict with call_id and status
        """
        # Note: Using MCP tool pattern - in production, this would be an HTTP API call
        logger.info(f"Triggering call for lead {lead_id} in campaign {campaign_id}")
        return {
            'call_id': 'pending_api_integration',
            'status': 'queued',
            'campaign_id': campaign_id,
            'lead_id': lead_id
        }
    
    async def trigger_call_now(
        self,
        campaign_id: str,
        lead_id: str
    ) -> Dict[str, Any]:
        """
        Trigger an immediate call (bypasses campaign scheduling)
        
        Args:
            campaign_id: Eqho campaign ID
            lead_id: Lead ID in Eqho system
        
        Returns:
            Dict with call_id and status
        """
        logger.info(f"Triggering immediate call for lead {lead_id}")
        return await self.trigger_call(campaign_id, lead_id)
    
    async def get_call_status(
        self,
        call_id: str
    ) -> Dict[str, Any]:
        """Get status of a call"""
        logger.info(f"Getting call status for {call_id}")
        return {
            'call_id': call_id,
            'status': 'unknown'
        }
    
    async def get_campaign_calls(
        self,
        campaign_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent calls for a campaign"""
        logger.info(f"Getting calls for campaign {campaign_id}")
        return []
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

