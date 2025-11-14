"""Outreach service with Eqho.ai integration"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from jinja2 import Template
from app.models.outreach import OutreachSequence, OutreachAssignment, OutreachHistory
from app.models.company import Company
from app.services.company_service import CompanyService
from app.services.eqho_service import EqhoService
from app.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)


class OutreachService:
    """Service for managing outreach campaigns with Eqho.ai integration"""
    
    def __init__(self):
        self.webhook_url = settings.outreach_webhook_url
        self.eqho_service = EqhoService() if settings.eqho_api_token else None
        self.default_campaign_id = settings.eqho_default_campaign_id
    
    async def create_sequence(
        self,
        db: AsyncSession,
        name: str,
        description: Optional[str],
        is_active: bool,
        steps: List[Dict[str, Any]]
    ) -> OutreachSequence:
        """Create an outreach sequence"""
        sequence = OutreachSequence(
            name=name,
            description=description,
            is_active=is_active,
            steps=steps
        )
        db.add(sequence)
        await db.commit()
        await db.refresh(sequence)
        return sequence
    
    async def assign_company_to_sequence(
        self,
        db: AsyncSession,
        company_id: UUID,
        sequence_id: UUID
    ) -> OutreachAssignment:
        """Assign a company to an outreach sequence"""
        assignment = OutreachAssignment(
            company_id=company_id,
            sequence_id=sequence_id,
            status='pending'
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment
    
    async def send_outreach(
        self,
        db: AsyncSession,
        company_id: UUID,
        channel: str,
        message_template: str,
        subject: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> OutreachHistory:
        """
        Send outreach message
        
        For 'phone' channel, uses Eqho.ai if configured, otherwise falls back to webhook
        """
        company = await CompanyService.get_company(db, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        # Generate message content
        message_content = self.generate_message_content(company, message_template, channel)
        
        # Create outreach history record
        outreach = OutreachHistory(
            company_id=company_id,
            channel=channel,
            status='pending',
            message_content=message_content
        )
        db.add(outreach)
        await db.commit()
        
        # Send via appropriate channel
        try:
            if channel == 'phone' and self.eqho_service:
                # Use Eqho.ai for voice AI calls
                result = await self._send_via_eqho(company, campaign_id or self.default_campaign_id)
            else:
                # Use webhook or legacy API
                result = await self._send_message(channel, company, message_content, subject)
            
            outreach.status = 'sent'
            outreach.sent_at = datetime.utcnow()
            outreach.external_id = result.get('id') or result.get('call_id')
            outreach.outreach_metadata = result
        except Exception as e:
            logger.error(f"Error sending outreach: {e}", exc_info=True)
            outreach.status = 'failed'
            outreach.outreach_metadata = {'error': str(e)}
        
        await db.commit()
        await db.refresh(outreach)
        return outreach
    
    async def _send_via_eqho(
        self,
        company: Company,
        campaign_id: str
    ) -> Dict[str, Any]:
        """Send outreach via Eqho.ai voice AI"""
        if not self.eqho_service:
            raise ValueError("Eqho service not configured")
        
        if not company.phone_primary:
            raise ValueError(f"Company {company.id} has no phone number")
        
        # Prepare lead data for Eqho
        lead_data = {
            'first_name': company.name.split()[0] if company.name else 'Business',
            'last_name': ' '.join(company.name.split()[1:]) if company.name and len(company.name.split()) > 1 else '',
            'phone': company.phone_primary,
            'email': company.email,
            'custom_fields': {
                'company_name': company.name,
                'address_city': company.address_city,
                'address_state': company.address_state,
                'zone_id': str(company.zone_id) if company.zone_id else None,
                'source': company.source
            }
        }
        
        # Upload lead and trigger call
        upload_result = await self.eqho_service.upload_leads_to_campaign(
            campaign_id=campaign_id,
            leads=[lead_data]
        )
        
        # Trigger immediate call
        call_result = await self.eqho_service.trigger_call_now(
            campaign_id=campaign_id,
            lead_id=upload_result.get('list_id')  # In production, would use actual lead_id
        )
        
        return {
            **call_result,
            'eqho_list_id': upload_result.get('list_id'),
            'method': 'eqho_ai'
        }
    
    def generate_message_content(
        self,
        company: Company,
        template: str,
        channel: str
    ) -> str:
        """Generate message content from template"""
        jinja_template = Template(template)
        return jinja_template.render(
            company=company,
            channel=channel
        )
    
    async def _send_message(
        self,
        channel: str,
        company: Company,
        message: str,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send message via webhook or API"""
        if self.webhook_url:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json={
                        'channel': channel,
                        'to': self._get_contact_info(company, channel),
                        'message': message,
                        'subject': subject,
                        'company_id': str(company.id)
                    }
                )
                response.raise_for_status()
                return response.json()
        else:
            # Stub implementation - just return success
            return {'id': 'stub', 'status': 'sent'}
    
    def _get_contact_info(self, company: Company, channel: str) -> str:
        """Get contact information based on channel"""
        if channel == 'email':
            return company.email or ''
        elif channel in ['sms', 'phone']:
            return company.phone_primary
        return ''
    
    async def process_outreach_queue(self, db: AsyncSession) -> Dict[str, int]:
        """Process pending outreach assignments"""
        from sqlalchemy import select, and_
        
        # Get active assignments that need processing
        result = await db.execute(
            select(OutreachAssignment).where(
                and_(
                    OutreachAssignment.status == 'active',
                    OutreachSequence.is_active == True
                )
            ).join(OutreachSequence)
        )
        assignments = result.scalars().all()
        
        processed = 0
        sent = 0
        failed = 0
        
        for assignment in assignments:
            try:
                # Get sequence and company
                sequence = assignment.sequence
                company = await CompanyService.get_company(db, assignment.company_id)
                
                if not company or not sequence:
                    continue
                
                # Get current step
                if assignment.current_step >= len(sequence.steps):
                    assignment.status = 'completed'
                    assignment.completed_at = datetime.utcnow()
                    await db.commit()
                    continue
                
                step = sequence.steps[assignment.current_step]
                
                # Check if it's time to send this step
                if assignment.started_at:
                    delay = timedelta(hours=step.get('delay_hours', 0))
                    if datetime.utcnow() < assignment.started_at + delay:
                        continue
                else:
                    assignment.started_at = datetime.utcnow()
                
                # Send outreach
                await self.send_outreach(
                    db,
                    assignment.company_id,
                    step['channel'],
                    step['template'],
                    step.get('subject')
                )
                
                # Move to next step
                assignment.current_step += 1
                if assignment.current_step >= len(sequence.steps):
                    assignment.status = 'completed'
                    assignment.completed_at = datetime.utcnow()
                
                await db.commit()
                sent += 1
                processed += 1
            except Exception as e:
                print(f"Error processing outreach assignment {assignment.id}: {e}")
                failed += 1
                processed += 1
        
        return {
            'processed': processed,
            'sent': sent,
            'failed': failed
        }

