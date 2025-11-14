"""Dashboard service for statistics"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.models.company import Company
from app.models.zone import Zone
from app.models.enrichment import EnrichmentSnapshot
from app.models.outreach import OutreachHistory, OutreachAssignment
from app.models.apify_run import ApifyRun
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
    
    @staticmethod
    async def get_apify_runs_stats(
        db: AsyncSession,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get Apify runs statistics"""
        # Recent runs
        recent_runs_result = await db.execute(
            select(ApifyRun)
            .order_by(ApifyRun.created_at.desc())
            .limit(limit)
        )
        recent_runs = recent_runs_result.scalars().all()
        
        # Count by status
        status_counts_result = await db.execute(
            select(
                ApifyRun.status,
                func.count(ApifyRun.id)
            ).group_by(ApifyRun.status)
        )
        status_counts = {row[0] or 'UNKNOWN': row[1] for row in status_counts_result.all()}
        
        # Count by processing status
        processing_counts_result = await db.execute(
            select(
                ApifyRun.processing_status,
                func.count(ApifyRun.id)
            ).group_by(ApifyRun.processing_status)
        )
        processing_counts = {row[0] or 'UNKNOWN': row[1] for row in processing_counts_result.all()}
        
        # Active runs (RUNNING status)
        active_runs_result = await db.execute(
            select(func.count(ApifyRun.id)).where(
                ApifyRun.status == 'RUNNING'
            )
        )
        active_runs = active_runs_result.scalar_one() or 0
        
        # Pending processing
        pending_result = await db.execute(
            select(func.count(ApifyRun.id)).where(
                and_(
                    ApifyRun.status == 'SUCCEEDED',
                    ApifyRun.processing_status == 'pending'
                )
            )
        )
        pending_processing = pending_result.scalar_one() or 0
        
        # Failed runs
        failed_result = await db.execute(
            select(func.count(ApifyRun.id)).where(
                or_(
                    ApifyRun.status == 'FAILED',
                    ApifyRun.processing_status == 'failed'
                )
            )
        )
        failed_runs = failed_result.scalar_one() or 0
        
        # Total items processed
        items_result = await db.execute(
            select(func.sum(ApifyRun.items_count)).where(
                ApifyRun.items_count.isnot(None)
            )
        )
        total_items = items_result.scalar_one() or 0
        
        # Format recent runs
        runs_data = []
        for run in recent_runs:
            runs_data.append({
                'run_id': run.run_id[:20] + '...' if len(run.run_id) > 20 else run.run_id,
                'location': run.location or 'N/A',
                'query': run.query or 'N/A',
                'status': run.status or 'UNKNOWN',
                'processing_status': run.processing_status or 'pending',
                'items_count': run.items_count or 0,
                'started_at': run.started_at.isoformat() if run.started_at else None,
                'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                'error_message': run.error_message[:50] + '...' if run.error_message and len(run.error_message) > 50 else run.error_message,
            })
        
        return {
            'recent_runs': runs_data,
            'status_counts': status_counts,
            'processing_counts': processing_counts,
            'active_runs': active_runs,
            'pending_processing': pending_processing,
            'failed_runs': failed_runs,
            'total_items': total_items,
        }
    
    @staticmethod
    async def get_import_progress_stats(
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get company import progress statistics"""
        # Total companies
        total_result = await db.execute(select(func.count(Company.id)))
        total_companies = total_result.scalar_one() or 0
        
        # Companies by scraping stage
        stage_result = await db.execute(
            select(
                Company.scraping_stage,
                func.count(Company.id)
            ).group_by(Company.scraping_stage)
        )
        by_stage = {row[0] or 'None': row[1] for row in stage_result.all()}
        
        # Companies by state
        state_result = await db.execute(
            select(
                Company.address_state,
                func.count(Company.id)
            ).where(Company.address_state.isnot(None))
            .group_by(Company.address_state)
        )
        by_state = {row[0]: row[1] for row in state_result.all()}
        
        # Companies with impound service
        impound_result = await db.execute(
            select(func.count(Company.id)).where(
                Company.has_impound_service == True
            )
        )
        with_impound = impound_result.scalar_one() or 0
        
        # Companies with websites scraped
        scraped_result = await db.execute(
            select(func.count(Company.id)).where(
                Company.website_scrape_status == 'success'
            )
        )
        websites_scraped = scraped_result.scalar_one() or 0
        
        # Recent imports (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_result = await db.execute(
            select(func.count(Company.id)).where(
                Company.created_at >= last_24h
            )
        )
        recent_imports = recent_result.scalar_one() or 0
        
        return {
            'total_companies': total_companies,
            'by_stage': by_stage,
            'by_state': by_state,
            'with_impound': with_impound,
            'websites_scraped': websites_scraped,
            'recent_imports_24h': recent_imports,
        }

