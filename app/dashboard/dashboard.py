"""Main Textual dashboard application"""
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, DataTable, Label, TabbedContent, Tab
from textual import events
from textual.reactive import reactive
from app.database import AsyncSessionLocal
from app.services.dashboard_service import DashboardService
from app.utils.time_periods import TimePeriod
from app.dashboard.widgets.stats_cards import StatsCards
from app.dashboard.widgets.apify_runs_monitor import ApifyRunsMonitor
from app.dashboard.widgets.import_progress import ImportProgressWidget
import asyncio


class DashboardApp(App):
    """Main dashboard application"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .stats-card {
        height: 5;
        border: solid $primary;
        margin: 1;
        padding: 1;
    }
    
    .stat-card {
        height: 6;
        border: solid $primary;
        margin: 1;
        padding: 1;
        width: 1fr;
    }
    
    .time-selector {
        dock: top;
        height: 3;
        background: $panel;
        padding: 1;
    }
    
    .widget-header {
        height: 3;
        background: $primary;
        color: $text;
        padding: 1;
        text-style: bold;
    }
    
    #apify-runs-table {
        height: 20;
    }
    
    #import-stats-table, #import-stage-table {
        height: 15;
        width: 1fr;
    }
    
    #companies-table, #zones-table {
        height: 15;
    }
    
    TabbedContent {
        height: 1fr;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("t", "set_period_today", "Today"),
        ("y", "set_period_yesterday", "Yesterday"),
        ("w", "set_period_this_week", "This Week"),
        ("l", "set_period_last_week", "Last Week"),
        ("m", "set_period_this_month", "This Month"),
        ("n", "set_period_last_month", "Last Month"),
        ("7", "set_period_7_days", "Last 7 Days"),
        ("1", "set_period_14_days", "Last 14 Days"),
        ("3", "set_period_30_days", "Last 30 Days"),
        ("tab", "next_tab", "Next Tab"),
        ("shift+tab", "previous_tab", "Previous Tab"),
    ]
    
    current_period = reactive("today")
    current_tab = reactive("overview")
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header(show_clock=True)
        yield Label(f"Time Period: {self.current_period.upper()} | Press 'r' to refresh | 'q' to quit", classes="time-selector")
        yield StatsCards(id="stats-cards")
        with TabbedContent():
            with Tab("Overview", id="tab-overview"):
                with ScrollableContainer():
                    with Horizontal():
                        with Vertical():
                            yield DataTable(id="companies-table")
                            yield DataTable(id="zones-table")
            with Tab("Apify Runs", id="tab-apify"):
                yield ApifyRunsMonitor()
            with Tab("Import Progress", id="tab-import"):
                yield ImportProgressWidget()
            with Tab("Companies", id="tab-companies"):
                with ScrollableContainer():
                    yield DataTable(id="companies-detailed-table")
            with Tab("Zones", id="tab-zones"):
                with ScrollableContainer():
                    yield DataTable(id="zones-detailed-table")
        yield Footer()
    
    async def on_mount(self) -> None:
        """Called when app starts"""
        # Initialize tab content
        await self.initialize_tabs()
        
        # Initial data load
        await self.refresh_data()
        
        # Auto-refresh every 5 seconds for real-time updates
        self.set_interval(5.0, self.refresh_data)
    
    async def initialize_tabs(self):
        """Initialize tab content widgets"""
        # Initialize tables
        companies_table = self.query_one("#companies-table", DataTable)
        companies_table.add_columns("Metric", "Value")
        
        zones_table = self.query_one("#zones-table", DataTable)
        zones_table.add_columns("Zone", "State", "Companies")
        
        companies_detailed = self.query_one("#companies-detailed-table", DataTable)
        companies_detailed.add_columns("Name", "State", "City", "Stage", "Impound", "Rating")
        
        zones_detailed = self.query_one("#zones-detailed-table", DataTable)
        zones_detailed.add_columns("Zone", "State", "Type", "Companies", "Active")
    
    async def refresh_data(self) -> None:
        """Refresh dashboard data"""
        async with AsyncSessionLocal() as db:
            service = DashboardService()
            
            # Get all stats in parallel
            stats_task = service.get_dashboard_stats(db, self.current_period)
            zone_stats_task = service.get_zone_stats(db, self.current_period)
            apify_stats_task = service.get_apify_runs_stats(db, limit=20)
            import_stats_task = service.get_import_progress_stats(db)
            
            stats, zone_stats, apify_stats, import_stats = await asyncio.gather(
                stats_task, zone_stats_task, apify_stats_task, import_stats_task
            )
            
            # Update stats cards
            stats_cards = self.query_one("#stats-cards", StatsCards)
            stats_cards.update_stats({
                'companies': stats['companies'],
                'zones': zone_stats,
                'apify': apify_stats,
                'import': import_stats,
            })
            
            # Update overview tab
            companies_widget = self.query_one("#companies-table", DataTable)
            companies_widget.clear()
            companies_widget.add_row("Total Companies", f"{stats['companies']['total']:,}")
            companies_widget.add_row("New Companies", f"{stats['companies']['new']:,}")
            companies_widget.add_row("Websites Scraped", f"{stats['enrichment']['websites_scraped']:,}")
            companies_widget.add_row("Outreach Sent", f"{stats['outreach']['sent']:,}")
            companies_widget.add_row("Outreach Replied", f"{stats['outreach']['replied']:,}")
            companies_widget.add_row("Reply Rate", f"{stats['outreach']['reply_rate']:.1f}%")
            
            zones_widget = self.query_one("#zones-table", DataTable)
            zones_widget.clear()
            for zone in zone_stats['zones']:
                zones_widget.add_row(
                    zone['name'],
                    zone['state'] or '',
                    f"{zone['company_count']:,}"
                )
            
            # Update Apify Runs tab
            apify_monitor = self.query_one(ApifyRunsMonitor)
            if apify_monitor:
                apify_monitor.update_runs(apify_stats['recent_runs'])
            
            # Update Import Progress tab
            import_widget = self.query_one(ImportProgressWidget)
            if import_widget:
                import_widget.update_progress(import_stats)
            
            # Update detailed tables (simplified for now)
            # TODO: Add pagination and filtering for large datasets
    
    def action_set_period_today(self) -> None:
        """Set period to today"""
        self.current_period = TimePeriod.TODAY
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_yesterday(self) -> None:
        """Set period to yesterday"""
        self.current_period = TimePeriod.YESTERDAY
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_this_week(self) -> None:
        """Set period to this week"""
        self.current_period = TimePeriod.THIS_WEEK
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_last_week(self) -> None:
        """Set period to last week"""
        self.current_period = TimePeriod.LAST_WEEK
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_this_month(self) -> None:
        """Set period to this month"""
        self.current_period = TimePeriod.THIS_MONTH
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_last_month(self) -> None:
        """Set period to last month"""
        self.current_period = TimePeriod.LAST_MONTH
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_7_days(self) -> None:
        """Set period to last 7 days"""
        self.current_period = TimePeriod.LAST_7_DAYS
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_14_days(self) -> None:
        """Set period to last 14 days"""
        self.current_period = TimePeriod.LAST_14_DAYS
        asyncio.create_task(self.refresh_data())
    
    def action_set_period_30_days(self) -> None:
        """Set period to last 30 days"""
        self.current_period = TimePeriod.LAST_30_DAYS
        asyncio.create_task(self.refresh_data())
    
    def action_refresh(self) -> None:
        """Refresh data"""
        asyncio.create_task(self.refresh_data())
    
    def on_tabbed_content_changed(self, event: TabbedContent.TabActivated) -> None:
        """Handle tab change"""
        self.current_tab = event.tab.id


def run_dashboard():
    """Run the dashboard"""
    app = DashboardApp()
    app.run()

