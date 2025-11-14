"""Dashboard service for statistics"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any
from datetime import datetime
from app.models.company import Company
from app.models.zone import Zone
from app.models.enrichment import EnrichmentSnapshot
from app.models.outreach import OutreachHistory, OutreachAssignment
from app.utils.time_periods import get_time_period_range


class DashboardService:
    """Service for dashboard statistics"""
    
    @staticmethod
    async def get_dashboard_stats(
        db: AsyncSession,
        time_period: str = "today"
    ) -> Dict[str, Any]:
        """Get overall dashboard statistics"""
        start_date, end_date = get_time_period_range(time_period)
        
        # Companies stats
        companies_result = await db.execute(
            select(func.count(Company.id)).where(
                and_(
                    Company.created_at >= start_date,
                    Company.created_at <= end_date
                )
            )
        )
        companies_new = companies_result.scalar_one() or 0
        
        # Total companies
        total_companies_result = await db.execute(select(func.count(Company.id)))
        total_companies = total_companies_result.scalar_one() or 0
        
        # Enrichment stats
        enrichment_result = await db.execute(
            select(func.count(EnrichmentSnapshot.id)).where(
                and_(
                    EnrichmentSnapshot.created_at >= start_date,
                    EnrichmentSnapshot.created_at <= end_date
                )
            )
        )
        enrichments_created = enrichment_result.scalar_one() or 0
        
        # Website scraping stats
        website_scraped_result = await db.execute(
            select(func.count(Company.id)).where(
                and_(
                    Company.website_scraped_at >= start_date,
                    Company.website_scraped_at <= end_date,
                    Company.website_scrape_status == 'success'
                )
            )
        )
        websites_scraped = website_scraped_result.scalar_one() or 0
        
        # Outreach stats
        outreach_sent_result = await db.execute(
            select(func.count(OutreachHistory.id)).where(
                and_(
                    OutreachHistory.created_at >= start_date,
                    OutreachHistory.created_at <= end_date,
                    OutreachHistory.status == 'sent'
                )
            )
        )
        outreach_sent = outreach_sent_result.scalar_one() or 0
        
        outreach_replied_result = await db.execute(
            select(func.count(OutreachHistory.id)).where(
                and_(
                    OutreachHistory.created_at >= start_date,
                    OutreachHistory.created_at <= end_date,
                    OutreachHistory.status == 'replied'
                )
            )
        )
        outreach_replied = outreach_replied_result.scalar_one() or 0
        
        return {
            'time_period': time_period,
            'companies': {
                'total': total_companies,
                'new': companies_new,
            },
            'enrichment': {
                'snapshots_created': enrichments_created,
                'websites_scraped': websites_scraped,
            },
            'outreach': {
                'sent': outreach_sent,
                'replied': outreach_replied,
                'reply_rate': (outreach_replied / outreach_sent * 100) if outreach_sent > 0 else 0,
            }
        }
    
    @staticmethod
    async def get_companies_stats(
        db: AsyncSession,
        time_period: str = "today"
    ) -> Dict[str, Any]:
        """Get company statistics"""
        start_date, end_date = get_time_period_range(time_period)
        
        # Companies by zone
        zones_result = await db.execute(
            select(Zone.name, func.count(Company.id)).join(Company).where(
                and_(
                    Company.created_at >= start_date,
                    Company.created_at <= end_date
                )
            ).group_by(Zone.name)
        )
        companies_by_zone = {row[0]: row[1] for row in zones_result.all()}
        
        # Companies by fleet size
        fleet_size_result = await db.execute(
            select(Company.fleet_size, func.count(Company.id)).where(
                Company.fleet_size != None
            ).group_by(Company.fleet_size)
        )
        companies_by_fleet = {row[0]: row[1] for row in fleet_size_result.all() if row[0]}
        
        # Companies with impound service
        impound_result = await db.execute(
            select(func.count(Company.id)).where(Company.has_impound_service == True)
        )
        companies_with_impound = impound_result.scalar_one() or 0
        
        return {
            'companies_by_zone': companies_by_zone,
            'companies_by_fleet_size': companies_by_fleet,
            'companies_with_impound': companies_with_impound,
        }
    
    @staticmethod
    async def get_zone_stats(
        db: AsyncSession,
        time_period: str = "today"
    ) -> Dict[str, Any]:
        """Get zone statistics"""
        start_date, end_date = get_time_period_range(time_period)
        
        zones_result = await db.execute(
            select(
                Zone.id,
                Zone.name,
                Zone.state,
                func.count(Company.id).label('company_count')
            ).join(Company).where(
                and_(
                    Company.created_at >= start_date,
                    Company.created_at <= end_date
                )
            ).group_by(Zone.id, Zone.name, Zone.state)
        )
        
        zones = []
        for row in zones_result.all():
            zones.append({
                'id': str(row[0]),
                'name': row[1],
                'state': row[2],
                'company_count': row[3]
            })
        
        return {'zones': zones}
    
    @staticmethod
    async def get_outreach_stats(
        db: AsyncSession,
        time_period: str = "today"
    ) -> Dict[str, Any]:
        """Get outreach statistics"""
        start_date, end_date = get_time_period_range(time_period)
        
        # Outreach by channel
        channel_result = await db.execute(
            select(
                OutreachHistory.channel,
                func.count(OutreachHistory.id)
            ).where(
                and_(
                    OutreachHistory.created_at >= start_date,
                    OutreachHistory.created_at <= end_date
                )
            ).group_by(OutreachHistory.channel)
        )
        outreach_by_channel = {row[0]: row[1] for row in channel_result.all()}
        
        # Outreach by status
        status_result = await db.execute(
            select(
                OutreachHistory.status,
                func.count(OutreachHistory.id)
            ).where(
                and_(
                    OutreachHistory.created_at >= start_date,
                    OutreachHistory.created_at <= end_date
                )
            ).group_by(OutreachHistory.status)
        )
        outreach_by_status = {row[0]: row[1] for row in status_result.all()}
        
        # Active assignments
        assignments_result = await db.execute(
            select(func.count(OutreachAssignment.id)).where(
                OutreachAssignment.status == 'active'
            )
        )
        active_assignments = assignments_result.scalar_one() or 0
        
        return {
            'outreach_by_channel': outreach_by_channel,
            'outreach_by_status': outreach_by_status,
            'active_assignments': active_assignments,
        }

